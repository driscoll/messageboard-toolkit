#!/bin/python

from datetime import datetime
from dateutil.parser import *

import re

def isDate(s):
    """Check if a string is a formatted datetime
    """
    if (type(s) == str):
        if (len(s) == 15):
            return (s[8] == 'T')
    return False

def getDateTime(utc = 0):
    """Return machine- and human-readable date-time as string, e.g. 20070304T203217
    """
    if utc:
        return datetime.utcnow().strftime('%Y%m%dT%H%M%S')
    else:
        return datetime.now().strftime('%Y%m%dT%H%M%S')

def convertDateTime(messydate):
    """Return arbitrary str to formatted datetime, '%Y%m%dT%H%M%S'
   
    e.g. 
    messydate = 'June-4th-2010, 10:48 AM'
    returns '20100604T104800' 

    TODO This will be an on-going problem because vB 
    can displays dates in a variety of ways"""
    return parse(messydate, fuzzy = True).strftime('%Y%m%dT%H%M%S')
    
def findThreadID(s):
    """Find thread ID in a URL or filename"""
    m = re.search(r't=([0-9]*)', s)
    if m == None:
        return None 
    else:   
        return m.group(1).strip()

def findThreadURL(s, id):
    """Find thread URL for given ID in a string"""
    # This pattern should match the first page in the thread
    # TODO this pattern isn't working
    pattern = r'http://[^\'"]*showthread[^\'"]*t=%s[^\'"]*' % id
    m = re.search(pattern, s)
    if m == None:
        return None 
    else:
        return m.group(0).strip()

def findThreadURLs(s):
    """Return all valid thread URLs in a string"""
    # This pattern should match the first page in threads
    pattern = r'http://[^\'"]*showthread[^\'"]*t=[0-9]*[^\'"]*'
    return re.findall(pattern, s)

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
    if isValidURL(raw_URL):
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

class Devnull:
    """Destination for msgs in non-verbose
    """
    def write(self, msg):
        pass

def dumpf(obj, filename = ''):
    """Dump a Post or Thread object to a JSON file""" 
    # TODO Should check if obj is Post or Thread
    if not filename:
        filename = obj.title + '.json'
    print "Printing JSON data to %s ..." % filename
    # TODO catch errors
    j = obj.exportJSON(4)
    print j
    with open(filename, 'w') as f:
        f.write(j)



