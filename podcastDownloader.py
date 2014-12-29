#!/usr/bin/env python 

import re
import feedparser
import requests
import os
import datetime
import logging
import pushbullet
import configparser

## todo:
## add limit
## add multiple sources with renaming
## get list of devices when not given

def pushToPB( message ):
    if usePushBullet != "1" :
        return
    pb = pushbullet.PushBullet(pushBulletApi)
    success, push = pb.push_note( 'Podcast downloader', message )
    if not success:
        logging.error('[ERR] Could not push notification: ' + push.status_code)
    else:
        logging.info('Pushed notification to device')


logging.basicConfig(filename='.podRacer.log',
                    level=logging.INFO,
                    format='%(asctime)s %(message)s'
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

config = configparser.ConfigParser()
config.sections()

if not os.path.isfile('settings.conf'):
    logging.info('[INF] No config file found, creating new one')
    config['global'] = {
        'podcasts_dir': '',
        'use_pushbullet': 0
    }
    config['pushBullet'] = {
        'api_key': '',
        'device_key': ''
    }

    with open('settings.conf', 'w') as configfile:
        config.write(configfile)

config.read('settings.conf')

baseDir = config['global']['podcasts_dir']
usePushBullet = config['global']['use_pushbullet']
maxRetries = config['global']['retries']

if baseDir == "":
    print("Please add a directory for the podcasts to the config file")
    exit()

if not baseDir.endswith("/"):
   baseDir += "/"

if usePushBullet == "1":
    pushBulletApi = config['pushBullet']['api_key']
    if pushBulletApi == "":
        logging.error("Pushbullet is enabled, but no settings are given") 
	usePushBullet = 0
    pb = pushbullet.PushBullet(pushBulletApi)

d = os.path.dirname(baseDir + "This_American_Life/")
logging.info('[BEG] Starting to parse feed')

if not os.path.exists(baseDir):
    logging.info('[INF] Podcast folder not found, creating')
    os.makedirs(d)

if not os.path.exists(d):
    logging.info('[INF] Folder not found, creating')
    os.makedirs(d)

feed = feedparser.parse("http://feeds.thisamericanlife.org/talpodcast")
items = feed.entries

for i in items:
    name = re.sub(' ', '_', i.title)
    title = datetime.datetime.strptime(i.published, '%a, %d %b %Y %X +0000').strftime('%Y_%m_%d') + '_' + re.sub('[#!:]', '', name)
    file = d + '/' + title + '.mp3'
    if os.path.isfile(file):
        logging.info("[SKP] File " + file + " already exists")
        continue
    logging.info("[INF] New file found: " + title)
    remoteFile = requests.get(i.media_content[0]['url'])
    if not remoteFile.ok:
        logging.error('[ERR] Could not download file: ' + str(remoteFile.error))
        pushToPB('File could not be downloaded: ' + i.title)
        continue
    with open(file, "wb") as local_file:
        local_file.write(remoteFile.content)
    logging.info("[SUC] File successfully downloaded")
    pushToPB('New episode downloaded: ' + i.title)
logging.info('[END] Done processing feed')
exit()

