#!/usr/bin/python
#
# Thread class and related methods 
# for working with vBulletin messageboards
#
# (c) Kevin Driscoll, kedrisco@usc.edu
#
# Last changed: 20 June 2010
#

import json
import re
import sys
import urllib2
import vbutils

def getFirstPage(url=''):
    """Download html from first page of a thread"""
    if url:
        # TODO catch errors
        response = urllib2.urlopen(url)
        return response.read()
    return '' 

def scrapeForumName(html):
    """Scrape forum name out of HTML"""
    # TODO Relying on vB convention, need to template
    if html:
        titletag = html[(html.find('<title>')+7):html.find('</title>')].strip()
        return titletag.split('-').pop().strip()
    else:
        return ''

def scrapeTitle(html):
    """Scrape thread title out of HTML"""
    # TODO Relying on vB convention, need to template
    title = ''
    if html:
        titletag = html[(html.find('<title>')+7):html.find('</title>')].strip()
        for t in titletag.split('-')[0:-1]:
            title += t.strip() + '_'
    if title:
        return title[:-1]
    return ''

def scrapeNumPages(html):
    """Scrape number of pages from thread"""
    # TODO based on vB convention, need template
    if html:
        m = re.search(r'Page [0-9]* of ([0-9]*)', html)
        if m:
            return int(m.group(1).strip())
    return 1

class Thread:
    """A thread is a collection of posts
        Thread objects can be built with either
            * unique thread ID # or
            * url to some page in the thread
    """

    def update(self, url = ''):
        """Retrieve HTML from first page and scrape basic info 
        """
   
        if not url:
            url = self.url 
 
        self.url = vbutils.cleanURL(url)
        self.id = vbutils.findThreadID(self.url)
        html = getFirstPage(self.url)
        self.lastupdate = vbutils.getDateTime()   
        self.forum = vbutils.makeSlug(scrapeForumName(html))
        self.title = vbutils.makeSlug(scrapeTitle(html))
        self.numpages = scrapeNumPages(html)

    def importJSON(self, jsondata):
        """Populate object from a string of JSON data"""
        # Create dictionary from jsondata
        j = json.loads(jsondata)
        # TODO test this
        self.posts = j["posts"]
        self.lastupdate = j["lastupdate "]
        self.forum = j["forum"]
        self.id = j["id"]
        self.numpages = j["numpages "]
        self.title = j["title "]
        self.url = j["url"]

    def exportJSON(self, indent_ = 0):
        """Generate JSON string from this object
        """
        j = {}
        j["id"] = self.id
        j["title"] = self.title
        j["forum"] = self.forum
        j["url"] = self.url
        j["lastupdate"] = self.lastupdate
        j["numpages"] = self.numpages
        # TODO implement exportJSON in the Post class 
        j["posts"] = {}
        return json.dumps(j, indent=indent_)

    def __init__(self, 
                url = '',
                id = '',
                lastupdate = '',
                title = '',
                forum = '',
                numpages = 1,
                posts = {}
                ):

        self.posts = posts
        self.lastupdate = lastupdate 
        self.forum = forum
        self.id = id
        self.numpages = numpages 
        self.title = title 
        self.url = url

        if url:
            self.update(url)
 
