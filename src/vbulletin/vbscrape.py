#!/usr/bin/python

import BeautifulSoup
import re
import vbpost
import vbutils

def stripTags(s):
    """Uses BeautifulSoup to strip tags, scripts from html string"""
    soup = BeautifulSoup.BeautifulSoup(s)
    return ''.join(soup.findAll(text = True))


def scrapePosts(html):
    """Return list of Post objects scraped from raw HTML

    html: List of html pages
    """
    if not (type(html) == type([])):
        s = html 
        html = []
        html.append(s) 

    post = {}
    
    for h in html:
        # Locate posts in h 
        for id in scrapePostIDs(h):
            post[id] = vbpost.Post(rawhtml = scrapePostHTML(id, h))

    return post 

def scrapePostMessage(html):
    """Return content from first post in str of HTML"""
    comment = r'message'
    return scrapeComment(comment, html).strip()

def scrapePostEditNote(html):
    """Return edit notes from first post in str of HTML

    TODO For now this returns a string but
            we could create an EditNote class.
         Could be a fruitful area of analysis.
    """
    comment = r'edit note'
    return scrapeComment(comment, html).strip()

def scrapePostSig(html):
    """Return content from first post in str of HTML"""
    comment = r'sig'
    return scrapeComment(comment, html).strip()

def scrapePostAuthorID(html):
    """Return user ID for author of first message in str of HTML
    
    Some forums allow users to post without logging in.
    They may be 'Guests' or 'Anonymous'.
    Regardless, they have no User ID so this returns -1.
    """
    pattern = r'u=([0-9]*)'
    m = re.search(pattern, html)
    if m == None:
        # User is probably logged in as Guest
        return -1
    else:
        return m.group(1).strip()

def scrapePostDate(html):
    """Return post date for first message found in a str of HTML"""
    comment = r'status icon and date'
    messydate = stripTags(scrapeComment(comment, html, False)).strip()
    # TODO Need to move from UTF-8 to Unicode
    messydate = messydate.encode("utf-8", "replace")
    return vbutils.convertDateTime(messydate)

def scrapePostPermalink(html, id = ''):
    """Return first post permalink in str of html

    CAUTION: Permalink may be a relative URL."""
    if id:
        pattern = r'<a href="([^"]*)(showpost\.php\?)[^"]*(p=%s)[^"]*"[^>]*id="postcount.*>' % id
    else:
        pattern = r'<a href="([^"]*)(showpost\.php\?)[^"]*(p=[0-9]*)[^"]*"[^>]*id="postcount.*>'
    m = re.search(pattern, html)
    if m == None:
        return ''
    else:
        return ''.join(m.groups())

def scrapePostCount(html, id = ''):
    """Return first postcount in str of html"""
    if id:
        pattern = r'id="postcount%s" name="([0-9]*)"' % id
    else:
        pattern = r'id="postcount[0-9]*" name="([0-9]*)"'
    m = re.search(pattern, html)
    if m == None:
        return -1
    else:
        return m.group(1)

def scrapePostID(html):
    """Return first Post ID found in a str of HTML"""
    # Try first looking in the comments
    pattern = []
    pattern.append(r'<!-- post #([0-9]*) -->')
    pattern.append(r'p=([0-9]*)')
    p = 0
    m = None
    while (m == None) and (p < len(pattern)):
        m = re.search(pattern[p], html)
        p += 1
    if m == None:
        return -1
    else:
        return m.group(1)

def scrapePostTitle(html):
    """Return first message title found in str of HTML"""
    comment = r'icon and title'
    messytitle = stripTags(scrapeComment(comment, html)).strip()
    # TODO Need to move from UTF-8 to Unicode
    messytitle = messytitle.encode('utf-8', 'replace')
    return messytitle
    
def scrapePostIDs(html):
    """Returns list of Post IDs scraped from str of HTML"""
    pattern = r'<!-- post #([0-9]*) -->'
    return re.findall(pattern, html)

def scrapePostHTML(id, html):
    """Returns HTML chunk for given Post ID"""
    pattern = '<!-- post #%s -->' % id
    start = html.find(pattern)
    pattern = '<!-- / post #%s -->' % id
    end = html.find(pattern) + len(pattern)
    return html[start:end]


