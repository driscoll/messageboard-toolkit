#!/usr/bin/python

import vbthread
import vbuser
import vbutils

class Forum:
    """vBulletin Forum
    """

    def __init__(self, url = '', name = '', lastupdate = '', thread = {}, user = {}):
        # TODO implement importJSON method a la Thread, Post
        # TODO should probably be subclassed in a future rev
        self.url = url 
        self.name = name
        self.lastupdate = lastupdate
 
        self.thread = {} 
        for id, t in thread.iteritems():
            kw = vbutils.convertKeysToStr(t)
            self.thread[id] = vbthread.Thread(**kw)
        
        self.user = {}
        """TODO User class not yet implemented
        for id, u in user:
            self.user[id] = vbuser.User(**t)
        """

    def exportDict(self):
        """Return dict of Forum data"""
        d = {}
        d["url"] = self.url
        d["name"] = self.name
        d["thread"] = {}
        for id, t in self.thread.iteritems():
            d["thread"][id] = self.thread[id].exportDict()
        """TODO User class not yet implemented
        d["user"] = {}
        for id, u in self.user.iteritems():
            d["user"][id] = self.user[id].exportDict()
        """
        d["user"] = self.user
        return d

