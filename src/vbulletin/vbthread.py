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
import urllib2
import vbutils

def getPage(url='', page = 1):
    """Returns page of a thread in string of HTML"""
    if url:
        # TODO Template multi-page URL construction
        url = '%s&page=%s' % (url, page)
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

def scrapePosts(html):
    """Return list of Post objects scraped from raw HTML"""
    return [] 

def scrapeID(html):
    """Scrape and return thread ID from chunk of HTML"""
    pattern = r'searchthreadid=([0-9]*)'
    m = re.search(pattern, html)
    if m:
        return m.group(1).strip()
    return ''

def scrapeURL(id, html):
    """Scrape and return thread URL from chunk of HTML"""
    pattern = r'http://[^\'"]*showthread[^\'"]*t=%s[^\'"]*' % id
    m = re.search(pattern, html)
    if m:
        return vbutils.cleanURL(m.group(0).strip())
    return ''

class Thread:
    """A thread is a collection of posts
        Thread objects can be built with either
            * unique thread ID # or
            * url to some page in the thread
    """

    def __init__(self, 
            url = '',
            id = '',
            lastupdate = '',
            title = '',
            forum = '',
            numpages = 1,
            posts = {},
            jsonstr = '',
            rawhtml = ''
            ):
        
        if jsonstr:

            self.importJSON(jsonstr)

        elif rawhtml:

            self.importHTML(rawhtml)
            
            # When creating a thread object with 
            #   raw HTML, one should also pass along 
            #   the lastupdate string 
            if lastupdate:
                self.lastupdate = lastupdate
            else:
                # Else set lastupdate to now
                self.lastupdate = getDateTime()

        else:

            self.posts = posts
            self.lastupdate = lastupdate 
            self.forum = forum
            self.id = id
            self.numpages = numpages 
            self.title = title 
            self.url = url

            if url:

                self.update(url)
 
    def update(self, url = ''):
        """Retrieve HTML from first page and scrape basic info 
        """
   
        if not url:
            url = self.url 
 
        self.url = vbutils.cleanURL(url)
        self.id = vbutils.findThreadID(self.url)

        page = []
        page[0]= getPage(self.url)
        for p in range(1, scrapeNumPages(page[0])):
            page[p] = getPage(self.url, (page + 1))

        self.importHTML(page)

        self.lastupdate = vbutils.getDateTime()   

    def importHTML(self, rawhtml):
        """Populate object by scraping chunk of HTML
        
        rawhtml : May be a string or a list of strings.
        """

        html = ''    
        if type(rawhtml) == type(list()):
            # TODO make function to do this better
            for p in rawhtml:
                html += rawhtml[p]
        else:
            html = rawhtml 

        self.id = scrapeID(html) 
        self.url = scrapeURL(self.id, html) 
        self.forum = vbutils.makeSlug(scrapeForumName(html))
        self.title = vbutils.makeSlug(scrapeTitle(html))
        self.numpages = scrapeNumPages(html)
        # TODO implement post scraper
        self.post = scrapePosts(html)
   
    def importJSON(self, jsondata):
        """Populate object from a string of JSON data"""
        # Create dictionary from jsondata
        j = json.loads(jsondata)
        # TODO Loop over posts 
        self.posts = j["posts"]
        self.lastupdate = j["lastupdate"]
        self.forum = j["forum"]
        self.id = j["id"]
        self.numpages = j["numpages"]
        self.title = j["title"]
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

    
