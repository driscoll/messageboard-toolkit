#!/usr/bin/python

import json
import vbutils
import vbscrape

class Post:

    def importHTML(self, rawhtml):
        """Populate object by scraping chunk of HTML
        """

        # TODO clean up the HTML
        # Converting to UTF-8 bc JSON uses UTF-8
        html = vbutils.cleanEncoding(rawhtml)
        
        # Force integer type conversion 
        self.id = int(vbscrape.scrapePostID(html))
        self.postcount = int(vbscrape.scrapePostCount(html, self.id))
        self.authorid = int(vbscrape.scrapePostAuthorID(html))

        self.permalink = vbscrape.scrapePostPermalink(html)
        self.dateposted = vbscrape.scrapePostDate(html)
        self.title = vbscrape.scrapePostTitle(html)
        self.message = vbscrape.scrapePostMessage(html)
        self.sig = vbscrape.scrapePostSig(html)
        self.editnote = vbscrape.scrapePostEditNote(html)
 
    def importJSON(self, jsondata):
        """Populate object from JSON string
        """
 
        # ''.join is used to accomodate list input
        clean = vbutils.cleanEncoding(''.join(jsondata), isHTML = False)

        # Try to load JSON data from the input str
        try:
            j = json.loads(clean)
        except TypeError:
            print "Error: Could not find JSON data."
            return None
        
        self.permalink = j["permalink"]
        self.id = j["id"]
        self.postcount = j["postcount"]
        self.dateposted = j["dateposted"]
        self.title = j["title"]
        self.authorid = j["authorid"]
        self.message  = j["message"]
        self.sig = j["sig"]
        self.editnote = j["editnote"]

    def exportDict(self):
        """Return dict obj with all post data"""
        j = {}
        j["permalink"] = self.permalink
        j["id"] = self.id
        j["postcount"] = self.postcount
        j["dateposted"] = self.dateposted
        j["title"] = self.title
        j["authorid"] = self.authorid
        j["message"] = self.message 
        j["sig"] = self.sig
        j["editnote"] = self.editnote
        return j

    def exportJSON(self, indent_ = 4):
        """Generate JSON string from this object
        """
        return json.dumps(self.exportDict(), indent=indent_)

    def __init__(self,
                id = '',
                permalink = '',
                postcount = '',
                dateposted = '',
                title = '',
                authorid = '',
                message = '',
                sig = '',
                editnote = '',
                rawhtml = '',
                jsonstr = ''
                ):
        """Single post in a thread
        """
        
        if jsonstr:
        
            self.importJSON(jsonstr)

        elif rawhtml:

            self.importHTML(rawhtml)

        else:
 
            self.permalink = permalink
            self.id = id
            self.postcount = postcount
            self.dateposted = dateposted
            self.title = title
            self.authorid = authorid
            self.message = message 
            self.sig = sig
            self.editnote = editnote

