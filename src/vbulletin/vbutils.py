#!/bin/python

import re

def findThreadID(s):
    """Find thread ID in a URL or filename"""
    m = re.search(r't=([0-9]*)', s)
    if m == None:
        return None 
    else:   
        return m.group(1).strip()

def isValidURL(url):
    # TODO This is janky verification but it's a start
    if (url.find('showthread') == -1):
        return False
    else:
        return True

def cleanURL(raw_URL):
    # Drop the &page= parameter for multipage threads
    # url = re.sub('&page=[0-9]*','',raw_URL)
    # Or... drop all parameters except for &t=
    # TODO are there parameters worth keeping?
    url = ''
    if isValidURL(url):
        url = re.sub(r'[&@?][^t][a-zA-Z]*=[a-zA-Z0-9]*','',raw_URL)
        if not (url.startswith('http://')):
            url = 'http://' + url
    return url

def makeSlug(s, length = 32):
    """Generate slug to use in filenames
        * Concat 32 chars
        * Trim trailing spaces
        * Convert non-alphanumeric to underscores
        * Convert all alpha to lowercase
        e.g. 
          'Israel raids ships carrying aid to Gaza'
        becomes
          'israel_raids_ships_carrying_aid'
    """
    slug = re.sub(r'[^a-zA-Z0-9-]', r'_', s).lower().strip('_')
    return slug[0:(length - 1)].strip('_')


    for t in title:
        slug += t.strip('_') + '_'
        # Trim the slug down to 32 chars
        slug = slug[0:32].strip('_')    
    return slug

class Devnull:
    """Destination for msgs in non-verbose
    """
    def write(self, msg):
        pass



