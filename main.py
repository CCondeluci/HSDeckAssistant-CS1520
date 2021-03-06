import datetime
import webapp2
import sys
import os
import json
import logging
import re
import time

if 'lib' not in sys.path:
	sys.path[0:0] = ['lib']

import unirest

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import mail
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
#convenience functions
###############################################################################
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
class ValidateUserinfoHandler(webapp2.RequestHandler):
	def get(self):
		self.post()
	def post(self):
		new_username = self.request.get('username')
		if len(new_username)>=3 and len(new_username)<=12 and not re.search(r'[^A-Za-z0-9_]', new_username): 
			q = UserInfo.query()
			if not q.filter(UserInfo.username == new_username).get():
				self.response.out.write(1)
			else:
				self.response.out.write(0)
		else:
			self.response.out.write(-1)

###############################################################################
class UpdateProfileHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		user = users.get_current_user()
		userinfo = UserInfo.get_userinfo()
		upload_files = self.get_uploads()
		if len(upload_files) > 0:
			image = upload_files[0]
			type = image.content_type

			if type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
				if userinfo.blob_key:
					blobstore.delete(userinfo.blob_key)
				userinfo.pic_url = images.get_serving_url(image.key(),size=200,crop=True)
				userinfo.blob_key = image.key()
				userinfo.put()

		else:
			userinfo.pic_url = '/static/assets/default_avatar.jpg'

		self.redirect('/')

###############################################################################
class EditProfileHandler(webapp2.RequestHandler):
	def get(self):
		args = self.request.get_all("id")
		user = users.get_current_user()
		if len(args) == 1 and user:
			edit_id = args[0]
			if edit_id == user.user_id():
				page_params = get_base_params(user.email())
				page_params['upload_url'] =  blobstore.create_upload_url('/updateprofile')
				render_template(self, 'editprofile.html', page_params)
			else:
				self.redirect('/')
		else:
			self.redirect('/')

###############################################################################
class ViewProfileHandler(webapp2.RequestHandler):
	def get(self):
		time.sleep(0.5)

		args = self.request.get_all("user")
		email = get_user_email()
		if len(args) == 1:
			view_user = args[0]
			view_userinfo = UserInfo.get_by_username(view_user)
			if view_userinfo:
				
				page_params = get_base_params(email)
				page_params['view_username'] = view_userinfo.get_username()
				page_params['view_pic_url'] = view_userinfo.get_user_pic()
				page_params['decks'] = UserInfo.get_decks_by_userinfo(view_userinfo)
				my_userinfo = UserInfo.get_userinfo()
				if my_userinfo and my_userinfo.user_id == view_userinfo.user_id:
					page_params['user_id'] = my_userinfo.user_id

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
					userInfo.blob_key = image.key()
				else:
					userInfo.pic_url = '/static/assets/default_avatar.jpg'

			else:
				userInfo.pic_url = '/static/assets/default_avatar.jpg'

			userInfo.email = user.email()
			userInfo.user_id = user.user_id()
			userInfo.username = self.request.get('username')
			userInfo.put()
			self.redirect('/')
		else:
			self.redirect('/')

###############################################################################
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
class SendFeedbackHandler(webapp2.RequestHandler):
	def post(self):
		email = get_user_email()
		if email:
			feedback = mail.EmailMessage()
			feedback.sender = email
			feedback.to = 'hsdeckassistant.webmaster@gmail.com'
			feedback.subject = 'HSDeckAssistant Feedback'
			feedback.body = self.request.get('feedback_area')
			feedback.send()

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
class AllDecklistsHandler(webapp2.RequestHandler):
	def get(self):
		email = get_user_email()
		all_decklists = get_all_decks()
		q = UserInfo.query(ancestor=USERINFO_KEY)
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
		page_params['playerClass'] = playerClass

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
			new_Decklist.username = UserInfo.query().filter(UserInfo.email == email).get().username
			new_Decklist.decklist = json.dumps(decklistObj['list'])
			new_Decklist.deck_class = decklistObj['deck_class']
			new_Decklist.write_up = decklistObj['write_up']
			new_Decklist.curve = decklistObj['curve']
			new_Decklist.put()

