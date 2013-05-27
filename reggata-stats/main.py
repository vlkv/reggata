import webapp2
from google.appengine.ext import ndb
from datetime import datetime
from uuid import uuid4


class Event(ndb.Model):
	appInstanceId = ndb.StringProperty(indexed=True)
	appVersion = ndb.StringProperty(indexed=True)
	sysPlatform = ndb.StringProperty()
	name = ndb.StringProperty(indexed=True)
	dateCreated = ndb.DateTimeProperty(auto_now_add=True)


class AppInstance(ndb.Model):
	id = ndb.StringProperty(indexed=True)
	appVersion = ndb.StringProperty(indexed=True)
	sysPlatform = ndb.StringProperty()
	comment = ndb.StringProperty(default="")
	dateCreated = ndb.DateTimeProperty(auto_now_add=True)


class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write("Request: \n" + str(self.request))


class RegisterApp(webapp2.RequestHandler):
	def get(self):
		appVersion = self.request.get("app_version", None)
		if appVersion is None:
			self.response.write("app_version argument is missing")
			return
		sysPlatform = self.request.get("sys_platform", None)
		if sysPlatform is None:
			self.response.write("sys_platform argument is missing")
			return
		ai = AppInstance()
		ai.id = str(uuid4())
		ai.appVersion = appVersion
		ai.sysPlatform = sysPlatform
		ai.put()
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write(ai.id)


class PutEvent(webapp2.RequestHandler):
	def get(self):
		appInstanceId = self.request.get("app_instance_id", None)
		appVersion = self.request.get("app_version", None)
		name = self.request.get("name", None)

		self.response.headers['Content-Type'] = 'text/plain'
		if appInstanceId is None:
			self.response.write("app_instance_id argument is missing")
			return
		if appVersion is None:
			self.response.write("app_version argument is missing")
			return
		sysPlatform = self.request.get("sys_platform", None)
		if sysPlatform is None:
			self.response.write("sys_platform argument is missing")
			return
		if name is None:
			self.response.write("name argument is missing")
			return

		e = Event()
		e.appInstanceId = appInstanceId
		e.appVersion = appVersion
		e.sysPlatform = sysPlatform
		e.name = name
		e.put()
		self.response.write("ok")



application = webapp2.WSGIApplication([
	('/', MainPage),
	('/register_app', RegisterApp),
	('/put_event', PutEvent),
], debug=True)
