import datetime
import webapp2
import sys
import os
import json
import logging
import xml.etree.cElementTree as ET

if 'lib' not in sys.path:
    sys.path[0:0] = ['lib']

import unirest

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

###############################################################################
# Global variables
###############################################################################
xmldoc = ET.parse('card-mapping.xml')
root = xmldoc.getroot()

###############################################################################
# We'll just use this convenience function to retrieve and render a template.
def render_template(handler, templatename, templatevalues={}):
  path = os.path.join(os.path.dirname(__file__), 'templates/' + templatename)
  html = template.render(path, templatevalues)
  handler.response.out.write(html)


###############################################################################
# We'll use this convenience function to retrieve the current user's email.
def get_user_email():
  result = None
  user = users.get_current_user()
  if user:
    result = user.email()
  return result

###############################################################################
class MainHandler(webapp2.RequestHandler):
    def get(self):
    	email = get_user_email()

    	page_params = {
    		'user_email': email,
     		'login_url': users.create_login_url(),
     		'logout_url': users.create_logout_url('/')
   		}

    	render_template(self, 'index.html', page_params)

###############################################################################
class DeckBuilder(webapp2.RequestHandler):
    def get(self):
    	email = get_user_email()
    	playerClass = self.request.get('class')
    	class_cards = get_class_cards(playerClass)
    	neutral_cards = get_neutral_cards()

    	page_params = {

    		'class_cards': class_cards,
    		'neutral_cards': neutral_cards,
    		'user_email': email,
    		'login_url': users.create_login_url(),
    		'logout_url': users.create_logout_url('/')
    	}
    	render_template(self, 'deckbuilder.html', page_params)

###############################################################################
# Returns an entire class' collection, with neutral cards (collectible only)
###############################################################################
def get_class_collection(player_class):
	response = unirest.get("https://omgvamp-hearthstone-v1.p.mashape.com/cards/classes/" + player_class + "?collectible=1", 
		headers={
			"X-Mashape-Key": "HFXwiln4KJmshs6B1jOMfsA75kg3p1Jj1qOjsntjBvnGaWzx1v"
		}
	)

	classCards = json.dumps(response.body, indent=1, separators=(',', ': '))

	classCardsDict = json.loads(classCards)

	removeHeroes = list()

	for x in classCardsDict:
			if x['type'] != "Hero":
				removeHeroes.append(x)

	response2 = unirest.get("https://omgvamp-hearthstone-v1.p.mashape.com/cards/types/Minion?collectible=1",
	  headers={
	    "X-Mashape-Key": "HFXwiln4KJmshs6B1jOMfsA75kg3p1Jj1qOjsntjBvnGaWzx1v"
	  }
	)

	minionCards = json.dumps(response2.body, indent=1, separators=(',', ': '))

	minionCardsDict = json.loads(minionCards)

	neutralCardsDict = list()

	for y in minionCardsDict:
			if 'playerClass' not in y:
				neutralCardsDict.append(y)

	collection = removeHeroes + neutralCardsDict

	return collection

###############################################################################
# Returns only collectible class cards for a given class
###############################################################################
def get_class_cards(player_class):
	response = unirest.get("https://omgvamp-hearthstone-v1.p.mashape.com/cards/classes/" + player_class + "?collectible=1", 
		headers={
			"X-Mashape-Key": "HFXwiln4KJmshs6B1jOMfsA75kg3p1Jj1qOjsntjBvnGaWzx1v"
		}
	)

	classCards = json.dumps(response.body, indent=1, separators=(',', ': '))

	classCardsDict = json.loads(classCards)

	removeHeroes = list()

	for x in classCardsDict:
			if x['type'] != "Hero":
				x['hheadId'] = get_hhead_id(x)
				removeHeroes.append(x)

	return removeHeroes

###############################################################################
# Returns all neutral collectible cards
###############################################################################
def get_neutral_cards():

	response2 = unirest.get("https://omgvamp-hearthstone-v1.p.mashape.com/cards/types/Minion?collectible=1",
	  headers={
	    "X-Mashape-Key": "HFXwiln4KJmshs6B1jOMfsA75kg3p1Jj1qOjsntjBvnGaWzx1v"
	  }
	)

	minionCards = json.dumps(response2.body, indent=1, separators=(',', ': '))

	minionCardsDict = json.loads(minionCards)

	neutralCardsDict = list()

	for y in minionCardsDict:
			if 'playerClass' not in y:
				y['hheadId'] = get_hhead_id(y)
				neutralCardsDict.append(y)

	return neutralCardsDict

###############################################################################
# gets the hearthhead id for a card (for the tooltip)
###############################################################################
def get_hhead_id(card):

	xpathString = ".//Card[api_id=\'" + card['cardId'] + "\']/hearthhead_id"
	result = root.find(xpathString)
	new_id = result.text
	return new_id

###############################################################################
app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/deckbuilder', DeckBuilder)
], debug=True)

