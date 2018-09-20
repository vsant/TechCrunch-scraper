#!/usr/bin/env python
# 
# TechCrunch Scraper
# Adapted from Craigslist/SDN scraper
# Vivek Sant <vsant@hcs.harvard.edu>
# 2011 08 11
# 

from BeautifulSoup import BeautifulSoup
import re
import urllib2
import requests
from urlparse import urljoin
import smtplib
import hashlib
import os
import email
from email.mime.multipart import MIMEMultipart
from email.MIMEImage import MIMEImage
from email.mime.text import MIMEText
from HTMLParser import HTMLParser
from settings import *

def mail(fr, to, subj, body, images_inline=0):
  msg = MIMEMultipart('alternative')
  msg['Subject'] = subj
  if images_inline:
    img_arr = list(set(re.findall('<img .*?src="(.*?)"', body)))
    for img_url in img_arr:
      img = grab_img(img_url)
      img_num = str(img_arr.index(img_url)+1)
      img.add_header('Content-ID', '<image'+img_num+'>')
      msg.attach(img)
      body = body.replace(img_url, 'cid:image' + img_num)
  msg.attach(MIMEText(body, 'html'))
  msg['From'] = fr
  msg['To'] = to

  if DEMO_MODE:
    print "************ WOULD HAVE SENT THIS *************"
    print msg.as_string(), "\n\n\n"
  else:
    s = smtplib.SMTP('localhost')
    s.sendmail(fr, to, msg.as_string())
    s.quit()

def grab_img(url):
  data = urllib2.urlopen(url).read()
  return MIMEImage(data)

def extract_post_data(entry):
  title = entry.find('a', 'post-block__title__link').getText()
  link  = entry.find('a', 'post-block__title__link').get('href')
  descr = entry.find('div', 'post-block__content').getText()
  img   = entry.find('img').get('src')
  return (title, link, descr, img)

def main():
  # Read in history
  history = map(lambda x: x.strip(), open(HISTFILE).readlines())

  email_data = ""

  for url in URLS:
    r = requests.get(url)
    soup = BeautifulSoup(r.content)

    # Read in all the posts
    for entry in soup.findAll('div', 'post-block'):
      (title, entry_url, description, img_url) = extract_post_data(entry)
      # Tag the entry
      tag = hashlib.md5(title.encode('utf-8')).hexdigest()
      if tag not in history:
        # Add to email string
        email_data += "<a href='%s' style='font-weight:bold;font-size:150%%;'>%s</a><br><span style='font-size:120%%'>%s</span><br><img src='%s'><br><br>\n\n" % (entry_url, title, description, img_url)
        # Add to history
        history.append(tag)

  # Send email if any new entries
  if email_data:
    htmlparser = HTMLParser()
    dat = htmlparser.unescape(email_data).encode('utf-8')
    mail(FROM, TO, SUBJ, dat, images_inline=1)

  # Write out new history file
  fp = open(HISTFILE, "w")
  fp.write('\n'.join(history))
  fp.close()

if __name__ == "__main__":
  main()
