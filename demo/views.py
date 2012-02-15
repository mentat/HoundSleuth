# coding=utf-8
# Copyright (c) 2011 - Jesse Lovelace - houndsleuth.com

import os
import logging

from google.appengine.ext import webapp 
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from urllib import quote_plus, unquote_plus

import models

import settings

from utils import paginate
    
class SearchWorksHandler(webapp.RequestHandler):
    """
    A simple handler to server the homepage and react to 
    search queries if the 'q' parameter is passed in.
    """
    PER_PAGE = 20
    
    def get(self):
        " Get either the list of works or search. "
        q = None

        if 'q' in self.request.params:
            # If 'q' in params find offset if given and search
            offset = int(self.request.params.get('offset', 0))
            # Unquote if we are continuing in a result set
            q = offset and unquote_plus(self.request.params['q']) or \
                self.request.params['q']
            logging.error(q)
            # Execute the search here
            works, info = models.Scene.search(q, 
                limit=self.PER_PAGE, offset=offset)
        else:
            # Otherwise just get the words in genre order.
            works, info = models.Work.all().order('genre').fetch(100), None
        
        path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
        self.response.out.write(template.render(path, { 
            'results':works, 
            'q':q,
            'info':info,
            'pagination': q and paginate(self, q, offset, self.PER_PAGE, info) or ''
        }))
        
class WorksHandler(webapp.RequestHandler):
    " A simple handler to return the TOC for a work."
    def get(self, work_id):
        
        work = models.Work.get_by_id(int(work_id))
        scenes = models.Scene.all().ancestor(work).order('act_num').order('scene_num')
        
        path = os.path.join(os.path.dirname(__file__), 'templates', 'work.html')
        self.response.out.write(template.render(path, {'work':work, 'scenes':scenes}))
        
class ScenesHandler(webapp.RequestHandler):
    " Gets the scene text. "
    def get(self, work_id, scene_id):
        
        key = db.Key.from_path('Work', int(work_id), 'Scene', int(scene_id))
        work, scene = db.get([key.parent(), key])
        
        path = os.path.join(os.path.dirname(__file__), 'templates', 'scene.html')
        self.response.out.write(template.render(path, {'work':work, 'scene':scene}))
        
