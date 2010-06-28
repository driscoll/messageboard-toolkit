#!/usr/bin/python
#
# Thread archiver
# for vBulletin messageboards
#
# (c) Kevin Driscoll, kedrisco@usc.edu
#
# Last changed: 20 June 2010
#

from __future__ import with_statement

import getopt
import json
import os
import re
import shlex
import subprocess
import sys
import urllib2

import vbforum
import vbthread
import vbutils


def isValidDir(localdir):
    """Check if a valid archive exists at localdir
    """
    # TODO Create a method to validate an archive 
    pass 

class Archive:
    """Programmable access to archive of threads on disk
    """
    
    def __init__(self, localdir, summary = 'archive.json'):
        
        self.forum = {} 
  
        # Check if localdir exists 
        if not os.access(localdir, os.F_OK):
            # Create a new local archive dir 
            os.mkdir(localdir)
                        
        self.localdir = localdir
        
        # Check if summary file exists
        if not os.access(os.path.join(localdir, summary), os.F_OK):
            # Create empty JSON summary file 
            self.dumpJSON()
         
        # Load data from a summary file 
        self.loadJSON()
 
    def loadJSON(self, localdir = '', filename = 'archive.json'):
        """Load archive data from summary file
        """
        # localdir and filename exist so that users can specify
        # alternate summary files
        if localdir == '':
            localdir = self.localdir

        # Load JSON data into a dictionary
        with open(os.path.join(localdir, filename), 'r') as j:
            data = json.load(j)
       
        print "This archive summary was last updated: %s" % data["lastupdate"]
 
        for forumid, forumobj in data["forum"].iteritems():
            # Create Forum object for each archived forum
            self.forum[forumid] = vbforum.Forum(forum)
        
            # Create Thread object for each archived thread
            for threadid, threadobj in data["forum"][forumid]["thread"].iteritems():
                # TODO change this after updating the Thread class
                self.forum[forum].thread[threadid] = vbthread.Thread(thread["url"])

            # Create User object for each archived user
            for userid, userobj in data["forum"][forumid]["user"].iteritems():
                self.forum[forum].user[userid] = vbuser.User(userid, **userobj)
 
    def dumpJSON(self, localdir = '', filename = 'archive.json', utc = 0):
        """Save archive data to a summary file
        """
        if localdir == '':
            localdir = self.localdir

        # Create dict of the current data model
        archive = {}
        archive["lastupdate"] = vbutils.getDateTime(utc) 
        archive["forum"] = {}
        
        # Loop over each forum
        for forumid, forumobj in self.forum:
           
            archive["forum"][forumid] = {}
            
            # Loop over each thread
            archive["forum"][forumid]["thread"] = {}
            for threadid, threadobj in forumobj.thread:
                # TODO gotta do something about this nightmare!
                # TODO dict exporter in Thread, User?
                archive["forum"][forumid]["thread"][threadid] = {}
                archive["forum"][forumid]["thread"][threadid]["url"] = threadobj.url
                archive["forum"][forumid]["thread"][threadid]["slug"] = threadobj.slug
                archive["forum"][forumid]["thread"][threadid]["numpages"] = threadobj.numpages
                archive["forum"][forumid]["thread"][threadid]["numposts"] = threadobj.numposts
                archive["forum"][forumid]["thread"][threadid]["archive"] = threadobj.archive
                
            # Loop over each user
            archive["forum"][forumid]["user"] = {}
            for userid, userobj in forumobj.user:
                archive["forum"][forumid]["user"][userid] = {}
                archive["forum"][forumid]["user"][userid]["handle"] = userobj.handle
                archive["forum"][forumid]["user"][userid]["joined"] = userobj.joined
                archive["forum"][forumid]["user"][userid]["numposts"] = userobj.numposts
       
        with open(os.path.join(localdir, filename), 'w') as j:
            json.dump(archive, j, indent = 4)
                
    def update(self):
        """Download latest version of all threads
            and update the JSON summary file.
        """
        # Loop over each thread in each forum
        #   and download latest data
        for forumid, forumobj in self.forum.iteritems():
            for threadid, threadobj in forumobj.thread.iteritems():
                vbarchive.downloadThread(threadobj, self.localdir, platform='windows')

        # Sync this Archive object with new data on disk 
        # os.walk gives us an iterator of a dir tree
        # TODO Need to catch errors
        tree = os.walk(self.localdir, topdown=True)

        # All dirs in the root of the archive
        #   should be the names of forums
        cwd = tree.next()[1]

        # Create a Forum object for each subdir
        for f in cwd:
            self._addForum(f)
        
        currentforum = ''
        currentthread = ''
        # Iterate through the rest of the subdirs
        # They won't be a reliable order so we need to
        #   figure out where we are in the tree each time
        for root, dirs, files in tree.next():
            lastdir = os.path.split(root.rstrip('/'))[1]
            # If the last dir is in our list of forum names
            #   then we are seeking thread slugs
            if (lastdir in self.forum.keys()):
                currentforum = lastdir
            elif (vbutils.isDate(lastdir)):
                # This is a leaf
                # Not doing anything with this right now 
                pass
            else:
                # We are in a thread dir
                currentthread = lastdir 
                # Retrieve list of all files/dirs
                instances = os.listdir(os.getcwd())
                # Find the dir of an arbitrary thread instance
                # Its filename will be a valid datetime stamp
                while not (vbutils.isDate(instances[0]) and os.path.isdir(instances[0])):
                    instances.pop(0) 
                files = os.listdir(os.path.join(os.getcwd(), instances[0]))  
                # Find an original html page,
                #   e.g. showthread.php@t=01235.orig
                while not (files[0][:4] == 'show' and files[0][-4:] == 'orig'):
                    files.pop(0)
                
                # TODO Much easier if subdirs = IDs instead of slugs
                # TODO Is this something we should change?
                id = vbutils.findThreadID(files[0])

                # Is there already a thread object?
                if not id in self.forum[currentforum].thread.keys():
                    # Read the original html
                    with open(os.path.join(os.getcwd(), instances[0], files[0]), 'r') as f:
                        orig_html = f.read()

                    # Find the URL in this HTML 
                    url = vbutils.findThreadURL(orig_html, id)
 
                    # Create this thread object 
                    self.addThread(url)

                # self.forum[currentforum].thread[lastdir] = vbthread.Thread(url)
                # Add all of the dated subdirs to Thread.archive list
        
        # If we survive that insane loop,
        #   the data model should be up to date
        # Store this updated data to a JSON summary
        self.dumpJSON()
    
 
    def _addForum(self, forumname):
        """Add a new forum to this archive
        """
        # Does this forum already exist in the archive? 
        if not forumname in self.forum.keys():
            # If not, then create a new Forum object
            self.forum[forumname] = vbforum.Forum(forumname)

    def addThread(self, url):
        """Add a new thread to be tracked by this archive
        """
        # Create Thread object from url
        newthread = vbthread.Thread(url)
        
        # Add a Forum object to this Archive
        self._addForum(newthread.forum)

        # Check if this thread already exists in the forum
        if not newthread.id in self.forum[newthread.forum].thread.keys():
            # Add this Thread object to the Forum object
            self.forum[newthread.forum].thread[newthread.id] = newthread
        
    def addUser(self, url):
        # TODO See addThread for inspiration
        pass

