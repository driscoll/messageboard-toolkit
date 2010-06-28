#!/usr/bin/python

import re
import vbutils


def scrapeForumName(html):
    """Scrape forum name out of HTML"""
    # TODO Relying on vB convention, need to template
    if html:
        titletag = html[(html.find('<title>')+7):html.find('</title>')].strip()
        return titletag.split('-').pop().strip()
    else:
        return ''

def scrapeTitle(html):
    """Scrape thread title out of HTML"""
    # TODO Relying on vB convention, need to template
    title = ''
    if html:
        titletag = html[(html.find('<title>')+7):html.find('</title>')].strip()
        for t in titletag.split('-')[0:-1]:
            title += t.strip() + '_'
    if title:
        return title[:-1]
    return ''

def scrapeNumPages(html):
    """Scrape number of pages from thread"""
    # TODO based on vB convention, need template
    if html:
        m = re.search(r'Page [0-9]* of ([0-9]*)', html)
        if m:
            return int(m.group(1).strip())
    return 1

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

def scrapePosts(html):
    """Return list of Post objects scraped from raw HTML

    html: List of html pages
    """
    if (type(html) == type(str())):
        s = html 
        html = []
        html.append(s) 

    post = {}
    
    for h in html:
        # Locate posts in h 
        # TODO THIS IS WHERE I LEFT OFF
        # Parse all posts out of h
        #   start with <div id="posts">
        # Create Post objects and append to the post dict
        pass 
    return post 

def scrapeID(html):
    """Scrape and return thread ID from chunk of HTML"""
    pattern = r't=([0-9]*)[^\'"]*goto=next'
    m = re.search(pattern, html)
    if m:
        return m.group(1).strip()
    return ''

def scrapeURL(id, html):
    """Scrape and return thread URL from chunk of HTML"""
    # TODO Some vB installation have only relative links 
    # TODO Not sure how to get the URL in that case 
    pattern = r'http://[^\'"]*showthread[^\'"]*t=%s[^\'"]*' % id
    m = re.search(pattern, html)
    if m:
        return vbutils.cleanURL(m.group(0).strip())
    return ''

