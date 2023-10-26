from db.models import Victim
from .source import NotificationSource
import requests

class CTISNotification():

    headers = {}
    url = ""

    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.CTIS_login(username, password)
        if not self.setup_relationships():
            raise Exception("Can't setup relationships for CTIS integration")

    def do_req(self, url, json):
        response = requests.post(self.url + url, headers = self.headers, json = json)

        ok = True
        if response.status_code == 500: # TODO
            response = requests.post(self.url + url, headers = self.headers, json = json)
        if response.status_code == 201:
            if "relationships" in url:
                res = response.json()
            else:
                res = response.json()["_id"]
        elif response.status_code == 409:
            if "relationshipTypes" in url or "relationships" in url:
                res = response.json()
            else:
                res = response.json()["_error"]["message"]["_id"]
        else:
            res = response.json()
            ok = False

        return ok, res
    
    def check_aliases(self, entity_url, name):
        res = requests.get(self.url + entity_url, headers = self.headers, json = []).json()["_items"]
        for e in res:
            if "aliases" in e and name in e["aliases"]:
                return e["_id"]
        return None

    def add_relationship_al_vic(self, rel_type, src, src_type, dst, dst_type):
        json_query = [
            {
                "confidence": 100,
                "sub-type": "is_victim",
                "relationship_type": rel_type,
                "source_ref": src,
                "source_type": src_type,
                "target_ref": dst,
                "target_type": dst_type,
                "type": "relationship"
            }
        ]

        return self.do_req("/relationships", json_query)

    def add_relationship(self, rel_type, src, src_type, dst, dst_type):
        json_query = [
            {
                "confidence": 100,
                "relationship_type": rel_type,
                "source_ref": src,
                "source_type": src_type,
                "target_ref": dst,
                "target_type": dst_type,
                "type": "relationship"
            }
        ]

        return self.do_req("/relationships", json_query)

    def add_relationship_type(self, relationship_type, source_ref_type, target_ref_type):
        json_query = [
            {
                "source_ref_type": source_ref_type,
                "relationship_type": [relationship_type],
                "target_ref_type": [target_ref_type]
            }
        ]

        return self.do_req("/relationshipTypes", json_query)

    def add_victim(self, name):
        res = self.check_aliases("/identities", name)
        if res != None:
            return True, res
        json_query = [
            {
                "confidence": 100,
                "name": name,
                "identity_class": "organization",
                "is_victim": "True",
                "x-sources": [
                    {
                        "source_name": "ransomwatch",
                        "classification": 0,
                        "releasability": 0,
                        "tlp": 0
                    }
                ]
            }
        ]

        return self.do_req("/identities", json_query)

    def add_operation(self, name, description, published, first_seen):
        description += "\nPUBLISHED: " + str(published)
        json_query = [
            {
                "confidence": 100,
                "description": description.replace('\n', '\r\n'),
                "labels": ["Type:ransomware"],
                "name": name,
                "x-sources": [
                    {
                        "source_name": "ransomwatch",
                        "classification": 0,
                        "releasability": 0,
                        "tlp": 0
                    }
                ]
            }
        ]

        if first_seen:
            json_query[0]["first_seen"] = str(first_seen) + "Z"

        return self.do_req("/x-operations", json_query)

    def add_intrusion_set(self, name):
        res = self.check_aliases("/intrusion-sets", name)
        if res != None:
            return True, res
        json_query = [
            {
                "confidence": 100,
                "name": name,
                "x-sources": [
                    {
                        "source_name": "ransomwatch",
                        "classification": 0,
                        "releasability": 0,
                        "tlp": 0
                    }
                ]
            }
        ]

        return self.do_req("/intrusion-sets", json_query)

    def add_alert(self, name, message):
        json_query = [
            {
                "entity_type": "report",
                "labels": ["Type:dls"],
                "title": name,
                "message": message.replace('\n', '\r\n'),
                "from": "ransomwatch",
                "alert_type": "x-operations",
                "role": "analyst",
                "x-sources": [
                    {
                        "source_name": "ransomwatch",
                        "classification": 0,
                        "releasability": 0,
                        "tlp": 0
                    }
                ]
            }
        ]

        return self.do_req("/alerts", json_query)

    def setup_relationships(self):
        if self.add_relationship_type("attributed-to", "x-operations", "intrusion-sets") and self.add_relationship_type("targets", "x-operations", "identities"):
            return True
        return False

    def CTIS_login(self, user, password):
        #response = requests.post(f"{self.url}/api/auth/login", json={"username": user, "password": password})
        response = requests.get(f"{self.url}/login", auth=(user, password))
        self.headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + response.json()["data"]["access_token"]}

    def send_new_victim_notification(self, victim: Victim, actor: "") -> bool:
        if actor == "":
            actor = victim.site.actor
        ok, identity = self.add_victim(victim.name)
        if not ok:
            raise Exception(f"Can't create identity {victim.name}: {identity}")
        ok, intrusion_set = self.add_intrusion_set(actor)
        if not ok:
            raise Exception(f"Can't create intrusion set {actor}: {intrusion_set}")
        ok, operation = self.add_operation(actor + " targets " + victim.name, victim.description, victim.published, victim.first_seen)
        if not ok:
            raise Exception(f"Can't create operation {actor} on {victim.name}: {operation}")
        ok, res = self.add_relationship("targets", operation, "x-operations", identity, "identities")
        if not ok:
            raise Exception("Can't create relationship operation -> identity: {res}")
        ok, res = self.add_relationship("attributed-to", operation, "x-operations", intrusion_set, "intrusion-sets")
        if not ok:
            raise Exception(f"Can't create relationship operation -> intrusion-set: {res}")
        ok, _alert = self.add_alert(actor + " leaks data from " + victim.name, f"Published date: {victim.published}\nLeak URL: {victim.url}")
        if not ok:
            raise Exception(f"Can't create alert: {_alert}")
        ok, res = self.add_relationship("related-to", _alert, "alerts", intrusion_set, "intrusion-sets")
        if not ok:
            raise Exception(f"Can't create relationship alert -> intrusion-set: {res}")
        ok, res = self.add_relationship_al_vic("related-to", _alert, "alerts", identity, "identities")
        if not ok:
            raise Exception(f"Can't create relationship alert -> identity: {res}")
        ok, res = self.add_relationship("related-to", _alert, "alerts", operation, "x-operations")
        if not ok:
            raise Exception(f"Can't create relationship alert -> operation: {res}")
        
        return True
