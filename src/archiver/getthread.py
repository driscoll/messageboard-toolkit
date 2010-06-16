#!/usr/bin/python
#
# Thread archiver
# for vBulletin messageboards
#
# (c) Kevin Driscoll, kedrisco@usc.edu
#
# Last changed: 11 June 2010
#

from datetime import datetime
import getopt
import os
import re
import shlex
import subprocess
import sys
import urllib2

# TODO Not sure why I did underscore style
# Should check the style guide
# These should prob be all caps
global _verbose
global _debug
global _utc
global _localdir
global _logfile
global _platform
global _useragent

def usage():
    # Conventional UNIX usage message
    print "Usage: getthread.py [-u] THREAD_URL [TARGET_DIR]"
    print

def main(argv):
    # Init global variables 
    _verbose = 0
    _debug = 0
    _utc = 0
    _localdir = '.'
    _logfile = ''
    # wget uses _platform for escaping illegal chrs in filenames
    if (sys.platform in "win32"):
        _platform = "windows"
    else:
        _platform = "unix"

    # _useragent = "HTTP_USER_AGENT:Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.17) Gecko/2010010604 Ubuntu/9.04 (jaunty) Firefox/3.0.17"
        
    # Check the commandline for arguments
    try:                                
        opts, args = getopt.getopt(argv, "dhl:uvw", ["debug", "help", "localdir=", "utc", "verbose", "windows"])
    except getopt.GetoptError:
        # Found a flag not in our known list
        # Returning a short usage message ...
        print "getthread.py: unrecognized flag"
        usage()
        # ... and bye-bye! 
        sys.exit(2)
  
    # Evaluate commandline options, arguments
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-v", "--verbose"):
            _verbose = 1
        elif opt in ("-d", "--debug"):
            _debug = 1
        elif opt in ("-u", "--utc"):
            _utc = 1
        elif opt in ("-l", "--localdir"):
            # TODO need to validate the directory
            # strip trailing slashes
            _localdir = arg.rstrip('/')
        elif opt in ("-w", "--windows"):
            _platform = "windows"
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
    # TODO This is janky verification but it's a start
    print "Validating URL ..."
    if (raw_URL.find('showthread') == -1):
        print "*****"
        print "Error: %s is not a valid vBulletin thread URL." % raw_URL
        print "*****"
        print
        sys.exit(2)

    # Drop the &page= parameter for multipage threads
    # url = re.sub('&page=[0-9]*','',raw_URL)
    # Or... drop all parameters except for &t=
    # TODO are there parameters worth keeping?
    url = re.sub(r'[&@?][^t][a-zA-Z]*=[a-zA-Z0-9]*','',raw_URL)
    if not (url.startswith('http://')):
        url = 'http://' + url
    print "Valid thread URL: %s" % url

    # Generate urllib2 request object from the URL
    req = urllib2.Request(url)
    # Get the HTML of the first page in the thread
    # TODO catch errors
    response = urllib2.urlopen(url)
    html = response.read()
 
    # Locate contents of title
    # Split the resulting string by -
    #   TODO this should be templated 
    title = re.sub(r'[^a-zA-Z0-9-]',r'_',
        html[(html.find('<title>')+7):
        html.find('</title>')]).lower().split('-')
    
    # Pop forum name and create slug to use in filenames
    # TODO Relying on vB convention, need to template
    print "Discovering forum name ..."
    forum = title.pop().strip('_')
    print "Forum name: %s" % forum
    
    # Locate thread title and generate slug to use in filenames
    # * Concat 32 chars
    # * Trim trailing spaces
    # * Convert non-alphanumeric to underscores
    # * Convert all alpha to lowercase
    # e.g. 
    #   <title> Israel raids ships carrying aid to Gaza, killings civilians - Page 25 - EXTREMESKINS.com</title>
    # becomes
    #   israel_raids_ships_carrying_aid
    print "Generating nickname for this thread from title..."
    slug = ''
    for t in title:
        slug += t.strip('_') + '_'
    # Trim the slug down to 32 chars
    slug = slug[0:32].strip('_')    
    print "Thread nickname: %s" % slug

    # Discover if this thread is multi-page
    print "Checking length of %s ..." % slug
    # re.search() returns None if there are no matches
    # TODO template the Page numbers interface
    m = re.search(r'Page [0-9]* of ([0-9]*)', html)
    if (m == None):
        maxpages = 1
    else:
        maxpages = int(m.group(1).strip())
    print "Found %s page(s) of posts." % maxpages

    # Create sub-dir with human-readable date-time, 
    #   e.g. 20070304T203217
    if _utc:
        date = datetime.utcnow().strftime('%Y%m%dT%H%M%S')
    else:
        date = datetime.now().strftime('%Y%m%dT%H%M%S')
  
    # Construct a target directory
    # TODO template this?
    print "Create target directories ..."
    localsubdirs = [forum, slug, date]
    newdir = _localdir
    for sub in localsubdirs:
        newdir += '/' + str(sub) 
        # check if newdir exists
        if not os.access(newdir, os.F_OK):
            print "%s doesn't exist. Creating ..." % newdir
            # if not, create it
            os.mkdir(newdir)     
    print "Target directory is %s" % newdir

    # One logfile per thread
    # For subsequent archives will append to this logfile
    _logfile = _localdir + '/' + forum + '/' + slug + '.log'

    # Count up the subdirs in this URL
    #   Sometimes vBulletin is installed in root
    #   Sometimes it is in a subdir
    # We need to know this number so we can tell wget to chill later
    subdirs = (url.count('/') - 3)
    print "Found %s sub-dir in the URL ..." % subdirs

    print "Downloading first page of the thread ..."
    wget_cmd = "wget -v -nH --cut-dirs=%s -k -K -E -H -p -P %s -S -a %s --restrict-file-names=%s -w 1 --random-wait --no-cache --no-cookies \"%s\"" % (subdirs, newdir, _logfile, _platform, url)
    args = shlex.split(wget_cmd)
    # subprocess.Popen() will start a subprocess
    # TODO This would be better with a single data structure
    #       of fixed length containing all the processes.
    proc_firstpage = subprocess.Popen(args)
    # .communicate() will grab output and exit info
    # will also half execution until complete
    # TODO Catch errors from communicate()
    proc_firstpage.communicate()
    print "Download complete!"