def scrapeThreadTitle(html):
    """Scrape thread title out of an HTML page"""
    # TODO Relying on vB convention, need to template
    title = ''
    if html:
        titletag = html[(html.find('<title>')+7):html.find('</title>')].strip()
        for t in titletag.split('-')[0:-1]:
            title += t.strip() + '_'
    if title:
        return title[:-1]
    return ''

def scrapeThreadID(html):
    """Return thread ID from str of HTML"""

    pattern = []

    # Yuku (Survivor Sucks)
    pattern.append(r'topic/([0-9]*)')
    
    # vBulletin (Extreme Skins)
    pattern.append(r't=([0-9]*)[^\'"]*goto=next')
    pattern.append(r'threadid=([0-9]*)')
    pattern.append(r't=([0-9]*)')
    pattern.append(r'/([0-9]*)-[^\.]*.html')
    pattern.append(r't([0-9]+)')
    
    # (Pricescope)
    pattern.append(r'topicID=([0-9]*)') 

    
    m = None
    p = 0
    while (m == None) and (p < len(pattern)):
        print "Trying %s" % pattern[p]
        m = re.search(pattern[p], html)
        p += 1

    if m:
        return m.group(1).strip()
    else:
        print "Thread ID not found."
        return ''

def scrapeThreadIDs(html):
    """Return list of all IDs found in a chunk of HTML

    Note: for user history searches, this includes dupes"""
    ids = []
    someid = scrapeThreadID(html)
    while someid:
        ids.append(someid)
        html = html[(html.find(someid)+len(someid)):]
        someid = scrapeThreadID(html)  
    return ids 

def scrapeThreadURL(id, html):
    """Return thread URL from str of HTML"""
    # TODO Some vB installation have only relative links 
    # TODO Not sure how to get the URL in that case 
    pattern = r'http://[^\'"]*showthread[^\'"]*t=%s[^\'"]*' % id
    m = re.search(pattern, html)
    if m:
        return vbutils.cleanURL(m.group(0).strip())
    return ''


def scrapeNumPages(html):
    """Return num of pages by parsing HTML of one page"""
    # TODO based on vB convention, need template
    if html:
        m = re.search(r'Page [0-9]* of ([0-9]*)', html)
        if m:
            return int(m.group(1).strip())
    return 1

def scrapeForumName(html):
    """Return forum name found in str of HTML"""
    # TODO Relying on vB convention, need to template
    if html:
        titletag = html[(html.find('<title>')+7):html.find('</title>')].strip()
        return titletag.split('-').pop().strip()
    else:
        return ''

def scrapeForumVersion(html):
    """Returns string containing vB version"""
    # Trim down to just the contents of the head tag
    html = html[html.find('<head>'):html.find('</head>')]
    # Get rid of the contents of the title tag
    starttitle = html.find('<title>')
    endtitle = html.find('</title>')
    html = html[:starttitle] + html[endtitle:]
    # Now search for vBulletin within the automatically-
    #   generated code. No user input is considered.
    start = html.find('vBulletin')
    if (start > -1):
        pattern = []
        pattern.append(r'vBulletin ([0-9\.]+)')
        pattern.append(r'vBulletin[^0-9]*([0-9\.]+)')
        m = None
        p = 0
        while (not m) and (p < len(pattern)):
            m = re.search(pattern[p], html[start:start + 20])
            p += 1
        if m:
            return m.group(1)  
    return ''

def scrapeComment(opening, html, includetags = False):
    """Returns str of html enclosed by comment s"""
    if not (opening.startswith('<!-- ')):
        opening = '<!-- %s -->' % opening

    start = html.find(opening)

    if (start > -1): 
        closing = opening[:5] + '/ ' + opening[5:]
        end = html.find(closing, (start+len(opening)))
        
        if includetags:
            end += len(closing)
        else:
            start += len(opening)

        try:
            content = html[start:end].encode('utf-8', 'replace')
        except UnicodeDecodeError:
            print "***********"
            print "UnicodeDecodeError on str:"
            print
            print html[start:end] 

        return content
    else:
        # html.find() returns -1 if comment isn't found
        return '' 

def scrapeUserAvatar(html):
    """Return URL pointing at User avatar"""
    pass

def scrapeUserNumPosts(html):
    """Return integer number of posts"""
    pass



