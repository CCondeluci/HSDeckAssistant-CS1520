import datetime
import webapp2
import sys
import os
import json
import logging

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
class AboutHandler(webapp2.RequestHandler):
    def get(self):
    	email = get_user_email()

    	page_params = {
    		'user_email': email,
     		'login_url': users.create_login_url(),
     		'logout_url': users.create_logout_url('/')
   		}

    	render_template(self, 'about.html', page_params)

###############################################################################
class MyDecklistsHandler(webapp2.RequestHandler):
    def get(self):
      email = get_user_email()

      if email:
        user_decklists = get_decks_for_user(email)
        page_params = {
          'user_email': email,
          'login_url': users.create_login_url(),
          'logout_url': users.create_logout_url('/'),
          'decklists': user_decklists
        }

        render_template(self, 'mydecklists.html', page_params)
      else:
        self.redirect('/')

###############################################################################
class AllDecklistsHandler(webapp2.RequestHandler):
    def get(self):
      email = get_user_email()

      all_decklists = get_all_decks()
      page_params = {
        'user_email': email,
        'login_url': users.create_login_url(),
        'logout_url': users.create_logout_url('/'),
        'decklists': all_decklists
      }

      render_template(self, 'alldecklists.html', page_params)

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
class SaveDeck(webapp2.RequestHandler):
  def post(self):
    email = get_user_email()

    if email:
      decklistObj = json.loads(self.request.get('inputData'))
      # logging.info(decklistObj)
      new_Decklist = DeckList()
      new_Decklist.name = decklistObj['deckname']
      new_Decklist.dustcost = decklistObj['dustcost']
      new_Decklist.email = email
      new_Decklist.decklist = json.dumps(decklistObj['list'])
      new_Decklist.deck_class = decklistObj['deck_class']
      new_Decklist.put()

###############################################################################
class DeckList(ndb.Model):
  name = ndb.StringProperty()
  decklist = ndb.JsonProperty()
  time_created = ndb.DateTimeProperty(auto_now_add=True)
  email = ndb.StringProperty()
  dustcost = ndb.IntegerProperty()
  deck_class = ndb.StringProperty()

###############################################################################
def get_decks_for_user(email):
  result = list()
  q = DeckList.query(DeckList.email == email)
  q = q.order(-DeckList.time_created)
  for deck in q.fetch(1000):
    result.append(deck)
  return result

###############################################################################
def get_all_decks():
  result = list()
  q = DeckList.query()
  q = q.order(-DeckList.time_created)
  for deck in q.fetch(1000):
    result.append(deck)
  return result

###############################################################################
def get_deck(deck_id):
  return ndb.Key(urlsafe=deck_id).get()

###############################################################################
class DeckCheckHandler(webapp2.RequestHandler):
  def get(self):
    id = self.request.get('id')
    deck = get_deck(id)
    email = get_user_email()
    cardlist = json.loads(deck.decklist)
    if deck:
      page_params = {
        'user_email': email,
        'login_url': users.create_login_url(),
        'logout_url': users.create_logout_url('/'),
        'deck': deck,
        'cardlist': cardlist
      }
      render_template(self, 'deckcheck.html', page_params)
    else:
      self.redirect('/mydecklists')

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
				neutralCardsDict.append(y)

	return neutralCardsDict

###############################################################################
app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/deckbuilder', DeckBuilder),
    ('/mydecklists', MyDecklistsHandler),
    ('/about', AboutHandler),
    ('/savedeck', SaveDeck),
    ('/deckcheck', DeckCheckHandler),
    ('/alldecklists', AllDecklistsHandler)
], debug=True)

