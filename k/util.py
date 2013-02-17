#!/usr/bin/env python
# -*- coding: utf-8 -*-

import webapp2
import json
import datetime
import time
import random

from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.api import memcache

from webapp2_extras import security

from myconfig import *

#flask風のURLマッピング
class WSGIApplication(webapp2.WSGIApplication):
	def __init__(self, *args, **kwargs):
		super(WSGIApplication, self).__init__(*args, **kwargs)
		#self.router.set_dispatcher(self.__class__.custom_dispatcher)

	def route(self, *args, **kwargs):
		def wrapper(func):
			self.router.add(webapp2.Route(handler=func, *args, **kwargs))
			return func
		return wrapper


class json2(json.JSONEncoder): # なんでもJSON
	def default(self, obj):
		if hasattr(obj, '__json__'):
			return getattr(obj, '__json__')()

		if isinstance(obj, db.Query):
			return list(obj)
		elif isinstance(obj, db.GqlQuery):
			return list(obj)
		elif isinstance(obj, ndb.Model):
			return obj.to_dict()
		elif isinstance(obj, db.Model):
			properties = obj.properties().items()
			output = {}
			for k in properties:
				output[k] = getattr(obj, k)
			return output
		elif isinstance(obj, ndb.Key):
			return obj.string_id()
		elif isinstance(obj, datetime.datetime):
			return int(time.mktime(obj.timetuple())) #unixtimeにして返す
		elif isinstance(obj, time.struct_time):
			return list(obj)

		return json.JSONEncoder.default(self, obj)

	@staticmethod
	def dumps(*args):
		if len(args) == 1:
			return json.dumps( args[0] , cls= json2)

		rv = {}
		for a in args:
			rv.update( a )
		return json.dumps( rv , cls= json2)

	@staticmethod
	def loads(rv):
		json.loads( rv )


def checkauth(original_func):
	def wrapper(self, *args, **keywords):
		self.session = session(self.request)
		if not self.session:
			self.redirect("/login", abort=True)
		else:
			original_func(self, *args, **keywords)
		#	return handler(self, *args, **kwargs)
	return wrapper

class session(dict):
	def __init__(self, request):
		self.ssid = request.get('ssid')
		self.userid = request.get('userid')
		if self.userid and self.ssid:
			authed = self.load(self.userid, self.ssid)
			if authed == None: #useridとssidを提示したのにダメ＝セッション切れ
				raise Exception('not logined. session was expired' ) #

		#return super(self.__class__, self).__init__(*args, **kwargs)

	def start(self, userid, data={}):
		#セッション開始
		ssid = security.create_token(entropy=128)
		self.update( data )
		self.update( {'ssid':ssid} )
		self.ssid = ssid
		memcache.add(userid, self, time=SESSION_EXPIRED_SECOUNDS, namespace='session')
		return self

	def load(self, userid, ssid):
		#セッション取得
		self.userid = userid
		ss = memcache.get(self.userid, namespace='session')
		if not ss:
			return None
		elif ss['ssid'] != ssid:
			return None
		self.ssid = ssid
		self.update( ss )
		if random.randint(0, SESSION_REGENERATE_N) == 0: #N回に一回 id再発行
			return self.regenerate_id()
		return self

	def save(self):
		#セッションを更新
		return memcache.set(self.userid, dict(self), time=SESSION_EXPIRED_SECOUNDS, namespace='session')

	def delete(self):
		#セッションを破棄
		memcache.delete(self.userid, namespace='session')

	def regenerate_id(self):
		#セッションをリジェネレート！
		memcache.delete(self.userid, namespace='session')
		self.ssid = security.create_token(entropy=128)
		self['ssid'] = self.ssid
		memcache.add(self.userid, self, time=SESSION_EXPIRED_SECOUNDS, namespace='session')
		return self

