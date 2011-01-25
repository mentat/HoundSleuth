# coding=utf-8
# Copyright (c) 2010 - Jesse Lovelace - houndsleuth.com

from google.appengine.ext import db

import houndsleuth
	
class Work(db.Model):
	" A work of literature. "
	# The title of the work
	title = db.StringProperty(multiline=True)
	# The author of the work
	author = db.StringProperty()
	# The genre of the work
	genre = db.StringProperty()
	
class Scene(db.Model, houndsleuth.Searchable):
	" A scene from a work. "
	
	# Define the name of the HoundSleuth index, can be multiple indices
	# as long as they share primary key space.
	INDEX = ['shakespeare']

	# Denormed 
	work_title = db.StringProperty(multiline=True)

	# The title of the scene
	title = db.StringProperty(multiline=True)
	
	# Act number
	act_num = db.IntegerProperty()

	# Scene number
	scene_num = db.IntegerProperty()
	
	# The text of the scene, HTML
	text = db.TextProperty()

	@classmethod
	def import_transform_key(cls, doc_id, properties):
		"""
		Create a key based on the properties stored on the
		index.  The default implementation is to create 
		a key like this:
			db.Key.from_path(cls.__name__, doc_id)

		Which will be suitable for some applications.
		"""
		# In this particular case the key is weird since I'm 
		# combining the idea of a act and scene into a single
		# integer for the child key...
		return db.Key.from_path('Work', properties['work_num'], 
					  			'Scene', int('%03d%03d' % (properties['act_num'], 
														   properties['scene_num'])))
	
