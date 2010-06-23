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

class Devnull:
    """Destination for msgs in non-verbose
    """
    def write(self, msg):
        pass

class Thread:

     
    
    def __init__(self, url):
        
        # TODO this is janky debug code for handling output.
        # Probably need some kind of output handler object?
        # VERBOSE = Devnull()
        VERBOSE = sys.stdout

        self.url = url

        # Extract unique thread ID from the URL
        print >>VERBOSE, "Seeking thread ID ..."
        m = re.search(r't=([0-9]*)', self.url)
        if m == None:
            print 'Error: Could not locate thread ID in URL.'
            print
            sys.exit(2)
        else:
            self.id = m.group(1).strip()
        print >>VERBOSE, "Thread ID: %s" % self.id

        # Get the HTML of the first page in the thread
        # Generate urllib2 request object from the URL
        req = urllib2.Request(url)
        # Get the HTML of the first page in the thread
        # TODO catch errors
        response = urllib2.urlopen(url)
        
        self.html = response.read()

        response.close()

        # Locate contents of title
        # Split the resulting string by -
        #   TODO this should be templated 
        title = re.sub(r'[^a-zA-Z0-9-]',r'_',
            self.html[(self.html.find('<title>')+7):
            self.html.find('</title>')]).lower().split('-')
        
        # Pop forum name and create slug to use in filenames
        # TODO Relying on vB convention, need to template
        # TODO can people edit thread titles? if so, better to use ID# than slug?
        print >>VERBOSE, "Discovering forum name ..."
        self.forum = title.pop().strip('_')
        print >>VERBOSE, "Forum name: %s" % self.forum
                 
        # Locate thread title and generate slug to use in filenames
        # * Concat 32 chars
        # * Trim trailing spaces
        # * Convert non-alphanumeric to underscores
        # * Convert all alpha to lowercase
        # e.g. 
        #   <title> Israel raids ships carrying aid to Gaza, killings civilians - Page 25 - EXTREMESKINS.com</title>
        # becomes
        #   israel_raids_ships_carrying_aid
        print >>VERBOSE, "Generating nickname for this thread from title..."
        self.slug = ''
        for t in title:
            self.slug += t.strip('_') + '_'
        # Trim the slug down to 32 chars
        self.slug = self.slug[0:32].strip('_')    
        print >>VERBOSE, "Thread nickname: %s" % self.slug

        # Discover if this thread is multi-page
        print >>VERBOSE, "Checking length of %s ..." % self.slug
        # re.search() returns None if there are no matches
        # TODO template the Page numbers interface
        m = re.search(r'Page [0-9]* of ([0-9]*)', self.html)
        if (m == None):
            self.numpages = 1
        else:
            self.numpages = int(m.group(1).strip())
        print >>VERBOSE, "Found %s page(s) of posts." % self.numpages
 

