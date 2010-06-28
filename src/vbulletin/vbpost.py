#!/usr/bin/python

import json
import vbutils
import vbscrape

class Post:

    def importHTML(self, html):
        """Populate object by scraping chunk of HTML
        """
        self.permalink = vbscrape.scrapePostPermalink(html)
        self.id = vbscrape.scrapePostID(html) 
        self.postcount = vbscrape.scrapePostCount(html, self.id) 
        self.dateposted = vbscrape.scrapePostDate(html) 
        self.title = vbscrape.scrapePostTitle(html) 
        self.authorid = vbscrape.scrapePostAuthorID(html) 
        self.message = vbscrape.scrapePostMessage(html) 
        self.sig = vbscrape.scrapePostSig(html) 
        self.editnote = vbscrape.scrapePostEditNote(html)
 
    def importJSON(self, jsondata):
        """Populate object from JSON string
        """
        j = json.loads(jsondata)
        self.permalink = j["permalink"]
        self.id = j["id"]
        self.postcount = j["postcount"]
        self.dateposted = j["dateposted"]
        self.title = j["title"]
        self.authorid = j["authorid"]
        self.message  = j["message"]
        self.sig = j["sig"]
        self.editnote = j["editnote"]

    def exportJSON(self, indent_ = 0):
        """Generate JSON string from this object
        """
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
        return json.dumps(j, indent=indent_)

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

