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

            self.lastupdate = lastupdate 
            self.forum = forum
            self.id = id
            self.numpages = numpages 
            self.title = title 
            self.url = url
            if post:
                self.post = {}
                for id, p in post.iteritems():
                    kw = vbutils.convertKeysToStr(p)
                    self.post[id] = vbpost.Post(**kw) 
            else:
                self.post = post 
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
        print "Scraping %s ..." % self.url
        page.append(getPage(self.url))
        self.numpages = int(vbscrape.scrapeNumPages(page[0]))
        print "Found %s pages." % str(self.numpages)
        for p in range(1, self.numpages):
            print "Scraping page %s of %s ..." % (str(p+1), str(self.numpages))
            page.append(getPage(self.url, (p + 1)))

        print "Importing data from HTML ..."
        self.importHTML(page, self.url)

        self.lastupdate = vbutils.getDateTime()   
        print "Thread update completed at %s" % self.lastupdate

    def importHTML(self, rawhtml, url = ''):
        """Populate object by scraping chunk of HTML
       
        rawhtml : May be a string or a list of strings.
        url : Optional param, useful to specify URL explicitly
                in situations where the URL is known.
                Many vB installations use only relative links
                so it can be hard to discover a URL from code.
        """

        html = []
        # Clean up the raw html
        if type(rawhtml) == type(list()):
            for h in rawhtml:
                html.append(vbutils.cleanEncoding(h))
        else:
            html.append(vbutils.cleanEncoding(rawhtml))
        
        self.id = vbscrape.scrapeThreadID(html[0]) 
        if url:
            self.url = url
        else:
            self.url = vbscrape.scrapeThreadURL(self.id, html[0]) 
        self.forum = vbutils.makeSlug(vbscrape.scrapeForumName(html[0]))
        self.title = vbutils.makeSlug(vbscrape.scrapeThreadTitle(html[0]))
        self.numpages = vbscrape.scrapeNumPages(html[0])

        self.post = {} 
        for h in html:
            self.post.update(vbscrape.scrapePosts(h))
   
    def importJSON(self, jsondata):
        """Populate object from a string of JSON data"""
       
        # ''.join is used to accomodate list input
        clean = vbutils.cleanEncoding(''.join(jsondata), isHTML = False)

        # Try to load JSON data from the input str
        try:
            j = json.loads(clean)
        except:
            print "Error: Could not find JSON data."
            return None
        
        # Loop over posts creating Post objs
        self.post = {}
        
        print "Found %s posts." % len(j["post"])
        for id, p in j["post"].iteritems():
            print "Importing Post #%s ..." % str(id)
            if type(p) is dict:
                # Keyword args must be str
                # but our JSON dict has unicode keys
                # so we must convert before passing
                # into the Post.__init__() method
                kw = vbutils.convertKeysToStr(p)
                self.post[id] = vbpost.Post(**kw)
            elif (type(p) in [str, unicode]):
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
        return json.dumps(self.exportDict(), indent=indent_)
    
    def exportDict(self):
        """Return dict obj with all thread data"""
        j = {}
        j["id"] = self.id
        j["title"] = self.title
        j["forum"] = self.forum
        j["url"] = self.url
        j["lastupdate"] = self.lastupdate
        j["numpages"] = self.numpages
        j["post"] = {}
        for id, p in self.post.iteritems():
            j["post"][id] = p.exportDict()
        return j

    def numPosts(self):
        """Return number of posts in the thread"""
        return len(self.post)

    def meanTimeBetweenPosts(self):
        """Return mean seconds between posts in the thread""" 
        postdate = []
        for p in self.post.itervalues():
            postdate.append(vbutils.parseDateTime(p.dateposted))
        postdate.sort()
        delta = 0
        i = 1
        while (i < len(postdate)):
            delta += abs(postdate[i-1] - postdate[i]).seconds
            i += 1
        return (float(delta)/len(postdate))

    def graph(self, style = "bar", format = "ascii"):
        """Construct graphical representations of Thread data"""
        # Determine scale 
        
        # For each period, count number of posts 
        # Create graphical representation
        return g 

