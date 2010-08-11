#!/usr/bin/python
#
# Scraping the Survivor Sucks thread
#
# Original URL:
#   http://p085.ezboard.com/fsurvivorsucksfrm12.showMessageRange?topicID=204.topic&start=1&stop=20
#
# New URL:
#   http://survivorsucks.yuku.com/topic/10051
#

import vbarchive

url = []

url.append('http://survivorsucks.yuku.com/topic/10051')

localdir = '/data/code/messageboard-toolkit/archive/'

archive = vbarchive.Archive(localdir, platform = 'windows')

for u in url:
    archive.addThread(u)
 
archive.update()



