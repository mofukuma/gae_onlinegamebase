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

import k
from k.util import json2 as json
from k.util import session
from k.util import checkauth

from models import *
from myconfig import *

from webapp2_extras import security

app = k.util.WSGIApplication(
debug=WEBAPP2_DEBUG,
config=WEBAPP2_CONFIG
)

#UUIDやパスワードでログイン。初回はアカウント作成
@app.route("/<create_by:.*>/login")
class pwdlogin(webapp2.RequestHandler):
	def get(self, create_by):
		q = self.request.GET

		if create_by not in ('uuid', 'password'):
			return

		new_userid =  create_by +":"+str( q['userid'] )

		a = AccountDB.get_by_id(new_userid)
		if a: #IDの存在チェック
			if security.check_password_hash(q['password'], a.password, pepper=PASSWORD_PEPPER):
				#パスワードOK
				p = PlayerDB.get_by_id(new_userid)

				self.session = session(self.request)
				self.session.start(new_userid, {"plkey":p.key})

				#playerdb+ssid 返す
				return webapp2.Response( json.dumps( {"result":p.to_dict()}, self.session) )

			return webapp2.Response(  json.dumps( {"code":1, "message":"ログインに失敗しました。"} )  )

		passh = security.create_password_hash(q['password'], pepper=PASSWORD_PEPPER)
		a = AccountDB(id = new_userid, userid = new_userid, password = passh, create_by = create_by)
		p = PlayerDB(id = new_userid, userid = new_userid, namae=q['namae'])
		ndb.put_multi( (a, p) )

		self.session = session(self.request)
		self.session.start(new_userid, {"plkey":p.key})

		return webapp2.Response(  json.dumps( {"result":p.to_dict()}, self.session  )  )


#ログアウト
@app.route("/logout")
class pwdlogout(webapp2.RequestHandler):
	def get(self, create_by):
		self.session = session(self.request)
		self.session.delete()
		#return webapp2.Response(  json.dumps( { } )  )

#指定ユーザ情報の取得
@app.route("/getuser/<userid:.*>")
class getuser(webapp2.RequestHandler):
	def get(self, userid):
		try:
			self.session = session(self.request)
			if userid == '': #指定がなければ自分を取得
				userid = self.request.get('userid')
			p = PlayerDB.get_by_id( userid )
			self.session.save()
			return webapp2.Response(  json.dumps( {"result":p.to_dict()}, self.session  )  )

		except:
			return webapp2.Response(  json.dumps( {"code":2, "message":"ユーザが取得できません"} )  )

#フレンド申請
@app.route("/friendrequest_to/<to_userid:.*>")
class friendrequest_to(webapp2.RequestHandler):
	def get(self, to_userid):
		try:
			self.session = session(self.request)
			from_userid = self.session.userid
			#TODO validate

			from_player_key =self.session["plkey"]
			to_player_key = PlayerDB.get_by_id(to_userid).key
			f = FriendRequestDB(id=from_userid+'#'+to_userid , from_player=from_player_key, to_player=to_player_key )
			f.put()

			self.session.save()
			return webapp2.Response(  json.dumps( self.session  )  )

		except:
			return webapp2.Response(  json.dumps( {"code":3, "message":MESSAGE_ARIENAI_ERROR} )  )

#自分へのフレンドリクエストリストを取得
@app.route("/friendrequest_list")
class friendrequest_list(webapp2.RequestHandler):
	def get(self):
		#try:
			self.session = session(self.request)

			#自分へのリクエストを取得
			to_player_key = self.session["plkey"]
			#ndbになってfilterがヤな書き方になった。注意
			query = FriendRequestDB.query().filter(FriendRequestDB.to_player == to_player_key)
			dat = query.fetch(100) #100人分でいいかな

			#全員分のプレイヤーデータ取得
			from_player_list = []
			for d in dat:
				from_player_list.append(d.from_player)
			pldatalist = ndb.get_multi( from_player_list ) #リストにしてndb.get_multi使うと高速だよ！

			self.session.save()
			return webapp2.Response(  json.dumps( {"result":pldatalist}, self.session  )  )
		#except:
		#	return webapp2.Response(  json.dumps( {"code":4, "message":"フレンドリクエストリストが取得できません"} )  )

#フレンド承認／却下
@app.route("/friendrequest_yesno/<yesno:.*>/<target_userid:.*>")
class friendrequest_yesno(webapp2.RequestHandler):
	def get(self, yesno, target_userid):
		#フレンドリクエストにあるかチェック
		try:
			self.session = session(self.request)
			to_player_key = self.session["plkey"]
			from_player_key = PlayerDB.get_by_id(target_userid).key
			f_request_key = FriendRequestDB.query().filter(
				FriendRequestDB.to_player == to_player_key).filter(
				FriendRequestDB.from_player == from_player_key).get(keys_only=True)
			#YES
			if yesno == 'yes':
				f = FriendDB(id=from_player_key.string_id()+'#'+to_player_key.string_id() , from_player=from_player_key, to_player=to_player_key )
				self.tran_putdel(f, f_request_key)

			#NO
			elif yesno == 'no':
				f_request_key.delete() #リクエストけすだけ

			self.session.save()
			return webapp2.Response( json.dumps( self.session ) )
		except:
			return webapp2.Response(  json.dumps( {"code":5, "message":MESSAGE_ARIENAI_ERROR} ) )

	@ndb.transactional(retries=1, xg=True)
	def tran_putdel(self, put1, delete1key):
		put1.put()
		delete1key.delete()


