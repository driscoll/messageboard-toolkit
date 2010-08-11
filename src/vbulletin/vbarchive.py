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
    
    def __init__(self, 
                localdir = '.', 
                summary = 'archive.json', 
                lastupdate = '',
                platform = 'unix',
                forum = {}
                ):

        if not localdir:
            localdir = '.'
        if not summary:
            summary = 'archive.json'

        if platform in ['unix', 'windows']:
            self.platform = platform
        else:
            self.platform = 'unix'

        # Check if localdir exists 
        if not os.access(localdir, os.F_OK):
            # Create a new local archive dir 
            os.mkdir(localdir)
        self.localdir = localdir
        print "Archive located at %s" % self.localdir

        self.lastupdate = lastupdate
        self.forum = forum 

        # Did we receive forum data as an **arg? 
        if forum:
            print "Forum data received as dict obj."
            # If so, create Forum objs from dict 
            for id, f in forum.iteritems():
                kw = vbutils.convertKeysToStr(f)
                self.forum[id] = vbforum.Forum(**kw)
        
        # If not, does a summary file exist in localdir?
        elif os.access(os.path.join(localdir, summary), os.F_OK):
            # If so, load forum data from the summary file 
            print "Reading forum data from JSON summary."
            self.readSummary()

        else:
            # TODO try to discover thread data and create summary 
            # 
            # Otherwise, create empty JSON summary file 
            print "No JSON summary found in archive dir."
            print "Update this object and it will try to read your archive." 
            self.writeSummary()
        
    def importJSON(self, jsondata):
        """Load archive data from string of JSON data 
        
        TODO implement this method
        """
        pass 

    def readSummary(self, localdir = '', filename = 'archive.json'):
        """Read archive data from summary file
        """
        # localdir and filename args enable users to specify
        # alternate JSON summary files
        if not localdir:
            localdir = self.localdir

        # Load JSON data into a dictionary
        with open(os.path.join(localdir, filename), 'r') as j:
            try:
                # Load JSON data from summary file into dict 
                jsond = json.load(j)
            except:
                print "Could not load JSON data from %s" % (os.path.join(localdir, filename))
                return None
       
        self.lastupdate = jsond["lastupdate"]
        print "This archive summary was last updated: %s" % jsond["lastupdate"]
        
        # Loop over forum dict, creating Forum objects 
        self.forum = {} 
        for forumkey, forumdict in jsond["forum"].iteritems():
            # Create Forum object for each archived forum
            # Can't use unicode strings as keywords in dict :(
            kw = vbutils.convertKeysToStr(forumdict)
            self.forum[forumkey] = vbforum.Forum(**kw)
        
    def exportDict(self):
        """Return dict obj with all Archive data"""
        # Create dict of the current data model
        archive = {}
        archive["lastupdate"] = vbutils.getDateTime() 
        archive["forum"] = {}
        
        # Loop over each forum
        for forumid, forumobj in self.forum.iteritems():
            archive["forum"][forumid] = self.forum[forumid].exportDict() 
        
        return archive            
  
    def exportJSON(self, indent_ = 4):
        """Generate JSON string from this object
        """
        return json.dumps(self.exportDict(), indent = indent_)
       
    def writeSummary(self, localdir = '', filename = 'archive.json', utc = 0):
        """Write archive data to a JSON summary file
        """
        if not localdir:
            localdir = self.localdir

        data = self.exportDict()
   
        with open(os.path.join(localdir, filename), 'w') as summaryf: 
            json.dump(data, summaryf, indent = 4)

    def update(self, platform_ = ''):
        """Download latest version of all threads
            and update the JSON summary file.
        """
        # Very important that platform_ is set correctly
        # Filename transformations depend on this setting
        if not platform_:
            if self.platform:
                platform_ = self.platform
            else:
                platform_ = 'unix'
        
        # Loop over each thread in each forum
        #   and download latest data
        for forumid, forumobj in self.forum.iteritems():
            print "Checking %s threads in %s for updates ..." % (len(forumobj.thread), forumid)
            for threadid, threadobj in forumobj.thread.iteritems():
                # TODO Problem: Thread objects created from
                #   arbitrary HTML/JSON may not have URL 
                #   Maybe we can implement a smarter URL guessing
                #   heuristic based on other things 
                #   Even google search? :-?
                if not downloadThread(threadobj, self.localdir, platform = platform_):
                    print "Failed to download thread %s" % threadobj.title
                    print "Attempting to proceed anyway ..."

        # Sync this Archive object with new data on disk 
        # os.walk gives us an iterator of a dir tree
        # TODO Need to catch errors
        print "Syncing new data in %s" % self.localdir

        currentforum = ''
        currentthreadlist = [] 
        currentthread = ''
        currentinstance = ''
        # Iterate through the rest of the subdirs
        # They won't be a reliable order so we need to
        #   figure out where we are in the tree each time
        for root, dirs, files in os.walk(self.localdir, topdown=True):
            lastdir = os.path.split(root.rstrip('/'))[1]
            nextlastdir = os.path.split(os.path.split(root.rstrip('/'))[0]) 
            if (root == self.localdir):
                # We are in archive root
                # Create a Forum object for each subdir
                for d in dirs:
                    print "Found forum %s" % d
                    self._addForum(d)
            elif (lastdir in self.forum.keys()):
                # We are in a forum dir
                currentforum = lastdir
                # Assume all files are subdirs named by slugs
                # TODO Need to validate these dirs
                currentthreadlist = dirs 
                for t in currentthreadlist:
                    print "Found thread %s" % t
                currentinstance = ''            
            elif (lastdir in currentthreadlist):
                # We are in a thread dir
                currentthread = lastdir
                # Assume all files are subdirs with instances
                # Sort by date 
                print "Reviewing thread %s" % currentthread
                print "Found %s saved instances" % len(dirs)
                dirs.sort()
                dirs = [dirs[0]]
                currentinstance = dirs[0]
                print "Latest update was on %s" % currentinstance
            elif (lastdir == currentinstance):
                # We are in the dir of an instance
                # Find an original html page,
                #   e.g. showthread.php@t=01235.orig
                # TODO this is vB convention need to be template
                try:
                    for f in files:
                        print f
                    orig_file = (f for f in files if (f[:4] == 'show' and f[-4:] == 'orig')).next()
                    print "Found source file: %s" % orig_file
                except:
                    orig_file = ''
                    print "Source HTML file not found"
                    break

                # TODO Much easier if subdirs = IDs instead of slugs
                # TODO Is this something we should change?
                id = vbutils.findThreadID(orig_file)

                # Is there already a thread object?
                if not id in self.forum[currentforum].thread.keys():
                    # Read the original html
                    subdir = root 
                    print "Attempting to read from %s" % subdir
                    with open(os.path.join(subdir, orig_file), 'r') as f:
                        orig_html = f.read()

                    # Find the URL in this HTML 
                    # TODO sometimes the URL is not discoverable
                    url = vbutils.findThreadURL(orig_html, id)
 
                    # Create this thread object 
                    # TODO Try/except might be cleaner
                    if not url:
                        print "No valid URL found in HTML."
                        print "Trying to make Thread object anyway from the HTML."
                        self.addThread(rawhtml_ = orig_html)
                    else:
                        if not self.addThread(url):
                            print "Tried and failed to create Thread object for URL: %s" % url

        # Last update is now!
        self.lastupdate = vbutils.getDateTime()        

        # If we survive that insane loop,
        #   the data model should be up to date
        # Store this updated data to a JSON summary
        self.writeSummary()
    
    def _addForum(self, forumname):
        """Add a new forum to this archive
        """
        # Does this forum already exist in the archive? 
        if not forumname in self.forum.keys():
            # If not, then create a new Forum object
            self.forum[forumname] = vbforum.Forum(forumname)

    def addThread(self, url = '', rawhtml_ = '', threadobj = ''):
        """Add a new thread to be tracked by this archive
        """
        # URL or HTML required to addThread in this manner
        if not (url or rawhtml_ or threadobj):
            return False

        # Create Thread object from url
        if threadobj:
            newthread = threadobj
        else: 
            newthread = vbthread.Thread(url, rawhtml = rawhtml_)
        
        # Add a Forum object to this Archive
        self._addForum(newthread.forum)

        # Check if this thread already exists in the forum
        if not newthread.id in self.forum[newthread.forum].thread.keys():
            # Add this Thread object to the Forum object
            self.forum[newthread.forum].thread[newthread.id] = newthread
       
        # update() should usually be called after addThread 
        # so that the new Thread data is written to disk 

    def addUser(self, url):
        # TODO See addThread for inspiration
        pass

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
    
    # Use machine- and human-readable date-time, e.g. 20070304T203217
    date = vbutils.getDateTime()

    # Construct a target directory
    # TODO template this?
    print "Create target directories ..."
    localsubdirs = [localdir, thread.forum, thread.title, date]
    newdir = os.path.join(*localsubdirs)

    if os.access(newdir, os.F_OK):
        print "Target already exists ..."
    else:
        print "Creating target dirs ..."
        try:
            # makedirs() recursively creates all
            # needed subdirs
            # raises error exception if leaf exists
            # or can't be created
            os.makedirs(newdir)    
        except:
            # because we previously test if leaf
            # exists, we can be sure that this is
            # some other error.
            print "Error: failed to create target dir: %s" % newdir
            return '' 
    print "Target directory is %s" % newdir
    return newdir

