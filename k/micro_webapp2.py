#!/usr/bin/env python 
# -*- coding: utf-8 -*-

import webapp2
import json
import datetime
import time

from google.appengine.ext import ndb
from webapp2_extras import auth
from webapp2_extras import sessions

#flask風のマイクロフレームワーク
class WSGIApplication(webapp2.WSGIApplication):
    def __init__(self, *args, **kwargs):
        super(WSGIApplication, self).__init__(*args, **kwargs)
        self.router.set_dispatcher(self.__class__.custom_dispatcher)

    @staticmethod
    def custom_dispatcher(router, request, response):
        rv = router.default_dispatcher(request, response)
        if isinstance(rv, basestring):
            rv = webapp2.Response(rv)
        elif isinstance(rv, tuple):
            rv = webapp2.Response(*rv)
        elif isinstance(rv, dict):
            rv = webapp2.Response(**rv)
        elif isinstance(rv, ndb.Query):
            rv = webapp2.Response( json.dumps( list(rv) ) )
        elif isinstance(rv, ndb.Model):
        	ret = rv.to_dict()
        	for k in ret:
        		if isinstance(ret[k], datetime.datetime): 
        			ret[k] = int(time.mktime(ret[k].timetuple()))
        	rv = webapp2.Response( json.dumps( ret ) )
        
        elif isinstance(rv, ndb.Key): 
            rv = webapp2.Response( rv )
        return rv

    def route(self, *args, **kwargs):
        def wrapper(func):
            self.router.add(webapp2.Route(handler=func, *args, **kwargs))
            return func

        return wrapper
        


class SessionHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()
        
        
def checkauth(handler):
    def check(self, *args, **kwargs):
        auth = self.auth
        if not auth.get_user_by_session():
            self.redirect("/login", abort=True)
        else:
            return handler(self, *args, **kwargs)
    return check