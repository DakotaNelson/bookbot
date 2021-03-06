import re
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup, Comment

def search_tind(search_term):
    q = "itemtype:ebook OR 245:'electronic resource' {}".format(search_term)
    payload = {
            'ln': 'en', # english
            'rg': 100, # return 100 results at a time
            'of': 'xm', # output xml
            'p': q
    }

    r = requests.get('https://olin.tind.io/search', params=payload)

    soup = BeautifulSoup(r.text, 'xml')

    # comments = soup.findAll(text=lambda text:isinstance(text, Comment))
    # num_results = comments[0].split(': ')[1]

    results = []
    for result in soup.select('record'):
        # get the title and author
        for subfield in result.find_all(tag='245'):
            title = None
            try:
                title = subfield.find_all(code='a')[0].text
            except IndexError:
                pass

            author = None
            try:
                author = subfield.find_all(code='c')[0].text
            except IndexError:
                pass

        # get a link
        link = None
        for subfield in result.find_all(tag='856'):
            try:
                link = subfield.find_all(code='u')[0].text
            except IndexError:
                pass

        # get the book description
        desc = None
        for subfield in result.find_all(tag='520'):
            try:
                desc = subfield.find_all(code='a')[0].text
            except IndexError:
                pass

        results.append({
            'title':title,
            'link':link,
            'author':author,
            'description': desc
        })

    return results
