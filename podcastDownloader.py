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

def pushToPB( message, phone ):
    if usePushBullet != "1" or phone is None:
        return
    push = phone.push_note( 'Podcast downloader', message )
    if push.status_code != 200:
        logging.error('[ERR] Could not push notification: ' + push.status_code)
    else:
        logging.info('Pushed notification to device')

logging.basicConfig(filename='.talDownloader.log',
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
pushBulletApi = config['pushBullet']['api_key']
deviceId = int(config['pushBullet']['device_key'])

if baseDir == "":
    print("Please add a directory for the podcasts to the config file")
    exit()

if usePushBullet == "1":
    if pushBulletApi == "" or deviceId == "":
        logging.error("Pushbullet is enabled, but no settings are given")
        exit()
    pb = pushbullet.PushBullet(pushBulletApi)
    phone = pb.get(deviceId)
else:
    phone = None

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
        pushToPB('File could not be downloaded: ' + i.title, phone)
        continue
    with open(file, "wb") as local_file:
        local_file.write(remoteFile.content)
    logging.info("[SUC] File successfully downloaded")
    pushToPB('New episode downloaded: ' + i.title, phone)
logging.info('[END] Done processing feed')
exit()

