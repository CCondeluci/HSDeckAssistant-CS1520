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
USERINFO_KEY = ndb.Key("Entity", "UserInfo_root")

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

def check_user_has_profile():
    result = False
    userinfo = UserInfo.get_userinfo()
    if userinfo:
        result = True
    return result

def get_base_params(email):
    page_params = {
        'login_url': users.create_login_url(),
        'logout_url': users.create_logout_url('/')
    }
    if email:
        page_params['user_email'] = email
        userInfo = UserInfo.get_userinfo()
        if userInfo:
            page_params['user_pic']=userInfo.get_user_pic()
            page_params['username']=userInfo.get_username()
        else:
            page_params['username']=email
    return page_params

###############################################################################
class ViewProfileHandler(webapp2.RequestHandler):
    def get(self):
        args = self.request.get_all("user")
        if len(args) == 1:
            user = self.request.get_all("user")[0]
            userinfo = UserInfo.get_by_username(user)
            if userinfo:
                page_params = get_base_params(userinfo.email)
                page_params['username'] = userinfo.get_username()
                page_params['pic_url'] = userinfo.get_user_pic()
                render_template(self, 'profile.html', page_params)
            else:
                self.redirect('/') #should we make a 404 page?
        else:
            self.redirect('/')

###############################################################################
class AddProfileHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        user = users.get_current_user()
        if user.email():
            userInfo = UserInfo(parent=USERINFO_KEY)
            upload_files = self.get_uploads()
            if len(upload_files) > 0:
                image = upload_files[0]
                type = image.content_type

                if type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                    userInfo.pic_url = images.get_serving_url(image.key(),size=200,crop=True)
            else:
                userInfo.pic_url = '/static/assets/default_avatar.jpg'

            userInfo.email = user.email()
            userInfo.user_id = user.user_id()
            userInfo.username = self.request.get('username')
            userInfo.put()
            self.redirect('/')

class CreateProfileHandler(webapp2.RequestHandler):
    def get(self):
        email = get_user_email()
        if email == None or check_user_has_profile():
            self.redirect('/')
        else:
            page_params = get_base_params(email)
            page_params['upload_url'] =  blobstore.create_upload_url('/add_profile')
            render_template(self, 'createprofile.html', page_params)

###############################################################################
class MainHandler(webapp2.RequestHandler):
    def get(self):
        email = get_user_email()
        if email:
            if not check_user_has_profile():
                self.redirect('/createprofile')

        page_params = get_base_params(email)
        render_template(self, 'index.html', page_params)

###############################################################################
class AboutHandler(webapp2.RequestHandler):
    def get(self):
        email = get_user_email()

        page_params = get_base_params(email)

        render_template(self, 'about.html', page_params)

###############################################################################
class MyDecklistsHandler(webapp2.RequestHandler):
    def get(self):
        email = get_user_email()

        if email:
            user_decklists = get_decks_for_user(email)
            page_params = get_base_params(email)
            page_params['decklists'] = user_decklists
            render_template(self, 'mydecklists.html', page_params)
        else:
            self.redirect('/')

###############################################################################
class AllDecklistsHandler(webapp2.RequestHandler):
    def get(self):
        email = get_user_email()
        all_decklists = get_all_decks()
        page_params = get_base_params(email)
        page_params['decklists'] = all_decklists
        render_template(self, 'alldecklists.html', page_params)

###############################################################################
class DeckBuilder(webapp2.RequestHandler):
    def get(self):
        email = get_user_email()
        playerClass = self.request.get('class')
        class_cards = get_class_cards(playerClass)
        neutral_cards = get_neutral_cards()

        page_params = get_base_params(email)
        page_params['class_cards'] = class_cards
        page_params['neutral_cards'] = neutral_cards

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
            new_Decklist.write_up = decklistObj['write_up']
            new_Decklist.curve = decklistObj['curve']
            new_Decklist.put()

###############################################################################
class DeckList(ndb.Model):
    name = ndb.StringProperty()
    decklist = ndb.JsonProperty()
    time_created = ndb.DateTimeProperty(auto_now_add=True)
    email = ndb.StringProperty()
    dustcost = ndb.IntegerProperty()
    deck_class = ndb.StringProperty()
    write_up = ndb.TextProperty()
    curve = ndb.IntegerProperty(repeated=True)

###############################################################################
class UserInfo(ndb.Model):
    email = ndb.StringProperty()
    user_id = ndb.StringProperty()
    username = ndb.StringProperty()
    pic_url = ndb.StringProperty()
    @staticmethod
    def get_userinfo():
        userinfo = None
        user = users.get_current_user()
        q = UserInfo.query(ancestor=USERINFO_KEY)
        if user:
            userinfo = q.filter(UserInfo.user_id == user.user_id()).get()
        return userinfo
    @staticmethod
    def get_by_username(username):
        q = UserInfo.query(ancestor=USERINFO_KEY)
        userinfo = q.filter(UserInfo.username == username).get()
        return userinfo

    def get_user_pic(self):
        return self.pic_url

    def get_username(self):
        return self.username

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
            page_params = get_base_params(email)
            page_params['deck'] = deck
            page_params['cardlist'] = cardlist

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
                ('/alldecklists', AllDecklistsHandler),
                ('/createprofile', CreateProfileHandler),
                ('/add_profile' , AddProfileHandler),
                ('/profile', ViewProfileHandler)
], debug=True)
