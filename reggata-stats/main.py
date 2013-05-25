import webapp2

from google.appengine.ext import ndb
from datetime import datetime


class Counter(ndb.Model):
	name = ndb.StringProperty(indexed=False)
	value = ndb.IntegerProperty(indexed=False)
	dateTimeCreated = ndb.DateTimeProperty(auto_now_add=True)


class MainPage(webapp2.RequestHandler):

	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write("Request: \n" + str(self.request))

		query = Counter.query()
		counters = query.fetch()

		counter = None
		if len(counters) > 0:
			counter = counters[0]
		else:
			counter = Counter()
			counter.name = "startup"
			counter.value = 0
		counter.value = counter.value + 1
		counter.put()


class Registrator(webapp2.RequestHandler):

	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'

		instanceId = str(datetime.now())
		self.response.write("Request: \n" + str(self.request))
		self.response.write("InstanceId: " + instanceId + "\n")




application = webapp2.WSGIApplication([
	('/', MainPage),
	('/register', Registrator),
], debug=True)
