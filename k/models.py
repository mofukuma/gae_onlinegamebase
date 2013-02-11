#!-*- coding:utf-8 -*-
#!/usr/bin/env python

import webapp2
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import memcache


#------------------------
class AutoCacheModel(ndb.Model): #自動memcacheベースクラス
	def put(self):
		ndb.Model.put(self)
		if(self.is_saved()):
			memcache.delete( self.__class__.__name__+str(self.key()) )
			Debug.info( self.__class__.__name__+str(self.key()) )

	def delete(self):
		memcache.delete( self.__class__.__name__+str(self.key()) )
		ndb.Model.delete(self)
#------------------------

class AccountDB(ndb.Model):
	#key_nameはuserid
	userid          = ndb.StringProperty  (required=True) #ユーザID uidの場合"UID#"+uidとする
	create_by       = ndb.IntegerProperty (required=True, indexed=False) #何からアカウント作成した？ uid/gmail/twitter
	password        = ndb.StringProperty  (indexed=False) 

	date            = ndb.DateTimeProperty(auto_now=True, indexed=False)     #更新日時(自動）
	create_date     = ndb.DateTimeProperty(auto_now_add=True, indexed=False) #作成日時(自動）

class PlayerDB(AutoCacheModel):
	#key_nameはuserid
	namae           = ndb.StringProperty  (required=True) #日本語名
	lv              = ndb.IntegerProperty (default=1)
	exp             = ndb.IntegerProperty (default=0, indexed=False)
	#続く....

	date            = ndb.DateTimeProperty(auto_now=True, indexed=False)     #更新日時(自動）
	create_date     = ndb.DateTimeProperty(auto_now_add=True, indexed=False) #作成日時(自動）

class FriendRequestDB(ndb.Model):
	from_player   = ndb.KeyProperty(PlayerDB)
	to_player     = ndb.KeyProperty(PlayerDB)
	
	create_date   = ndb.DateTimeProperty(auto_now_add=True, indexed=False) #作成日時(自動）

class FriendDB(ndb.Model):
	from_player   = ndb.KeyProperty(PlayerDB)
	to_player     = ndb.KeyProperty(PlayerDB)
	
	create_date   = ndb.DateTimeProperty(auto_now_add=True, indexed=False) #作成日時(自動）

class MessageDB(ndb.Model):
	from_player   = ndb.KeyProperty(PlayerDB)
	to_player     = ndb.KeyProperty(PlayerDB)
	
	text          = ndb.TextProperty     (indexed=False)
	kidoku        = ndb.BooleanProperty  (indexed=False, default=False)
	
	create_date   = ndb.DateTimeProperty (auto_now_add=True, indexed=False) #作成日時(自動）



