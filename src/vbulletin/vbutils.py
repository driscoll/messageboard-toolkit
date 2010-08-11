#!/bin/python

from BeautifulSoup import UnicodeDammit
from datetime import datetime
from dateutil.parser import *

import os
import re


def isDate(s):
    """Check if a string is a formatted datetime
    """
    if (type(s) == str):
        if (len(s) == 15):
            return (s[8] == 'T')
    return False

def parseDateTime(t, format = '%Y%m%dT%H%M%S'):
    """Return datetime object from strf datetime"""
    return datetime.strptime(t, format)

def getDateTime(utc = 0, format = '%Y%m%dT%H%M%S'):
    """Return machine- and human-readable date-time as string, e.g. 20070304T203217
    """
    if utc:
        return datetime.utcnow().strftime(format)
    else:
        return datetime.now().strftime(format)

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
        return '' 
    else:   
        return m.group(1).strip()

def findThreadURL(s, id):
    """Find thread URL for given ID in a string"""
    # This pattern should match the first page in the thread
    # TODO this pattern isn't working
    pattern = r'http://[^\'"]*showthread[^\'"]*t=%s[^\'"]*' % id
    m = re.search(pattern, s)
    if m == None:
        return '' 
    else:
        return m.group(0).strip()

def findThreadURLs(s):
    """Return all valid thread URLs in a string"""
    # This pattern should match the first page in threads
    pattern = r'http://[^\'"]*showthread[^\'"]*t=[0-9]*[^\'"]*'
    return re.findall(pattern, s)


def isValidURL(url):
    """Check if URL is valid vB thread
    
    TODO Janky verification but it's a start
    """
    indicators = []
    indicators.append('showthread')
    indicators.append('http://')
    indicators.append('yuku')
    i = 0
    found = False
    while (i < len(indicators)) and not found: 
        if (url.find(indicators[i]) < 0):
            found = True
    return found 

def isValidJSONStr(obj):
    """Check if obj is a str, list, or dict of valid JSON 
    
    TODO Janky validation needs improving
    
    Right now it basically safeguards against filenames 
    being passed to importJSON() methods of Post and 
    Thread objs 
    """
    if type(obj) == type(str()): 
        if (obj.find('{') < 0) or (obj.find('}', 1) < 0):
            return False 
        return True 

def isValidFilename(filename):
    """Check if filename exists on local disk

    TODO We could check inside the file 
         for valid JSON.
    """
    return os.access(filename, os.F_OK)

             
def cleanEncoding(s, isHTML = True):
    """Return HTML with UTF-8 character encoding

    HTML encoding on vB seems to be a mess.
    BeautifulSoup.UnicodeDammit should help avoid encoding errors.
    """
    clean = UnicodeDammit(s, isHTML = isHTML)
    # print "UnicodeDammit found encoding: %s" % clean.originalEncoding
    return clean.unicode

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


def convertKeysToStr(d):
    """Return dict with keys coerced to str"""
    strkeys = {}
    for k, v in d.iteritems():
        strkeys[str(k)] = v
    return strkeys


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
        filename = makeSlug(obj.title) + '.json'
    # TODO catch errors
    j = obj.exportJSON(4)
    with open(filename, 'w') as f:
        f.write(j)
    print "JSON data written to %s" % filename

