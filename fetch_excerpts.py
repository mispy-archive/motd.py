#!/usr/bin/env python

import subprocess
import re
import os
import time
from BeautifulSoup import BeautifulSoup

def sh(cmd):
    return subprocess.check_output(cmd, shell=True).strip()

texts = []
for i in range(50):
    try:
        sh("wget http://en.wikipedia.org/wiki/Special:Random -O /tmp/wikirandom.html -o /dev/null")
        soup = BeautifulSoup(open("/tmp/wikirandom.html").read(), convertEntities=BeautifulSoup.HTML_ENTITIES)
        title = soup.find('title').text.split(' -')[0]
        para = sorted(soup.findAll('p'), key=lambda el: abs(len(el.text.split())-50))[0]
        text = title + "\n" + ''.join(para.findAll(text=True))
        if text[-1] == ":" or len(text.split()) < 25 or len(text.split()) > 75:
            continue
        text = re.sub(r'\[.*\]', '', text)
        texts.append(text)
    except Exception, e:
        print e
        time.sleep(1)
        continue

f = open(os.path.join(os.path.dirname(__file__), 'excerpts'), 'w')
f.write('\n%\n'.join(texts).encode('utf-8'))
f.close()
