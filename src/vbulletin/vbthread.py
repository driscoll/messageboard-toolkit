#!/usr/bin/python
#
# Thread class and related methods 
# for working with vBulletin messageboards
#
# (c) Kevin Driscoll, kedrisco@usc.edu
#
# Last changed: 20 June 2010
#

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
    return None

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
        self.forum = vbutils.makeSlug(scrapeForumName(html))
        self.title = vbutils.makeSlug(scrapeTitle(html))
        self.numpages = scrapeNumPages(html)

    def __init__(self, url=''):

        self.archive = {} 
        
        self.forum = '' 
        self.id = ''
        self.numpages = 1 
        self.title = ''
        self.url = url
        
        if url:
            print "ok"
            self.update(url)
 