def wgetPage(thread, page, targetdir, platform = 'unix', logfile = ''):
    """Call wget to download page of a thread to targetdir for local archive
    """

    if not vbutils.isValidURL(thread.url):
        return False

    # Count up the subdirs in this URL
    #   Sometimes vBulletin is installed in root
    #   Sometimes it is in a subdir
    # We need to know this number so we can tell wget to chill later
    subdirs = (thread.url.count('/') - 3)
    print "Found %s sub-dir in the URL ..." % subdirs

    if (page == 1):
        wget_cmd = "wget -v -nH --cut-dirs=%s -k -K -E -H -p -P %s -S -w 1 --random-wait --no-cache --no-cookies \"%s\"" % (subdirs, targetdir, thread.url)
    else:
        wget_cmd = "wget -v -nH --cut-dirs=%s -k -K -E -H -p -P %s -N -w 1 --random-wait --no-cache --no-cookies \"%s&page=%s\"" % (subdirs, targetdir, thread.url, page)

    # Split wget invocation into list for subprocess
    # TODO Apparently shlex.split can't take unicode arguments?
    # Is this going to be a problem in the future?
    args = shlex.split(str(wget_cmd))
 
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
    return True 

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
    with open(os.path.join(targetdir, tempfilename),'w') as temppage:
        with open(os.path.join(targetdir, infilename),'r') as firstpage:
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
    os.rename(os.path.join(targetdir, tempfilename), os.path.join(targetdir, infilename))
    
    # Assuming success!    
    return 1