# Destinations for output messages
# TODO gotta be a better way
global VERBOSE
global DEBUG
VERBOSE = vbutils.Devnull()
DEBUG = vbutils.Devnull()

def usage():
    # TODO terribly out of date
    # Conventional UNIX usage message
    print "Usage: getthread.py [-u] [-l TARGET_DIR] THREAD_URL"
    print

def constructLogfile(localdir, forum, slug):
    # TODO we could do something more useful with this logfile
    return localdir + '/' + forum + '/' + slug + '.log'
 
def constructTargetDirs(thread, localdir, utc = 0): 
    """Create needed subdirs to archive thread
        If utc is True, then use UTC time
    """
    
    global VERBOSE

    # Use machine- and human-readable date-time, e.g. 20070304T203217
    date = vbutils.getDateTime(utc)

    # Construct a target directory
    # TODO template this?
    print >>VERBOSE, "Create target directories ..."
    localsubdirs = [thread.forum, thread.slug, date]
    newdir = localdir
    for sub in localsubdirs:
        newdir += '/' + str(sub) 
        # check if newdir exists
        if not os.access(newdir, os.F_OK):
            print >>VERBOSE, "%s doesn't exist. Creating ..." % newdir
            # if not, create it
            os.mkdir(newdir)     
    print >>VERBOSE, "Target directory is %s" % newdir
    return newdir

