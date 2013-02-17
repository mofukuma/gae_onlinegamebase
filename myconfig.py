#!/usr/bin/env python
# -*- coding: utf-8 -*-

PASSWORD_PEPPER = 'KUMARRRR-TEST'

SESSION_REGENERATE_N = 200000
SESSION_EXPIRED_SECOUNDS = 60*60 #60min.

WEBAPP2_DEBUG = True
WEBAPP2_CONFIG= {}

MESSAGE_ARIENAI_ERROR = "予期せぬエラーが発生しました"

"""
WEBAPP2_CONFIG={'webapp2_extras.sessions':{
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
"""