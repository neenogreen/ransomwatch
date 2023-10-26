FROM library/python:3.9-buster

ENV DEBIAN_FRONTEND noninteractive
ENV GECKODRIVER_VER v0.32.0
ENV FIREFOX_VER 108.0
 
RUN apt update && apt install -y firefox-esr
 
# Add latest FireFox
RUN curl -sSLO https://download-installer.cdn.mozilla.net/pub/firefox/releases/${FIREFOX_VER}/linux-x86_64/en-US/firefox-${FIREFOX_VER}.tar.bz2 \
   && tar -jxf firefox-* \
   && mv firefox /opt/ \
   && chmod 755 /opt/firefox \
   && chmod 755 /opt/firefox/firefox
  
# Add geckodriver
RUN curl -sSLO https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VER}/geckodriver-${GECKODRIVER_VER}-linux64.tar.gz \
   && tar zxf geckodriver-*.tar.gz \
   && mv geckodriver /usr/bin/
 
COPY requirements.txt /

RUN pip install -r /requirements.txt

RUN mkdir /app
COPY src /app/

CMD python3 /app/ransomwatch.py