def wgetPage(thread, page, targetdir, platform = 'unix', logfile = ''):
    """Call wget to download page of a thread to targetdir for local archive
    """

    global VERBOSE

    # Count up the subdirs in this URL
    #   Sometimes vBulletin is installed in root
    #   Sometimes it is in a subdir
    # We need to know this number so we can tell wget to chill later
    subdirs = (thread.url.count('/') - 3)
    print >>VERBOSE, "Found %s sub-dir in the URL ..." % subdirs

    if (page == 1):
        wget_cmd = "wget -v -nH --cut-dirs=%s -k -K -E -H -p -P %s -S -w 1 --random-wait --no-cache --no-cookies \"%s\"" % (subdirs, targetdir, thread.url)
    else:
        wget_cmd = "wget -v -nH --cut-dirs=%s -k -K -E -H -p -P %s -N -w 1 --random-wait --no-cache --no-cookies \"%s&page=%s\"" % (subdirs, targetdir, thread.url, page)

    # Split wget invocation into list for subprocess
    args = shlex.split(wget_cmd)
   
    # Are we specifying a special logfile location?
    if (logfile != ''):
        args.insert(1, '-a')
        args.insert(2, logfile) 

    # Force special character converstion to win32
    # e.g. ? becomes @ (see wget man pages for details)
    if (platform == 'windows'):
        args.insert(1, '--restrict-file-names=windows')

    # subprocess.Popen() will start a subprocess
    # TODO This would be better with a single data structure
    #       of fixed length containing all the processes.
    # TODO need to catch errors
    proc_firstpage = subprocess.Popen(args)
    # .communicate() will grab output and exit info
    # will also half execution until complete
    # TODO Catch errors from communicate()
    proc_firstpage.communicate()

    # Assuming success!
    return 1

def fixMultiPageLinks(thread, page, targetdir, platform='unix'):
    """Transform links to other thread pages in wget's single-page HTML output for local browsing 
    """
    # Fix links in the downloaded page to
    #   point to pages in the local dir
    #   (departing from typical wget behavior)
    # Note: filename is a tuple (name, extension) 
    if (platform == "windows"):
        # wget escapes chrs diff on win32
        # TODO We should transform the filenames
        filename = (thread.url.split('/').pop().replace('?','@'), '.html')
    else:
        # TODO Need to test this on OS X, Linux, etc.
        # What chr might show up in a URL and be escaped?
        filename = (thread.url.split('/').pop(), '.html')

    if (page == 1):
        infilename = filename[0] + filename[1]
    else:
        infilename = filename[0] + '&page=' + str(page) + filename[1]

    # Using with syntax automatically closes the fileobjects
    # Earlier version than Python 2.6, requires import
    # This tempfile will be deleted if all goes well.
    # If it is still in the dir after a crash, we know
    #   roughly where things went wrong.
    tempfilename = '.' + infilename + '.tmp'
    # TODO will these forward slashes work on Windows?
    # TODO might need to use os.path module
    with open((targetdir + '/' + tempfilename),'w') as temppage:
        with open((targetdir + '/' + infilename),'r') as firstpage:
            for line in firstpage:
                
                # Transform links to pages other than page 1
                pattern = r'http://[^\'"]*showthread[^\'"]*t=%s[^\'"]*page=([0-9]*)[^\'"]*' % thread.id
                # Remember filename is a tuple...
                #   which is why it can match both %s
                substitute = r'%s&page=\1%s' % filename
                # Write altered HTML to temporary file
                newline = re.sub(pattern, substitute, line)
                

                # This should transform links to page 1 
                pattern = r'http://[^\'"]*showthread[^\'"]*t=%s[^\'"]*' % thread.id
                # Remember: filename is a tuple...
                #   which is why it can match both %s
                # TODO Is this confusing?
                substitute = filename[0] + filename[1]
                # Write altered HTML to a temporary file
                newline = re.sub(pattern, substitute, line)

                # Write the changed line to the tempfile
                temppage.write(newline)

    # Overwrite the temporary file with the new one
    # (Don't worry: wget created an unchanged version .orig)
    os.rename(targetdir + '/' + tempfilename, targetdir + '/' + infilename)
    
    # Assuming success!    
    return 1

