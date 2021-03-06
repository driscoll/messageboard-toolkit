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
from datetime import datetime
from vbthread import Thread
import getopt
# TODO replace mydebug with __init__.py
from mydebug import *
import os
import re
import shlex
import subprocess
import sys
import urllib2

def usage():
    # Conventional UNIX usage message
    print "Usage: getthread.py [-u] [-l TARGET_DIR] THREAD_URL"
    print

def isValidURL(url):
    # TODO This is janky verification but it's a start
    if (url.find('showthread') == -1):
        return False
    else:
        return True

def cleanURL(raw_URL):
    # Drop the &page= parameter for multipage threads
    # url = re.sub('&page=[0-9]*','',raw_URL)
    # Or... drop all parameters except for &t=
    # TODO are there parameters worth keeping?
    url = re.sub(r'[&@?][^t][a-zA-Z]*=[a-zA-Z0-9]*','',raw_URL)
    if not (url.startswith('http://')):
        url = 'http://' + url
    return url

def constructTargetDirs(thread): 
    """Create needed subdirs to archive thread
    """
    # Use machine- and human-readable date-time, e.g. 20070304T203217
    if UTC:
        date = datetime.utcnow().strftime('%Y%m%dT%H%M%S')
    else:
        date = datetime.now().strftime('%Y%m%dT%H%M%S')

    # Construct a target directory
    # TODO template this?
    print >>VERBOSE, "Create target directories ..."
    localsubdirs = [thread.forum, thread.slug, date]
    newdir = LOCALDIR
    for sub in localsubdirs:
        newdir += '/' + str(sub) 
        # check if newdir exists
        if not os.access(newdir, os.F_OK):
            print >>VERBOSE, "%s doesn't exist. Creating ..." % newdir
            # if not, create it
            os.mkdir(newdir)     
    print >>VERBOSE, "Target directory is %s" % newdir
    return newdir

def wgetPage(thread, page, targetdir):
    """Call wget to download page of a thread to targetdir for local archive
    """
    # Count up the subdirs in this URL
    #   Sometimes vBulletin is installed in root
    #   Sometimes it is in a subdir
    # We need to know this number so we can tell wget to chill later
    subdirs = (thread.url.count('/') - 3)
    print >>VERBOSE, "Found %s sub-dir in the URL ..." % subdirs

    if (page == 1):
        wget_cmd = "wget -v -nH --cut-dirs=%s -k -K -E -H -p -P %s -S -a %s --restrict-file-names=%s -w 1 --random-wait --no-cache --no-cookies \"%s\"" % (subdirs, targetdir, LOGFILE, PLATFORM, thread.url)
    else:
        wget_cmd = "wget -v -nH --cut-dirs=%s -k -K -E -H -p -P %s -N -a %s --restrict-file-names=%s -w 1 --random-wait --no-cache --no-cookies \"%s&page=%s\"" % (subdirs, targetdir, LOGFILE, PLATFORM, thread.url, page)

    # Split wget invocation into list for subprocess
    args = shlex.split(wget_cmd)
    
    # subprocess.Popen() will start a subprocess
    # TODO This would be better with a single data structure
    #       of fixed length containing all the processes.
    proc_firstpage = subprocess.Popen(args)
    # .communicate() will grab output and exit info
    # will also half execution until complete
    # TODO Catch errors from communicate()
    proc_firstpage.communicate()

    # Assuming success!
    return 1

def fixMultiPageLinks(thread, page, targetdir):
    """Transform links to other thread pages in wget's single-page HTML output for local browsing 
    """
    # Fix links in the downloaded page to
    #   point to pages in the local dir
    #   (departing from typical wget behavior)
    # Note: filename is a tuple (name, extension) 
    if (PLATFORM == "windows"):
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
                pattern = r'http://.*showthread.*t=%s.*page=([0-9]*)[^\'"]*' % thread.id
                # Remember filename is a tuple...
                #   which is why it can match both %s
                substitute = r'%s&page=\1%s' % filename
                # Write altered HTML to temporary file
                temppage.write(re.sub(pattern, substitute, line))
                

                # TODO This should transform links to page 1 
                pattern = r'http://.*showthread.*t=%s[^\'"]*' % id
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

def downloadThread(thread, targetdir):
    """Initiate downloading latest instance of a thread.
    thread: Thread object
    targetdir: String 
    """
    # Loop through pages in thread
    # and download them to the same dir.
    # Wget won't download duplicate files
    # but we still have to fix the local links.
    for page in range(1, (thread.numpages + 1)): 

        # Download page of thread
        print >>VERBOSE, "Downloading page %s of %s ..." % (page, thread.numpages)
        wgetPage(thread, page, targetdir) 

        # Transform links in local archive
        print >>VERBOSE, "Transforming links ..."
        fixMultiPageLinks(thread, page, targetdir)

    print >>VERBOSE, "Thread download complete!"

def init(argv):
    """Init all globals according to options and params in argv
    Returns string with cleaned up URL of a thread to archive
    """
    # Init global variables 
    global UTC
    global LOCALDIR
    global LOGFILE
    global PLATFORM
    global USERAGENT

    VERBOSE = Devnull() 
    DEBUG = Devnull() 
    UTC = 0
    LOCALDIR = '.'
    LOGFILE = ''
    # wget uses _platform for escaping illegal chrs in filenames
    if (sys.platform in "win32"):
        PLATFORM = "windows"
    else:
        PLATFORM = "unix"

    # USERAGENT = "HTTP_USER_AGENT:Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.17) Gecko/2010010604 Ubuntu/9.04 (jaunty) Firefox/3.0.17"
        
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
            UTC = 1
        elif opt in ("-l", "--localdir"):
            # TODO need to validate the directory
            # strip trailing slashes
            LOCALDIR = arg.rstrip('/')
        elif opt in ("-w", "--windows"):
            PLATFORM = "windows"
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
    if not (isValidURL(raw_URL)):
        print "Error: %s is not a valid vBulletin thread URL." % raw_URL
        print
        sys.exit(2)

    # Clean up URL from the commandline 
    # Keep the domain, sub dirs, showthread, and &t=
    url = cleanURL(raw_URL)
    print >>VERBOSE, "Valid thread URL: %s" % url
    return url

def main(url):
   
    # Create Thread object from this URL
    thread = Thread(url)

    # Construct target directories
    targetdir = constructTargetDirs(thread)

    # One logfile per thread
    # Subsequent archives will append to this logfile
    # TODO we could do something more useful with this logfile
    LOGFILE = LOCALDIR + '/' + thread.forum + '/' + thread.slug + '.log'

    downloadThread(thread, targetdir)

    print >>VERBOSE, "See %s for details." % LOGFILE
    print
    print >>VERBOSE, "Goodbye."
    print

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "Error: missing URL"
        usage()
        sys.exit(2)
    else:
        # Initialize all globals, get URL
        url = init(sys.argv[1:])
        # sys.argv[0] is the name of this script
        # sys.argv[1:] is everything else on the commandline
        main(url)

