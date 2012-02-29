# coding=utf-8
# Copyright (c) 2011 - Jesse Lovelace - houndsleuth.com

import os
from google.appengine.dist import use_library
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
use_library('django', '1.1')
import django

remoteapi_CUSTOM_ENVIRONMENT_AUTHENTICATION = ('HTTP_X_APPENGINE_INBOUND_APPID', ['houndsleuth-hrd'])