def downloadThread(thread, localdir = '.', logfile = '', platform='unix'):
    """Initiate downloading latest instance of a thread.
    thread: Thread object
    targetdir: String 
    """
    global VERBOSE
   
    # Construct target directories
    targetdir = constructTargetDirs(thread, localdir)
 
    # Loop through pages in thread
    # and download them to the same dir.
    # Wget won't download duplicate files
    # but we still have to fix the local links.
    for page in range(1, (thread.numpages + 1)): 

        # Download page of thread
        print >>VERBOSE, "Downloading page %s of %s ..." % (page, thread.numpages)
        wgetPage(thread, page, targetdir, platform, logfile) 

        # Transform links in local archive
        print >>VERBOSE, "Transforming links ..."
        fixMultiPageLinks(thread, page, targetdir, platform)

    print >>VERBOSE, "Thread download complete!"

def init(argv):
    """Init all globals according to options and params in argv
    Returns string with cleaned up URL of a thread to archive
    """
    
    # Destinations for output
    # TODO create logfile at some point?
    global VERBOSE
    global DEBUG

    params = {}
    params = { "utc" : 0,
                "localdir" : '.' }

    # wget uses _platform for escaping illegal chrs in filenames
    if (sys.platform in "win32"):
        params["platform"] = "windows"
    else:
        params["platform"] = "unix"

    # params["useragent"] = "HTTP_USER_AGENT:Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.17) Gecko/2010010604 Ubuntu/9.04 (jaunty) Firefox/3.0.17"
        
    # Check the commandline for arguments
    try:                                
        opts, args = getopt.getopt(argv, "dhl:uvw", ["debug", "help", "localdir=", "utc", "verbose", "windows"])
    except getopt.GetoptError:
        # Found a flag not in our known list
        # Returning a short usage message ...
        print "Error: unrecognized flag"
        usage()
        # ... and bye-bye! 
        sys.exit(2)
  
    # Evaluate commandline options, arguments
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-v", "--verbose"):
            VERBOSE = sys.stdout 
        elif opt in ("-d", "--debug"):
            DEBUG = sys.stdout
        elif opt in ("-u", "--utc"):
            params["utc"] = 1
        elif opt in ("-l", "--localdir"):
            # TODO need to validate the directory
            # strip trailing slashes
            params["localdir"] = arg.rstrip('/')
        elif opt in ("-w", "--windows"):
            params["platform"] = "windows"
        else:
            print >>DEBUG, "opt: %s, arg: %s" % (opt, arg)

    # Should be exactly 1 positional argument
    # URL to the thread should be the only argument 
    try:
        raw_URL = args[0]
    except IndexError:
        print "getthread.py: missing URL"
        usage()
        sys.exit(2)

    # Is raw_URL a valid vB thread URL?
    print >>VERBOSE, "Validating URL ..."
    if not (vbutils.isValidURL(raw_URL)):
        print "Error: %s is not a valid vBulletin thread URL." % raw_URL
        print
        sys.exit(2)

    # Clean up URL from the commandline 
    # Keep the domain, sub dirs, showthread, and &t=
    params["url"] = vbutils.cleanURL(raw_URL)
    print >>VERBOSE, "Valid thread URL: %s" % url
    return params 

def main(argv):
  
    # Eval commandline opts/args, return dict params 
    params = init(argv)
 
    # Create Thread object from this URL
    thread = vbthread.Thread(params["url"])

    # One logfile per thread
    # Subsequent archives will append to this logfile
    params["logfile"] = constructLogfile(params["localdir"], forum, slug)

    downloadThread(thread, targetdir, params["logfile"])

    print >>VERBOSE, "See %s for details." % params["logfile"]
    print
    print >>VERBOSE, "Goodbye."
    print
    
   
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "Error: missing URL"
        usage()
        sys.exit(2)
    else:
       # sys.argv[0] is the name of this script
        # sys.argv[1:] is everything else on the commandline
        main(sys.argv[1:])

