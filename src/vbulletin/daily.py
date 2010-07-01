#!/usr/bin/python
#
# Example of a daily Archiver thread

import vbarchive

url = []

# Mega 43+ page thread
# url.append('http://www.extremeskins.com/showthread.php?t=324532')
    
# Smaller 2+ page thread
# url.append('http://forums.wrongdiagnosis.com/showthread.php?t=49675')

# Single page thread (as of June 22)
url.append('http://www.naturallycurly.com/curltalk/showthread.php?t=104226')

localdir = '/data/code/messageboard-toolkit/archive/'

archive = vbarchive.Archive(localdir, platform = 'windows')

for u in url:
    archive.addThread(u)
 
archive.update()



