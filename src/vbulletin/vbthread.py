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
import urllib2
import vbpost
import vbscrape
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
            post = {}, 
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
                self.lastupdate = vbutils.getDateTime()

        else:

            self.post = post
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
        print "Scraping page %s ..." % str(1)
        page.append(getPage(self.url))
        self.numpages = int(vbscrape.scrapeNumPages(page[0]))
        print "Found %s pages." % str(self.numpages)
        for p in range(1, self.numpages):
            print "Scraping page %s of %s ..." % (str(p+1), str(self.numpages))
            page.append(getPage(self.url, (p + 1)))

        print "Importing data from HTML ..."
        self.importHTML(page)

        self.lastupdate = vbutils.getDateTime()   
        print "Thread update completed at %s" % self.lastupdate

    def importHTML(self, rawhtml):
        """Populate object by scraping chunk of HTML
        
        rawhtml : May be a string or a list of strings.
        """

        html = []
        # Clean up the raw html
        if type(rawhtml) == type(list()):
            for h in rawhtml:
                html.append(h.encode('utf-8', 'replace'))
        else:
            html.append(rawhtml.encode('utf-8', 'replace'))
        
        self.id = vbscrape.scrapeThreadID(html[0]) 
        self.url = vbscrape.scrapeThreadURL(self.id, html[0]) 
        self.forum = vbutils.makeSlug(vbscrape.scrapeForumName(html[0]))
        self.title = vbutils.makeSlug(vbscrape.scrapeThreadTitle(html[0]))
        self.numpages = vbscrape.scrapeNumPages(html[0])
       
        self.post = {} 
        for h in html:
            self.post.update(vbscrape.scrapePosts(h))
   
    def importJSON(self, jsondata):
        """Populate object from a string of JSON data"""
        # Create dictionary from jsondata
        j = json.loads(jsondata)
        # TODO Loop over posts 
        self.post = {}
        for id, p in j["post"].iteritems():
            self.post[id] = vbpost.Post(jsonstr = p)
        self.lastupdate = j["lastupdate"]
        self.forum = j["forum"]
        self.id = j["id"]
        self.numpages = j["numpages"]
        self.title = j["title"]
        self.url = j["url"]

    def exportJSON(self, indent_ = 4):
        """Generate JSON string from this object
        """
        j = {}
        j["id"] = self.id
        j["title"] = self.title
        j["forum"] = self.forum
        j["url"] = self.url
        j["lastupdate"] = self.lastupdate
        j["numpages"] = self.numpages
        j["post"] = {}
        for id, p in self.post.iteritems():
            j["post"][id] = p.exportJSON(indent_) 
        return json.dumps(j, indent=indent_)

    
