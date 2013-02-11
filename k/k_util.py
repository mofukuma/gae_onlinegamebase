# -*- coding: utf-8 -*-

# 便利関数群
# つかいかた
# from k_util import *

import unicodedata
import re
import urllib

import datetime
import time
from google.appengine.ext import db
from google.appengine.api import users
from django.utils import simplejson

class GaeJson(simplejson.JSONEncoder):
    def default(self, obj): 
        if hasattr(obj, '__json__'): 
            return getattr(obj, '__json__')() 
       
        if isinstance(obj, db.Query):
            return list(obj)

        if isinstance(obj, db.GqlQuery): 
            return list(obj) 
        
        elif isinstance(obj, db.Model): 
            properties = obj.properties().items() 
            output = {} 
            for field, value in properties: 
                output[field] = getattr(obj, field)
            return output 
        elif isinstance(obj, db.Key): 
            return None 
        
        # datetime は単純な文字列にする
        elif isinstance(obj, datetime): 
            #return str(obj)
            return int(time.mktime(obj.timetuple()))
        
        elif isinstance(obj, time.struct_time):
            return list(obj)

        elif isinstance(obj, users.User):
            output = {}
            methods = ['nickname', 'email', 'auth_domain']
            for method in methods:
                output[method] = getattr(obj, method)()
            return output
        
        return simplejson.JSONEncoder.default(self, obj) 

def jsondump(obj):
    return GaeJson().encode(obj)


# パラメータ部分の日本語・記号のURI変換。
def encodeURIComponent(s):
  def replace(match):
    return "%" + hex( ord( match.group() ) )[2:].upper()
  return re.sub(r"([^0-9A-Za-z!'()*\-._~])", replace, s.encode('utf-8') )

def decodeURIComponent(s):
    return urllib.unquote(s)

# 幅(半角基準)
def width_kana(str):
    all = len(str)      # 全文字数
    zenkaku = count_zen(str)        # 全角文字数
    hankaku = all - zenkaku     # 半角文字数
    
    return zenkaku * 2 + hankaku

# 全角文字数
def count_zen(str):
    n = 0
    for c in str:
        wide_chars = u"WFA"
        eaw = unicodedata.east_asian_width(c)
        if wide_chars.find(eaw) > -1:
            n += 1
    return n

import urllib, urllib2, hmac, hashlib, base64
from datetime import datetime


# Amazon 
class AmazonAPI:
    def __init__(self, access_key_id, secret_key, associate_tag=None, version='2008-08-19'):
        self.access_key_id = access_key_id
        self.secret_key = secret_key
        self.associate_tag = associate_tag
        self.version = version
        self.uri = 'webservices.amazon.co.jp'
        self.end_point = '/onca/xml'

    def lookup(self, asin, options={}):
        options['Operation'] = 'ItemLookup'
        options['ItemId'] = asin
        return self.request(options)

    def request(self, options):
        options['Service'] = 'AWSECommerceService'
        options['AWSAccessKeyId'] = self.access_key_id
        options['Version'] = self.version
        
        # Timestampをセットしないとエラーになる。
        # タイムスタンプはGMT(≒UTC)
        options['Timestamp'] = datetime.utcnow().isoformat()

        if self.associate_tag:
            options['AssociateTag'] = self.associate_tag

        # パラメーターをソートしてURLエンコード
        # (修正 2009/05/17) payload = urllib.urlencode(sorted(options.items()))
        payload = ""
        for v in sorted(options.items()):
            payload += '&%s=%s' % (v[0], urllib.quote(str(v[1])))
        payload = payload[1:]

        # 署名用の文字列
        strings = ['GET', self.uri, self.end_point, payload]

        # 署名の作成
        digest = hmac.new(self.secret_key, '\n'.join(strings), hashlib.sha256).digest()
        signature = base64.b64encode(digest)

        url = "http://%s%s?%s&Signature=%s" % (self.uri, self.end_point, payload, urllib.quote_plus(signature))
        return urllib2.urlopen(url).read()


def strcut_width(str, n):
    z = 0
    i = 0
    for c in str:
        wide_chars = u"WFA"
        eaw = unicodedata.east_asian_width(c)
        if wide_chars.find(eaw) > -1:
            z += 1
        i += 1
        if i+z > n:
            return str[:i] + u'…'
    return str

class ValidationError(Exception):
    #バリデーションエラー用の例外クラス
    def __init__(self, msg):
        Exception.__init__(self, msg)
        self.msg=msg

    def get_message(self):
        return self.msg


class BaseValidator(object):
    #バリデータ用のベースクラス
    def validate(self, value):
        return value


class NotEmpty(BaseValidator):
    errors=('この項目は必須です。',)

    def validate(self, value):
        if not value:
            raise ValidationError(self.errors[0])
        return value

class LengthCheck(BaseValidator):
    errors=('文字の長さが不正です。',)

    def __init__(self, min_val, max_val):
        self.min=min_val
        self.max=max_val

    def validate(self, value):
        nagasa = len(value)
        if nagasa < self.min or nagasa > self.max :
            raise ValidationError(self.errors[0])
        return value

class IntCheck(BaseValidator):
    errors=('この項目には数値を入力してください。',)

    def validate(self, value):
        try:
            value=int(value)
        except ValueError:
            raise ValidationError(self.errors[0])
        if int(abs(value))!=abs(value):
            raise ValidationError(self.errors[0])
        return value


class IntRangeCheck(BaseValidator):
    errors=('入力された数値が設定された範囲を超えています。',)

    def __init__(self, min_val, max_val):
        self.min=min_val
        self.max=max_val

    def validate(self, value):
        value=IntValidator().validate(value)
        if value>self.max or self.min>value:
            raise ValidationError(self.errors[0])
        return value

class RegexCheck(BaseValidator):
    #入力値が正規表現にマッチするかどうか調べるバリデータ
    errors=('使用できない文字が含まれています。',)

    def __init__(self, pat):
        self.regex_pat=re.compile(pat)

    def validate(self, value):
        if not self.regex_pat.search(value):
            raise ValidationError(self.errors[0])
        return value

class URLCheck(RegexCheck):
    errors=('正しいURLを入力してください。',)

    def __init__(self):
        self.regex_pat=re.compile(
            r'^(http|https)://[a-z0-9][a-z0-9\-\._]*\.[a-z]+'
            r'(?:[0-9]+)?(?:/.*)?$', re.I)


class EmailCheck(RegexCheck):
    errors=('正しいメールアドレスを入力してください。',)

    def __init__(self):
        self.regex_pat=re.compile(
            r'([0-9a-zA-Z_&.+-]+!)*[0-9a-zA-Z_&.+-]+@'
            r'(([0-9a-zA-Z]([0-9a-zA-Z-]*[0-9a-z-A-Z])?\.)+'
            r'[a-zA-Z]{2,6}|([0-9]{1,3}\.){3}[0-9]{1,3})$')

class Validation():
    def __init__(self, checklist):
        self.checklist = checklist

    def check(self,h, it):
        try:
            for v in self.checklist:
                v.validate(it)
        except ValidationError, e:
            return e.msg
        return None

