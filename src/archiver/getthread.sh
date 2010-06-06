#!/bin/bash
#
# Thread archiver 
# for vBulletin messageboards
#
# (c) Kevin Driscoll, kedrisco@usc.edu
#
# Last changed: 5 June 2010
#

echo
# ASCII art USC logo
echo "      ___           ___           ___     "
echo "     /__/\         /  /\         /  /\    "
echo "     \  \:\       /  /:/_       /  /:/    "
echo "      \  \:\     /  /:/ /\     /  /:/     "
echo "  ___  \  \:\   /  /:/ /::\   /  /:/  ___ "
echo " /__/\  \__\:\ /__/:/ /:/\:\ /__/:/  /  /\/"
echo " \  \:\ /  /:/ \  \:\/:/~/:/ \  \:\ /  /:/"
echo "  \  \:\  /:/   \  \::/ /:/   \  \:\  /:/ "
echo "   \  \:\/:/     \__\/ /:/     \  \:\/:/  "
echo "    \  \::/        /__/:/       \  \::/   "
echo "     \__\/         \__\/         \__\/ "
echo
echo Starting Thread Archiver ...
echo Initializing variables ...

USERAGENT='HTTP_USER_AGENT:Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.17) Gecko/2010010604 Ubuntu/9.04 (jaunty) Firefox/3.0.17'
# Add this to wget if the host is rejecting us for being wget :,-( 
# --user-agent=$USERAGENT 

# URL to the thread should be the first parameter
RAWURL=$1
echo Validating URL ...
# Is it a valid vBulletin thread URL?
# This is janky verification but it's a start
if [ -z '$(echo '$RAWURL'| grep 'showthread')' ]; then
    echo *****
    echo Error: $RAWURL is not a valid vBulletin thread URL.
    echo *****
    echo
    exit
fi
# Drop the &page= parameter for multipage threads
URL=$(echo $RAWURL |sed 's/&page=[0-9]*\([^0-9]\)/\1/g')
echo Valid URL: $URL

# Locate thread title and generate slug to use in filenames
# 1. Get HTML
# 2. Find line with title tag
# 3. Find thread title
# 4. Concat 32 chars
# 5. Trim trailing spaces
# 6. Convert non-alphanumeric to underscores
# 7. Convert all alpha to lowercase
# e.g. 
#   <title> Israel raids ships carrying aid to Gaza, killings civilians - Page 25 - EXTREMESKINS.com</title>
# becomes
#   israel_raids_ships_carrying_aid
echo Generating nickname for this thread from title...
SLUG=$(wget -O - -q "$URL" | grep -m 1 '^.*<title>' | sed -e 's/<title>[ ]*\([^-]\+\).*$/\1/' -e 's/ *$//' -e 's/^\(.\{0,32\}\).*$/\1/' -e 's/[^a-zA-Z0-9]/_/g' -e 's/^_*\([^_].*[a-zA-Z0-9]\)_*$/\1/' | tr "[:upper:]" "[:lower:]") 
echo Thread nickname: $SLUG

# Locate forum name and create slug to use in filenames
# (Very similar process as above...)
echo Discovering forum name ...
FORUM=$(wget -O - -q "$URL" | grep -m 1 '<title>' | sed -e 's/^.*<title>.* - \([^<]*\)<\/title>.*$/\1/' -e 's/^\(.\{0,32\}\).*$/\1/' -e 's/ *$//' -e 's/[^.a-zA-Z0-9]/_/g' | tr "[:upper:]" "[:lower:]") 
echo Forum name: $FORUM

# Count up the subdirs in this URL
#   Sometimes vBulletin is installed in root
#   Sometimes it is in a subdir
# We need to know this number so we can tell wget to chill later
SUBDIRS=$(echo $URL |sed 's/^.*\/\/[^/]*\///g' |awk -F'/' '{print NF-1}')
# Note: we ask awk to print NF-1 because it counts the newline as a record
#   Weirdness due to using forward slash as field separator
# See manual for explanation: 
# http://www.gnu.org/software/gawk/manual/gawk.html#Command-Line-Field-Separator

echo Found $SUBDIRS sub-dir in the URL ...

