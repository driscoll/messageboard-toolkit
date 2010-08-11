#!/usr/bin/python

class User:
    """User in a forum
    """
    def __init__(self, 
                id = '', 
                lastupdate = '',
                firstname = '',
                lastname = '',
                username = '',
                datejoined = '',
                lastlogin = '',
                reply = [],
                thread = [], 
                jsonstr = '',
                rawhtml = ''  
                ):

        if jsonstr:
    
            self.importJSON(jsonstr)

        elif rawhtml:

            self.importHTML(rawhtml)

        self.id = id


    def importJSON(self, jsonstr):
        pass
    
    def importHTML(self, rawhtml):
        pass

