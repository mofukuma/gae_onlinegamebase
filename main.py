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
from webapp2_extras import auth
from webapp2_extras import sessions

import k.micro_webapp2
from k.models import *

app =  k.micro_webapp2.WSGIApplication(debug=True,
	config={'webapp2_extras.sessions':{
            'secret_key':'test_sskey',
            'cookie_name':'KUMA---',
            'session_max_age':3600,
            'cookie_arg':{
                'max_age':None,
                'domain':None,
                'path':'/',
                'secure':None,
                'httponly':None,
            },
            'default_backend':'memcache'
            }}
)

@app.route('/login')
def loginHandler(r):
	#Gmailのアカウント取得
	user = users.get_current_user()

	#ログインしてない
	if not user:
		login_url=users.create_login_url('/login')
		return "<A HREF='"+login_url+"'>Sign in with Google</A>"
	
	#してる
	new_userid = "GMAIL#"+str( user.user_id() )
	try:
		AccountDB.get_by_id(new_userid).key.delete()# テスト
		PlayerDB.get_by_id(new_userid).key.delete()# テスト
	except:
		pass
	if AccountDB.get_by_id(new_userid):#IDの重複チェック
		return "duplicate"
	a = AccountDB(id = new_userid, userid = new_userid, create_by = "GMAIL")
	p = PlayerDB(id = new_userid, namae=user.nickname())  #TODO 名前入力
	ndb.put_multi( (a, p) )#生成
	return a

@app.route('/adduser')
def adduserHandler(r):
	return 

@k.micro_webapp2.checkauth
class rootHandler(k.micro_webapp2.SessionHandler):
	@app.route('/')
	def get(self):
		return PlayerDB.get_by_id("GMAIL#185804764220139124118")