# Create sub-dir with human-readable date-time, e.g. 20070304T203217
DATE=$(date +%Y%m%dT%H%M%S)
if [ -z "$2" ]; then
    LOCALDIR=.
else
    # Remove trailing slashes (if any)
    LOCALDIR=$(echo "$2" |sed 's/\/*$//')
fi
NEWDIR=$LOCALDIR/$FORUM/$SLUG/$DATE
echo Discovering target directory... 
if [ ! -e $LOCALDIR/$FORUM ]; then
    echo "$LOCALDIR/$FORUM/ doesn't exist. Creating ..."
    mkdir $LOCALDIR/$FORUM
fi
if [ ! -e $LOCALDIR/$FORUM/$SLUG ]; then
    echo "$LOCALDIR/$FORUM/$SLUG doesn't exist. Creating ..."
    mkdir $LOCALDIR/$FORUM/$SLUG
fi
mkdir $NEWDIR
LOGFILE=$LOCALDIR/$FORUM/$SLUG.log
if [ -e $NEWDIR ]; then
    echo Successly created $NEWDIR
fi

# Download HTML from first page
# Parse to discover if it is multi-page
echo Checking length of $SLUG ...
MAXPAGES=$(wget -O - -q "$URL" | grep -P -m 1 'Page [0-9]+ of ([0-9]+)' | sed 's/^.*Page [0-9]* of \([0-9]*\).*$/\1/g')

if [ -z $MAXPAGES ]; then
    MAXPAGES=1
fi
echo "Found $MAXPAGES page(s) of posts."

echo Downloading first page of the thread ...
wget -v -nH --cut-dirs=$SUBDIRS -k -K -E -H -p -P $NEWDIR -S -a $LOGFILE --restrict-file-names=windows -w 2 --random-wait --no-cache --no-cookies "$URL"
echo Download complete!

if (($MAXPAGES > 1)); then
    # This is a multi-page thread!
    
    # Fix page links to point local
    # HTML=filename generated by wget for 1st page in thread
    HTML=$(echo "$URL" | sed -e 's/^.*\(showthread.*\)$/\1/' -e 's/?/@/g').html
    # THREAD=thread ID extracted from the filename
   # THREAD=$(echo "$HTML" | sed 's/^.*t=\([0-9]*\)[^0-9].*$/\1/')

    # TODO regex pattern in this sed is janky because its based on
    # the special character substitions in wget's "windows" 
    # setting (i.e. ? gets replaced by @) - not sure unix is 
    # any better.
    # Flexible, cross-platform solution needed for the future
    # TODO using $THREAD for t= is broken in the link transformation 
    #   not sure why -- maybe a quotes issue? 
    # Using \(t=[0-9]*\)&amp; is a weak hack
    #   Might transform links to threads that we aren't archiving
    #   Result: broken links in the archive
     echo Transforming multi-page links in $NEWDIR/$HTML
    cat $NEWDIR/$HTML | sed 's/http.*\(showthread.*\)?s=[a-z0-9]*&amp;\(t=[0-9]*\)&amp;\(page=[0-9]*\)/\1@\2\&\3.html/g' > output
    # overwrite the wget generated file with our revision
    # DEBUG change below to cp for useful debug 
    mv output $NEWDIR/$HTML

    for p in $(seq 2 $MAXPAGES);
    do
        echo Downloading page $p of $MAXPAGES ...
        wget -v -nH --cut-dirs=$SUBDIRS -k -K -E -H -p -P $NEWDIR -N -a $LOGFILE --restrict-file-names=windows -w 2 --random-wait --no-cache --no-cookies "$URL&page=$p"
        echo Download complete!

        # Transform links in this new file, too 
        HTML=$(echo "$URL" | sed -e 's/^.*\(showthread.*\)$/\1/' -e 's/?/@/g').html
        echo Transforming multi-page links in $NEWDIR/$HTML
        cat $NEWDIR/$HTML | sed 's/http.*\(showthread.*\)?s=[a-z0-9]*&amp;\(t=[0-9]*\)&amp;\(page=[0-9]*\)/\1@\2\&\3.html/g' > output
        # DEBUG change below to cp for useful debug
         mv output $NEWDIR/$HTML
 
    done

fi

echo See $LOGFILE for details.
echo
echo Goodbye.
echo