###############################################################################
class DeckList(ndb.Model):
	name = ndb.StringProperty()
	decklist = ndb.JsonProperty()
	time_created = ndb.DateTimeProperty(auto_now=True)
	email = ndb.StringProperty()
	username = ndb.StringProperty()
	dustcost = ndb.IntegerProperty()
	deck_class = ndb.StringProperty()
	write_up = ndb.TextProperty()
	curve = ndb.IntegerProperty(repeated=True)

	def add_like(self, user):
	  DeckLike.get_or_insert(user, parent=self.key)
	
	def remove_like(self, user):
	  deck_like = DeckLike.get_by_id(user, parent=self.key)
	  if deck_like:
		deck_like.key.delete()
	
	def count_likes(self):
	  q = DeckLike.query(ancestor=self.key)
	  return q.count()
	
	def is_liked(self, user):
	  result = False
	  if DeckLike.get_by_id(user, parent=self.key):
		result = True
	  return result
	
	def create_comment(self, user, text):
	  comment = DeckComment(parent=self.key)
	  comment.user = user
          comment.user_pic = UserInfo.get_pic_by_username(user)
	  comment.text = text
	  comment.put()
	  return comment
	
	def get_comments(self):
	  result = list()
	  q = DeckComment.query(ancestor=self.key)
	  q = q.order(-DeckComment.time_created)
	  for comment in q.fetch(1000):
                comment.user_pic = UserInfo.get_pic_by_username(comment.user)
		result.append(comment)
	  return result
	
	def count_comments(self):
	  q = DeckComment.query(ancestor=self.key)
	  return q.count()
	

###############################################################################
def get_images():
  result = list()
  q = PostedImage.query()
  q = q.order(-PostedImage.time_created)
  for img in q.fetch(100):
	img.count = img.count_votes()
	img.comment_count = img.count_comments()
	result.append(img)
  return result


###############################################################################
class UserInfo(ndb.Model):
	email = ndb.StringProperty()
	user_id = ndb.StringProperty()
	username = ndb.StringProperty()
	pic_url = ndb.StringProperty()
	blob_key = ndb.BlobKeyProperty()
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
	@staticmethod
	def get_by_email(email):
		q = UserInfo.query(ancestor=USERINFO_KEY)
		userinfo = q.filter(UserInfo.email == email)
		return userinfo
	@staticmethod
	def get_decks_by_userinfo(userinfo):
		return get_decks_for_user(userinfo.email)
        @staticmethod 
        def get_pic_by_username(username):
            q = UserInfo.query(ancestor=USERINFO_KEY)
            userinfo = q.filter(UserInfo.username == username).get()
            return userinfo.pic_url

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
		if email:
			deck.liked = deck.is_liked(email)
		deck.comments = deck.get_comments()
		deck.comment_count = len(deck.comments)
		deck.count = deck.count_likes()
		cardlist = json.loads(deck.decklist)
		if deck:
			page_params = get_base_params(email)
			page_params['deck'] = deck
			page_params['cardlist'] = cardlist

			render_template(self, 'deckcheck.html', page_params)
		else:
			self.redirect('/profile')

###############################################################################
class DeckComment(ndb.Model):
  user = ndb.StringProperty()
  user_pic = ndb.StringProperty()
  text = ndb.TextProperty()
  time_created = ndb.DateTimeProperty(auto_now_add=True)			

###############################################################################
class DeckLike(ndb.Model):
  pass

###############################################################################
class LikeHandler(webapp2.RequestHandler):
  def get(self):
	email = get_user_email()
	if email:
	  deck_id = self.request.get('id')
	  deck = get_deck(deck_id)
	  deck.add_like(email)
	self.redirect('/deckcheck?id=' + deck_id)

