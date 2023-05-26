# RansomWatch

RansomWatch is a ransomware leak site monitoring tool. It will scrape all of the entries on various ransomware leak sites, store the data in a SQLite database, and send notifications via Slack or Discord when a new victim shows up, or when a victim is removed.

## Configuration

In `config_vol/`, please copy `config.sample.yaml` to `config.yaml`, and add the following:

* Leak site URLs. I decided not to make this list public in order to prevent them from gaining even more noteriety, so if you have them, add them in. If not, this tool isn't for you.
  * To get the Hive API onion, load their main site and press F12 to use the developer tools. Look for XHR requests, you should see a few to a `hiveapi...` onion domain.
* Notification destinations. RansomWatch currently supports notifying via.the following:
  * Slack: Follow [these](https://api.slack.com/messaging/webhooks) instructions to add a new app to your Slack workspace and add the webhook URL to the config.
  * Discord: Follow [these](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) instructions to add a new app to your Discord server and add the webhook URL to the config.
  * Teams: Follow [these](https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook) instructions to add a new app to your Teams channel and add the webhook URL to the config.
  * Telegram: simply create a new bot with BotFather, add it to the group in which you want to receive notifications and compile the config file
* 2captcha api key: to bypass captchas

Additionally, there are a few environment variables you may need to set:

* `RW_DB_PATH`: Path for the SQLite database to use
* `RW_CONFIG_PATH`: Path to the `config.yaml` file

These are both set in the provided `docker-compose.yml`.

## Usage

This is intended to be run in Docker via a cronjob on whatever increment you decide to use.

First, build the container: `docker-compose build app`

Then, add it to your crontab. Example crontab entry (running every 8 hours):

```
*/30 * * * * cd /home/ioc/ransomwatch && ./run.sh
```

This can also be run via the command line, but that requires you to have your own Tor proxy (with the control service) running. Example execution:

```
$ RW_DB_PATH=./db_vol/ransomwatch.db RW_CONFIG_PATH=./config_vol/config.yaml python3 src/ransomwatch.py
```

## Example Slack Messages

![Slack notification for new victim](/img/slack_example_new_victim.png)

![Slack notification for removed victim](/img/slack_example_removed_victim.png)

![Slack notification for site down](/img/slack_example_site_down.png)

![Slack notification for an error](/img/slack_example_error.png)

The messages sent to Discord and Teams are very similar in style, identical in content.

## Leak Site Implementations

The following leak sites are supported (unchecked are currently not monitored by Leonardo):

- [x] Everest
- [X] Cuba
- [X] RansomEXX
- [X] Lockbit
- [] Hive
- [X] Blackbyte
- [X] Blackbasta
- [X] Lorenz
- [X] Cl0p
- [X] ViceSociety
- [X] Royal
- [X] Ragnar Locker
- [X] Babuk
- [X] Blacktor
- [X] Dark Leak Market
- [X] Quantum
- [X] DataLeak
- [X] 0mega
- [X] Mallox
- [X] Qilin
- [X] Unsafe
- [X] Play
- [X] Bianlian
- [X] Daixin
- [X] Relic
- [X] RansomHouse
- [X] Nokoyawa
- [X] Snatch
- [X] Karakurt
- [X] Free Civilian
- [X] Monti
- [X] MoneyMessage
- [X] 8base
- [X] Donut
- [X] Akira
- [X] Abyss
- [X] Cryptnet
- [X] Malas
- [X] Rancoz
- [X] Ra Group
- [X] Medusa
- [X] BlackSuit
- [X] Vendetta

## Leak Sites lists

- https://ransomwatch.telemetry.ltd/#/INDEX
- https://github.com/fastfire/deepdarkCTI/blob/main/ransomware_gang.md

# Slack to CTIS

Transfer slack notifications to Leonardo's CTIS platform.

## How to

Add to your crontab the following line: `*/5 * * * * /PATH/TO/run_bridge.sh >> /EVENTUAL/LOG/FILE 2>&1`

## Configuration

In ransomwatch's config file there is a section dedicated to slack to ctis integration; here's an example of it filled with information.

```
slack_to_ctis:
  slack_error_url: channel url for errors
  slack:
    token: xoxb-TOKEN
    channel_id: C03XXXXXXGN # channel un which the bridge will work
  ctis:
    url: https://cis.smth.com
    username: username
    password: password
  time_path: /PATH/TO/TIME/FILE # file in which the bridge will save the timestamp of the last message bridged
```