# TODO TEST MULTI PAGE


    if (maxpages > 1):
        # This is a multi-page thread!
        
        # Fix links in the downloaded page to
        #   point to pages in the local dir
        #   (departing from typical wget behavior)
        # Note: filename is a tuple (name, extension) 
        if (_platform == "windows"):
            # wget escapes chrs diff on win32
            filename = (url.split('/').pop().replace('?','@'), '.html')
        else:
            # TODO Need to test this on OS X, Linux, etc.
            # What chr might show up in a URL and be escaped?
            filename = (url.split('/').pop(), '.html')

        # Every vB thread has a unique numerical ID
        # TODO should we do this earlier?
        print "Seeking thread ID ..."
        m = re.search(r't=([0-9]*)', filename[0])
        if m == None:
            print '*****'
            print 'Could not locate thread ID in URL.'
            print '*****'
            print
            sys.exit(2)
        else:
            id = m.group(1).strip()
        print "Thread ID: %s" % id

        print "Transforming multi-page links in %s/%s%s" % (newdir, filename[0], filename[1])

        # Using with syntax automatically closes the fileobjects
        # Earlier version than Python 2.6, requires import
        tempfilename = '.' + filename[0] + filename[1] + '.tmp'
        # TODO will these forward slashes work on Windows?
        # TODO might need to use os.path module
        with open((newdir + '/' + tempfilename),'w') as temppage:
            with open((newdir + '/' + filename[0] + filename[1]),'r') as firstpage:
                for line in firstpage:
                    pattern = r'http://.*showthread.*t=%s.*page=([0-9]*)[^\'"]*' % id
                    # Remember that filename is a tuple...
                    #   which is why it can match both %s
                    substitute = r'%s&page=\1%s' % filename
                    # Write altered HTML to a temporary file
                    temppage.write(re.sub(pattern, substitute, line))
        # Overwrite the temporary file with the new one
        # wget created an unchanged version .orig
        os.rename(newdir + '/' +tempfilename, newdir + '/' +filename[0]+filename[1])

        # Now loop through the remaining pages
        # and download them to the same dir.
        # Wget won't download duplicate files
        # but we still have to fix the local links.
        for page in range(2, (maxpages + 1)): 

            print "Downloading page %s of %s ..." % (page, maxpages)
            wget_cmd = "wget -v -nH --cut-dirs=%s -k -K -E -H -p -P %s -N -a %s --restrict-file-names=%s -w 1 --random-wait --no-cache --no-cookies \"%s&page=%s\"" % (subdirs, newdir, _logfile, _platform, url, page)
            args = shlex.split(wget_cmd)
            # subprocess.Popen() will start a subprocess
            # TODO Need process stack structure (see above)
            proc_nextpage = subprocess.Popen(args)
            # .communicate() will grab output and exit info
            # will also half execution until complete
            # TODO Catch errors from communicate()
            proc_nextpage.communicate()
            print "Download complete!"

            # Using with syntax automatically closes the fileobjects
            # Earlier than Python 2.6, requires import
            # TODO template this suffix
            # TODO clean up these variable names, confusing
            nextfilename = filename[0] + '&page=' + str(page) + filename[1]
            print "Transforming multi-page links in %s" % (newdir + '/' + nextfilename)
            tempfilename = '.' + nextfilename + '.tmp'
            with open((newdir + '/' +tempfilename),'w') as temppage:
                with open((newdir + '/' +nextfilename),'r') as firstpage:
                    for line in firstpage:
                        # TODO this isn't working for pages >1 
                        pattern = r'http://.*showthread.*t=%s.*page=([0-9]*)[^\'"]*' % id
                        # Remember: filename is a tuple...
                        #   which is why it can match both %s
                        # TODO Is this confusing?
                        substitute = r'%s&page=\1%s' % filename
                        # Write altered HTML to a temporary file
                        temppage.write(re.sub(pattern, substitute, line))
            
            # Overwrite the temporary file with the new one
            # wget created an unchanged version .orig
            os.rename(newdir + '/' +tempfilename, newdir + '/' +nextfilename)

    print "See %s for details." % _logfile
    print
    print "Goodbye."
    print




if __name__ == "__main__":
    if len(sys.argv) < 2:
        print len(sys.argv)
        print "%s: missing URL" % sys.argv[0]
        usage()
        sys.exit(2)
    else:
        # sys.argv[0] is the name of this script
        # sys.argv[1:] is everything else on the commandline
        main(sys.argv[1:])


