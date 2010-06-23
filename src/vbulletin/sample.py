#!/usr/bin/python

import vbarchive
import vbthread

url = []

# Mega 43+ page thread
# url.append('http://www.extremeskins.com/showthread.php?t=324532')
    
# Smaller 2+ page thread
# url.append('http://forums.wrongdiagnosis.com/showthread.php?t=49675')

# Single page thread (as of June 22)
url.append('http://www.naturallycurly.com/curltalk/showthread.php?t=104226')

thread = []

for u in url:
    thread.append(vbthread.Thread(u))
 
for t in thread:
    vbarchive.downloadThread(t, '.', '', 'windows')


