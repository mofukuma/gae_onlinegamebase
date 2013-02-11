#!-*- coding:utf-8 -*-
#!/usr/bin/env python

import sys

#日本語処理おまじない-------------
stdin = sys.stdin
stdout = sys.stdout
reload(sys)
sys.setdefaultencoding('utf-8')
sys.stdin = stdin
sys.stdout = stdout
#---------------------------------

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import memcache

import webapp2
import k.micro_webapp2

from k.models import *

app =  k.micro_webapp2.WSGIApplication(debug=True)

@app.route('/login')
def loginHandler(r):
	#Gmailのアカウント取得
	user = users.get_current_user()

	#ログインしてない
	if not user:
		login_url=users.create_login_url('/login')
		return "<A HREF='"+login_url+"'>Googleでログイン</A>"
	
	#してる
	new_userid = "GMAIL#"+str( user.user_id() )
	if AccountDB.get(new_userid):
	p = AccountDB()
	p.populate(
	 userid = "GMAIL#"+str( user.user_id() )
	)
	p.put()
	return p

@app.route('/adduser')
def adduserHandler(r):
	return 

@app.route('/')
def rootHandler(r):
	
	return "hello"
