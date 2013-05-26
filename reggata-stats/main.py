import webapp2
from google.appengine.ext import ndb
from datetime import datetime
from uuid import uuid4


class Counter(ndb.Model):
	name = ndb.StringProperty(indexed=False)
	value = ndb.IntegerProperty(indexed=False)
	dateTimeCreated = ndb.DateTimeProperty(auto_now_add=True)

class InstanceId(ndb.Model):
	uuid = ndb.StringProperty()
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
		iid = InstanceId()
		iid.uuid = str(uuid4())
		iid.put()

		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write(iid.uuid)

		#self.response.write("instance_id: " + str(self.request.get("instance_id", None)))
		#q = InstanceId.query(InstanceId.uuid == uuid)
		#ids = q.fetch()
		#if len(ids) > 0:
		#	self.response.write(" Already registered")
		#else:
		#	self.response.write(" Not registered")






application = webapp2.WSGIApplication([
	('/', MainPage),
	('/register', Registrator),
], debug=True)
