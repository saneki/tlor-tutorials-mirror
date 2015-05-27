#!/usr/bin/env python
# Python 3 script to rip tutorial pages from thelegendofrandom.com and
# convert them to markdown.
# Currently handles:
# - Headers (h2)
# - Subheaders (h3)
# - Lists (ul/li)
# - Special text (bold/italics)
# - Links
# - Images

import os
import re
import sys
import requests
from pyquery import PyQuery as pq
from io import StringIO

def get_tutorial_url(id):
    return 'http://thelegendofrandom.com/blog/archives/{0}'.format(id)

def get_tutorial_document(id):
    return pq(url=get_tutorial_url(id))

def get_tutorial(id):
    d = get_tutorial_document(id)
    tutorial = { 'url': get_tutorial_url(id) }

    # Parse title
    tutorial['title'] = d('#maincol h2.posttitle > a').text()

    # Parse meta - later

    # Parse content
    content = []
    images = []
    children = d('div.postcontent').children()
    for e in children:
        tag = e.tag
        e = pq(e)
        # Parse header
        if tag == 'h2':
            content.append({ 'type': 'header', 'text': e('span').text() })
        elif tag == 'h3':
            content.append({ 'type': 'subheader', 'text': e.text() })
        elif tag == 'ul':
            list = []
            for item in e('li').items():
                list.append(item.text())
            content.append({ 'type': 'list', 'items': list })
        # Parse paragraph
        elif tag == 'p':
            #print(len(e('a > img')))
            if e('a > img'):
                # Add both images to list if they differ
                imgurl = e('a').attr('href')
                imgsrc = e('a img').attr('src')
                images.append(imgsrc)
                if imgurl != imgsrc:
                    images.append(imgurl)

                content.append({ 'type': 'image', 'href': imgurl, 'src': imgsrc })
            else:
                e = fix_paragraph_special(fix_paragraph_urls(e))
                content.append({ 'type': 'text', 'text': e.text() })
    tutorial['content'] = content
    tutorial['images'] = images

    return tutorial

def get_markdown(tutorial):
    """ Get a markdown string from a tutorial dictionary """
    str = StringIO()

    # Write title/link
    title = tutorial['title']
    str.write('{0}\n{1}\n'.format(title, '-' * len(title)))
    str.write('\nLink: {0}'.format(tutorial['url']))

    # Write content
    content = tutorial['content']
    for c in content:
        if c['type'] == 'header' and len(c['text']) > 0:
            str.write('\n\n### {0}\n'.format(c['text']))
        if c['type'] == 'subheader' and len(c['text']) > 0:
            str.write('\n##### {0}\n'.format(c['text']))
        if c['type'] == 'list':
            str.write('\n')
            for item in c['items']:
                str.write('- {0}\n'.format(item))
        if c['type'] == 'text' and len(c['text']) > 0:
            str.write('\n{0}\n'.format(c['text']))
        if c['type'] == 'image':
            imgfile = transform_image_url(c['src'], prefix='')
            imgsrc = transform_image_url(c['src'])
            str.write('\n![{0}]({1})\n'.format(imgfile, imgsrc))
    return str.getvalue()

def get_directory_name(tutorial):
    """ Get the default directory name to save a tutorial to """
    title = re.sub('[#:]', '', tutorial['title'])
    title = re.sub('\s+', '_', title)
    return title.lower()

def transform_image_url(url, prefix='img/'):
    """ Get the filename from an original image url """
    return '{0}{1}'.format(prefix, url.split('/')[-1])

def fix_paragraph_special(p):
    for element in p('strong').items():
        e = pq(element)
        e.before('**{0}**'.format(e.text()))
        e.remove()
    for element in p('em').items():
        e = pq(element)
        e.before('*{0}*'.format(e.text()))
        e.remove()
    return p

def fix_paragraph_urls(p):
    spans = p('span')
    for element in spans.items():
        e = pq(element)
        if(e('a')):
            href = e('a').attr('href').strip()
            text = e('a span').text().strip()
            e.before('[{0}]({1})'.format(text, href))
            e.remove()
    return p

def download_file(url, filepath, verbose=True):
    """ Download a single file """
    if(verbose): print("Downloading {0} to {1}".format(url, filepath))
    r = requests.get(url)
    with open(filepath, 'wb') as file:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)
                file.flush()

def download_images(tutorial):
    """ Download all images collected from the tutorial """
    images = tutorial['images']
    dir = tutorial['directory']
    for url in images:
        filename = transform_image_url(url, prefix='')
        filepath = os.path.join(dir, 'img', filename)
        download_file(url, filepath)

def write_markdown(tutorial):
    markdown = get_markdown(tutorial)
    filepath = os.path.join(tutorial['directory'], 'README.md')
    with open(filepath, 'w') as file:
        file.write(markdown)
        file.flush()

def prepare_directory(dir):
    if os.path.exists(dir):
        if os.path.isdir(dir):
            print('Directory already exists at {0}'.format(dir))
        else:
            print('Non-directory file already exists at {0}'.format(dir))
        return False
    else:
        os.mkdir(dir)
        os.mkdir(os.path.join(dir, 'img'))
        return True

def perform(id):
    print('Downloading tutorial...')
    tutorial = get_tutorial(id)

    dirname = get_directory_name(tutorial)
    if not prepare_directory(dirname):
        return

    tutorial['directory'] = dirname

    print('Writing markdown file...')
    write_markdown(tutorial)

    print('Downloading {0} images...'.format(len(tutorial['images'])))
    download_images(tutorial)

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        resource = None

        try:
            resource = int(sys.argv[1])
        except ValueError:
            print('Invalid resource', file=sys.stderr)

        if resource is not None: perform(resource)
    else:
        print('Url or id is required', file=sys.stderr)
