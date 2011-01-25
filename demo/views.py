# coding=utf-8
# Copyright (c) 2011 - Jesse Lovelace - houndsleuth.com

import os
import logging

from google.appengine.ext import webapp 
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from urllib import quote_plus, unquote_plus

import models
import houndsleuth
from utils import paginate

class ShakespeareIndexHandler(houndsleuth.IndexHandler):
	"""
	A web handler that derives from IndexHandler.
	"""
	# We want to index all of the scenes
	QUERY = models.Scene.all()
	# Smaller chunck size since they are large, not really needed.
	CHUNK_SIZE = 50
	# The list of fields to index.
	FIELDS = (
		# Index 'title' and store it on the index.
		houndsleuth.Field(name='title', store=True),
		# Index 'text'--the scene text
		houndsleuth.Field(name='text'),
		# Add act num as an attribute--since it's in IntergerProperty
		# this is the default.
		houndsleuth.Field(name='act_num'),
		# Add scene num as an attribute--since it's in IntergerProperty
		# this is the default.
		houndsleuth.Field(name='scene_num'),
		# Add act num as an attribute--here the source for the field
		# is a lambda function that takes the object.  We specify
		# the type to be 'IntegerProperty'.
		houndsleuth.Field(name='work_num', 
			source=lambda x: x.parent_key().id(), type_='IntegerProperty')
	)

	def export_transform_key(self, entity):
		"""
		Creates a unique integer key for this index based on
		a combination of the parent and child key's integer ids.
		The default implementation of this function simply 
		uses key().id(). 
		"""
		return int('%d%05d' % (entity.parent_key().id(), entity.key().id()))
	
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
		