def downloadThread(thread, localdir = '', logfile = '', platform='unix'):
    """Initiate downloading latest instance of a thread.
    thread: Thread object
    targetdir: String 
    """
  
    if not localdir:
        if self.localdir:
            localdir = self.localdir
        else:
            localdir = '.'

    # Construct target directories
    targetdir = constructTargetDirs(thread, localdir)
    if not targetdir:
        print "Error creating target dirs. Aborting thread download." 
        # TODO Should probably raise an error here.
        return False 
    
    print targetdir
    return 0 

    # Loop through pages in thread
    # and download them to the same dir.
    # Wget won't download duplicate files
    # but we still have to fix the local links.
    for page in range(1, (thread.numpages + 1)): 

        # Download page of thread
        print "Downloading page %s of %s ..." % (page, thread.numpages)

        # TODO This would be cleaner with try/except
        #       wgetPage needs to raise exceptions
        if (wgetPage(thread, page, targetdir, platform, logfile)):
        
            # Transform links in local archive
            print "Transforming links in page %s ..." % page
            fixMultiPageLinks(thread, page, targetdir, platform)

        else:

            print "Unable to download page %s" % page
            print "Bad URL?"
            print "URL: %s" % str(thread.url)

    print "Thread download complete!"

def init(argv):
    """Init all globals according to options and params in argv
    Returns string with cleaned up URL of a thread to archive
    """
    
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
            pass 
        elif opt in ("-d", "--debug"):
            pass
        elif opt in ("-u", "--utc"):
            params["utc"] = 1
        elif opt in ("-l", "--localdir"):
            # TODO need to validate the directory
            # strip trailing slashes
            params["localdir"] = arg.rstrip('/')
        elif opt in ("-w", "--windows"):
            params["platform"] = "windows"
        else:
            print "opt: %s, arg: %s" % (opt, arg)

    # Should be exactly 1 positional argument
    # URL to the thread should be the only argument 
    try:
        raw_URL = args[0]
    except IndexError:
        print "getthread.py: missing URL"
        usage()
        sys.exit(2)

    # Is raw_URL a valid vB thread URL?
    print "Validating URL ..."
    if not (vbutils.isValidURL(raw_URL)):
        print "Error: %s is not a valid vBulletin thread URL." % raw_URL
        print
        sys.exit(2)

    # Clean up URL from the commandline 
    # Keep the domain, sub dirs, showthread, and &t=
    params["url"] = vbutils.cleanURL(raw_URL)
    print "Valid thread URL: %s" % url
    return params 

def main(argv):
  
    # Eval commandline opts/args, return dict params 
    params = init(argv)
 
    # Create Thread object from this URL
    thread = vbthread.Thread(params["url"])

    # One logfile per thread
    # Subsequent archives will append to this logfile
    params["logfile"] = constructLogfile(params["localdir"], forum, title)

    downloadThread(thread, targetdir, params["logfile"])

    print "See %s for details." % params["logfile"]
    print
    print "Goodbye."
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