#自分のフレンドリスト
@app.route("/friend_list")
class friend_list(webapp2.RequestHandler):
	def get(self):
		try:
			self.session = session(self.request)

			friend_q = FriendDB.query().filter(
				FriendDB.to_player == self.session['plkey'] )
			friend_keys = friend_q.fetch(200, keys_only=True)
			dat = ndb.get_multi(friend_keys)

			self.session.save()
			return webapp2.Response(  json.dumps( {"result": dat }, self.session ) )

		except:
			return webapp2.Response(  json.dumps( {"code":6, "message":MESSAGE_ARIENAI_ERROR} ) )

#フレンド削除
@app.route("/friend_delete/<target_userid:.*>")
class friend_delete(webapp2.RequestHandler):
	def get(self, target_userid):
		self.session = session(self.request)

		from_player_key = PlayerDB.get_by_id(target_userid).key

		f_key = FriendDB.query().filter(
			FriendDB.to_player == self.session['plkey'] ).filter(
			FriendDB.from_player == from_player_key
			).get(keys_only=True)
		f_key.delete()

		self.session.save()
		return webapp2.Response(  json.dumps( self.session ) )

#シンプルメッセージ送信
@app.route("/message_to/<target_userid:.*>")
class message_to(webapp2.RequestHandler):
	def get(self, target_userid):
		self.session = session(self.request)

		t = self.request.get('text')

		to_player_key = PlayerDB.get_by_id(target_userid).key

		msg = MessageDB(from_player=self.session['plkey'], to_player=to_player_key, text = t )

		msg.put()

		self.session.save()
		return webapp2.Response( json.dumps( self.session ) )

#メッセージリスト
@app.route("/message_list")
class message_list(webapp2.RequestHandler):
	def get(self):
		self.session = session(self.request)

		#自分が送った/自分に送られたメール
		mlist_keys = MessageDB.query().filter(
			ndb.OR( MessageDB.to_player == self.session['plkey'],
				 MessageDB.from_player == self.session['plkey'] )
			).fetch(100, keys_only=True)
		mdatas = ndb.get_multi(mlist_keys)

		#from_playerの情報も取得
		playerdata_keys = set() #重複しないように集合をつかう。
		for m in mdatas:
			playerdata_keys.add( m.from_player )
		pldatas = ndb.get_multi(playerdata_keys)

		#データの整形をしてあげる。
		pldict = {}
		for pl in pldatas:
			pldict[pl.userid] = pl

		mdataout = []
		for m in mdatas:
			mout = m.to_dict()
			#やっぱりIDだけ渡して、クライアント側でpldictを参照する
			#mout['from_player'] = pldict[m.from_player.string_id()]
			mout['from_player'] = m.from_player.string_id()
			mout['key_urlsafe'] = m.key.urlsafe()
			mdataout.append( mout )

		#新しい順にソート
		mdataout.sort( cmp=lambda x,y: cmp(x['create_date'], y['create_date']), reverse=True )

		self.session.save()
		return webapp2.Response( json.dumps( {"result":mdataout, "pldict":pldict}, self.session ) )

"""
#メッセージ削除 いらない予感・・・
@app.route("/message_delete/<key_urlsafe:.*>")
class message_delete(webapp2.RequestHandler):
	def get(self, key_urlsafe):
		self.session = session(self.request)

		k = ndb.Key(urlsafe=key_urlsafe)
		m = k.get()
		#自分へのメッセージだったら削除可能(念のため）
		if m.to_player == self.session['plkey']:
			m.key.delete()
		#この設計だと削除しちゃうと送った方も見れなくなる☆

		self.session.save()
		return webapp2.Response( json.dumps( self.session ) )
"""

#ステージデータを配信
@app.route("/game_stagestart")
class game_stagestart(webapp2.RequestHandler):
	def get(self):
		self.session = session(self.request)

		self.session.save()
		return webapp2.Response( json.dumps( self.session ) )

#ステージデータをクリア報告
@app.route("/game_stageclear")
class game_stageclear(webapp2.RequestHandler):
	def get(self):
		self.session = session(self.request)

		self.session.save()
		return webapp2.Response( json.dumps( self.session ) )

"""
@app.route("/game/action/")
class gameaction(webapp2.RequestHandler):
	def get(self):
		self.session = session(self.request)

		self.session.save()
		return webapp2.Response( json.dumps( self.session ) )
"""

@app.route("/")
class root(webapp2.RequestHandler):
	def get(self):
		return


