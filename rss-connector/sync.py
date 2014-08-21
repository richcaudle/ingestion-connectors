import requests
import sys
import time
import json
import xml2json
import threading

from xml.etree import ElementTree

fullArticle = False

def GetRSSFeed(url):
    sys.stderr.write('Getting RSS feed: ' + url+ '\n')

    response = requests.get(url)

    if response.status_code != 200:
        sys.stderr.write('Status: ' + str(response.status_code) + ', Error requesting RSS feed. ' + url + '\n')
    else:
        # To print out RSS result as JSON
        # sys.stdout.write(xml2json.xml2json(response.content))

        data = ElementTree.fromstring(response.content)

        for item in data.findall("./channel/item"):

            if fullArticle:
                for child in item.getchildren():
                    if child.tag == "link":
                        thread = threading.Thread(target=GetWebPage, args = (child.text,))
                        thread.start()
                        thread.join()
            else:
                sys.stdout.write(xml2json.elem2json(item) +'\n')

def GetWebPage(url):
    sys.stderr.write('Getting web page: ' + url+ '\n')

    response = requests.get(url)

    if response.status_code != 200:
        sys.stderr.write('Status: ' + str(response.status_code) + ', Error requesting web page. ' + url + '\n')
    else:
        pass
        #sys.stdout.write(xml2json.xml2json(response.content))

feeds = ['http://feeds.bbci.co.uk/news/rss.xml']

for feed in feeds:
    GetRSSFeed(feed)

