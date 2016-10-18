import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmc
import sys
import os
import utils
import ConfigParser
import urllib, json
from datetime import datetime

from game import Game
from urlparse import parse_qsl

addonUrl = sys.argv[0]
addonHandle = int(sys.argv[1])
addonId = "video.lazyman.nhl.tv"
addon = xbmcaddon.Addon(id = addonId)
addonPath = addon.getAddonInfo('path')
addonName = addon.getAddonInfo('name')

iniFilePath = os.path.join(addonPath, 'resources', 'lazyman.ini')
config = ConfigParser.ConfigParser()
config.read(iniFilePath)

def games(date): return Game.fromDate(config,date)

def listyears():
  items = []
  for y in utils.years():
    listItem = xbmcgui.ListItem(label = str(y))
    listItem.setInfo( type="Video", infoLabels={ "Title": str(y) } )
    url = '{0}?action=listmonths&year={1}'.format(addonUrl,y)
    items.append((url, listItem, True))

  ok = xbmcplugin.addDirectoryItems(addonHandle, items, len(items)) 
  xbmcplugin.endOfDirectory(addonHandle)

def listmonths(year):
  items = []
  for (mn,m) in utils.months(year):
    listItem = xbmcgui.ListItem(label = mn)
    listItem.setInfo( type="Video", infoLabels={ "Title": mn } )
    url = '{0}?action=listdays&year={1}&month={2}'.format(addonUrl,year,m)
    items.append((url, listItem, True))

  ok = xbmcplugin.addDirectoryItems(addonHandle, items, len(items)) 
  xbmcplugin.endOfDirectory(addonHandle)

def listdays(year,month):
  items = []
  for d in utils.days(year,month):
    listItem = xbmcgui.ListItem(label = str(d))
    listItem.setInfo( type="Video", infoLabels={ "Title": str(d) } )
    url = '{0}?action=listgames&year={1}&month={2}&day={3}'.format(addonUrl,year,month,d)
    items.append((url, listItem, True))

  ok = xbmcplugin.addDirectoryItems(addonHandle, items, len(items)) 
  xbmcplugin.endOfDirectory(addonHandle)


def listgames(date,previous = False):
  items = []
  dategames = games(date) 
  for g in dategames: 
    label = "%s vs. %s [%s]" % (g.awayFull,g.homeFull,g.timeRemaining if g.timeRemaining != "N/A" else utils.asCurrentTz(date,g.time))
    listItem = xbmcgui.ListItem(label = label)
    listItem.setInfo( type="Video", infoLabels={ "Title": label } )
    url = '{0}?action=feeds&game={1}&date={2}'.format(addonUrl,g.id,date)
    items.append((url, listItem, True))
  if len(items) == 0:
    xbmcgui.Dialog().ok(addonName, "No games scheduled today")
    
  if previous:
    listItem = xbmcgui.ListItem(label = "Previous")
    listItem.setInfo( type="Video", infoLabels={ "Title": "Previous" } )
    url = '{0}?action=listyears'.format(addonUrl)
    items.append((url, listItem, True))
  ok = xbmcplugin.addDirectoryItems(addonHandle, items, len(items)) 
  xbmcplugin.endOfDirectory(addonHandle)
  print "Added %d games" % len(items)

def listfeeds(game,date):
  items = []
  for f in filter(lambda f: f.viewable(), game.feeds):
    label = str(f)
    listItem = xbmcgui.ListItem(label = label)
    listItem.setInfo( type="Video", infoLabels={ "Title": label } )
    url = '{0}?action=play&date={1}&feedId={2}'.format(addonUrl,date,f.mediaId)
    items.append((url, listItem, False))

  ok = xbmcplugin.addDirectoryItems(addonHandle, items, len(items)) 
  xbmcplugin.endOfDirectory(addonHandle)

def playgame(date,feedId):
  cdn = 'akc' if addon.getSetting("cdn") == "Akamai" else 'l3c'
  contentUrl = "http://mf.svc.nhl.com/m3u8/%s/%s" % (date,feedId)
  print "Content url [%s]" % (contentUrl)
  response = urllib.urlopen(contentUrl)
  playUrl = response.read().replace('l3c',cdn)
  print "play url [%s]" % (str(playUrl))
  xbmc.Player().play(playUrl + ("|Cookie=mediaAuth%%3D%%22%s%%22" % (utils.salt())))
	

def router(paramstring):
  params = dict(parse_qsl(paramstring))
  if params:
    if params['action'] == 'feeds':
      dategames = games(params['date'])
      gameDict = dict(map(lambda g: (g.id, g), dategames))
      listfeeds(gameDict[int(params['game'])], params['date'])
    elif params['action'] == 'play':
      playgame(params['date'],params['feedId'])
    elif params['action'] == 'listyears':
      listyears()
    elif params['action'] == 'listmonths':
      listmonths(params['year'])
    elif params['action'] == 'listdays':
      listdays(params['year'],params['month'])
    elif params['action'] == 'listgames':
      listgames("%d-%02d-%02d" % (int(params['year']),int(params['month']),int(params['day'])))
  else:
    listgames(utils.today().strftime("%Y-%m-%d"),True)

if __name__ == '__main__':
  router(sys.argv[2][1:])