###############################################################################
class UnlikeHandler(webapp2.RequestHandler):
  def get(self):
	email = get_user_email()
	if email:
	  deck_id = self.request.get('id')
	  deck = get_deck(deck_id)
	  deck.remove_like(email)
	self.redirect('/deckcheck?id=' + deck_id)
 
###############################################################################
class CommentHandler(webapp2.RequestHandler):
  def post(self):
	email = get_user_email()
	if email: 
	  deck_id = self.request.get('deck-id')
	  deck = get_deck(deck_id)
	  curr_username = UserInfo.get_userinfo().get_username()
	  if deck:
		text = self.request.get('comment')
		if text != "":
			deck.create_comment(curr_username, text)
		self.redirect('/deckcheck?id=' + deck_id)
	else:
	  self.redirect('/deckcheck')

###############################################################################
class DeckEditHandler(webapp2.RequestHandler):
	def get(self):
		email = get_user_email()
		id = self.request.get('id')
		deck = get_deck(id)
		cardlist = json.loads(deck.decklist)
		playerClass = self.request.get('class')
		class_cards = get_class_cards(playerClass)
		neutral_cards = get_neutral_cards()

		if deck and (email == deck.email):
			page_params = get_base_params(email)
			page_params['class_cards'] = class_cards
			page_params['neutral_cards'] = neutral_cards
			page_params['playerClass'] = playerClass
			page_params['deck'] = deck
			page_params['cardlist'] = cardlist

			render_template(self, 'deckeditor.html', page_params)
		else:
			self.redirect('/')

###############################################################################
class SaveDeckEdit(webapp2.RequestHandler):
	def post(self):
		email = get_user_email()
		id = self.request.get('id')
		deck = get_deck(id)

		if deck and (email == deck.email):
			decklistObj = json.loads(self.request.get('inputData'))
			deck.name = decklistObj['deckname']
			deck.dustcost = decklistObj['dustcost']
			deck.email = email
			# deck.time_created = ndb.DateTimeProperty(auto_now_add=True)
			deck.username = UserInfo.query().filter(UserInfo.email == email).get().username
			deck.decklist = json.dumps(decklistObj['list'])
			deck.deck_class = decklistObj['deck_class']
			deck.write_up = decklistObj['write_up']
			deck.curve = decklistObj['curve']
			deck.put()

###############################################################################
# Returns all neutral collectible cards
###############################################################################
class SingleCheckHandler(webapp2.RequestHandler):
	def get(self):
		cname = self.request.get('card_name')
		cname = cname.replace(" ", "%20")

		# These code snippets use an open-source library.
		response = unirest.get("https://omgvamp-hearthstone-v1.p.mashape.com/cards/" + cname + "?collectible=1&locale=enUS",
		  headers={
			"X-Mashape-Key": "HFXwiln4KJmshs6B1jOMfsA75kg3p1Jj1qOjsntjBvnGaWzx1v",
			"Accept": "application/json"
		  }
		)

		resp_card = json.dumps(response.body, indent=1, separators=(',', ': '))
		self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
		self.response.out.write(resp_card)


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
				('/about', AboutHandler),
				('/savedeck', SaveDeck),
				('/deckcheck', DeckCheckHandler),
				('/alldecklists', AllDecklistsHandler),
				('/createprofile', CreateProfileHandler),
				('/add_profile' , AddProfileHandler),
				('/profile', ViewProfileHandler),
				('/editprofile', EditProfileHandler),
				('/updateprofile', UpdateProfileHandler),
				('/check_availability', ValidateUserinfoHandler),
				('/sendfeedback', SendFeedbackHandler),
				('/singlecardcheck', SingleCheckHandler),
				('/deckeditor', DeckEditHandler),
				('/savedeckedit', SaveDeckEdit),
				('/like', LikeHandler),
				('/unlike', UnlikeHandler),
				('/comment', CommentHandler)
], debug=True)
