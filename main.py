
import webapp2
import sys
import os
import json

# inject './lib' dir in the path so that we can simply do "import ndb" or whatever there's in the app lib dir.
if 'lib' not in sys.path:
    sys.path[0:0] = ['lib']

import unirest

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('''
        	<html>
        		<body>
        			<h1>CLASS CARD LIST GENERATOR TEST</h1>
        			<br>
        			<p>Please select your class: </p>
        			<br>
        			<form action="/cardlist" method="post">
			        	<select name="class_select">
			        		<option value="Druid">Druid</option>
			        		<option value="Hunter">Hunter</option>
			        		<option value="Mage">Mage</option>
			        		<option value="Paladin">Paladin</option>
			        		<option value="Priest">Priest</option>
			        		<option value="Rogue">Rogue</option>
			        		<option value="Shaman">Shaman</option>
			        		<option value="Warlock">Warlock</option>
			        		<option value="Warrior">Warrior</option>
			        	</select>

        				<input type="submit" value="Get Card List">
        			</form>
        		</body>
        	</html>

        ''')

class CardList(webapp2.RequestHandler):
    def post(self):
		response = unirest.get("https://omgvamp-hearthstone-v1.p.mashape.com/cards/classes/" + self.request.get('class_select') + "?collectible=1", headers={"X-Mashape-Key": "HFXwiln4KJmshs6B1jOMfsA75kg3p1Jj1qOjsntjBvnGaWzx1v"})

		test = json.dumps(response.body, indent=1, separators=(',', ': '))

		testTwo = json.loads(test)

		self.response.write('<html>\n<body>\n<p>' + self.request.get('class_select') + ' Class Cards: </p>\n')

		for x in testTwo:
			if x['type'] != "Hero":
				self.response.write('<img height="400" src=' + x['img'] + '>\n')

		# These code snippets use an open-source library. http://unirest.io/python
		response2 = unirest.get("https://omgvamp-hearthstone-v1.p.mashape.com/cards/types/Minion?collectible=1",
		  headers={
		    "X-Mashape-Key": "HFXwiln4KJmshs6B1jOMfsA75kg3p1Jj1qOjsntjBvnGaWzx1v"
		  }
		)

		test2 = json.dumps(response2.body, indent=1, separators=(',', ': '))

		testTwo2 = json.loads(test2)

		self.response.write('<p>Neutral Cards: </p>\n')

		for y in testTwo2:
			if 'playerClass' not in y:
				self.response.write('<img height="400" src=' + y['img'] + '>\n')

		self.response.write('</body>\n</html>')

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/cardlist', CardList)
], debug=True)

def main():
    application.run()

if __name__ == "__main__":
    main()