# coding=utf-8
# Copyright (c) 2010-2011 - Jesse Lovelace - houndsleuth.com
#
# HoundSleuth index handler and search mixin for Python.
# @version 0.9.1
#

import os
import logging
import urllib
import time
import hmac
import hashlib
import copy

from xml.etree import ElementTree as et
from google.appengine.ext import webapp 
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch import DownloadError

from django.utils import simplejson

import settings

def CDATA(text=None):
	element = et.Element(CDATA)
	element.text = text
	return element

old_ElementTree = et.ElementTree

class ElementTreeCDATA(et.ElementTree):
	def _write(self, file, node, encoding, namespaces):
		if node.tag is CDATA:
			text = node.text.encode(encoding)
			file.write("\n<![CDATA[%s]]>\n" % text.strip())
		else:
			old_ElementTree._write(self, file, node, encoding, namespaces)

et.ElementTree = ElementTreeCDATA

class Field(object):
	"""
	A field in a full-text index.
	
	StringProperty, TextProperty, & StringListProperty are always 
	considered full-text indexed fields.
	IntegerProperty and FloatProperty are considered attribute fields.
	
	 * store - Store this value on the index.  Useful for small strings in case
	    you want to skip datastore access.
	 * to_ord - Convert string to ordinal value.
	 * bits - Number of bits to store integer/float in.
	 * source - The field or callable to draw the value from.  Default is the 
	    same as name.
	 * type_ - The type of the field.  Usually not needed except in the case
	    of using a callable for source.
	 * kill - Use this value as a kill attribute.  If the resulting value
	    is True the record will be removed from the index.
	"""
	def __init__(self, name, store=False, to_ord=False, bits=32, 
				 source=None, type_=None, kill=False):
		self.name = name
		self.store = store
		self.to_order = to_ord
		self.bits = bits
		self.source = source
		self.type_ = type_
		self.kill = kill

class IndexHandler(webapp.RequestHandler):
	"""
	Base class for a fulltext indexing feed.  To define your own feed
	subclass this handler and override the class variables. See the sample
	views.py for a possible implementation.

	The HoundSleuth index needs a unique integer key.  Override the 
	method "export_transform_key(self, entity) in the derived class
	to transform your model key if needed.  The default implementation
	should be sufficient for entities that are not children in an 
	entity group.
	"""

	# The number of records to pull at a time, if your entities are 
	# very large you might scale this back some.
	CHUNK_SIZE = 200

	# A tuple of Field objects that define which properties of the
	# resulting query objects to add to the index.
	FIELDS = None
	
	# This would be your per-index key used to generate a signature to protect
	# your indexing URL.
	INDEX_KEY=None
	
	def get_query(self, hourly=False, daily=False, weekly=False):
		"""
		Return the query needed to generate the index feed.
		If your app/query supports it, the hourly, daily, and weekly
		flags can be used.
		"""
		raise NotImplementedError

	def export_transform_key(self, entity):
		"""
		Transform the entity's key for use in the index.  The index requires
		unique integer keys for indexed documents.
		"""
		return entity.key().id()
	
	def render_header(self):
		" Render index header. "
		
		self.response.out.write('<?xml version="1.0" encoding="utf-8"?>\n')
		self.response.out.write('<sphinx:docset>\n')
		
		props = self.get_query()._model_class.properties()
		
		tree = et.Element('sphinx:schema')
		for field in self.FIELDS:
			if field.kill:
				continue
			if field.source:
				if callable(field.source):
					if field.type_ is None:
						logging.warn("Cannot determine field type of callable, you must define the field with 'type_' argument: %s" % field.name)
						continue
					type_ = field.type_
				else:
					type_ = props[field.source].__class__.__name__
			else:
				type_ = props[field.name].__class__.__name__

			attrs = dict(name=field.name)
			
			if type_ in ['StringProperty','TextProperty', 'StringListProperty', 'EmailProperty']:	
				if field.store:
					attrs['attr'] = u'string'
				tree.append(et.Element('sphinx:field', attrs))
			elif type_ == 'IntegerProperty':
				attrs['bits'] = str(field.bits)
				attrs['type'] = 'int'
				tree.append(et.Element('sphinx:attr', attrs))
			elif type_ == 'FloatProperty':
				attrs['bits'] = str(field.bits)
				attrs['type'] = 'float'
				tree.append(et.Element('sphinx:attr', attrs))
			else:
				raise RuntimeError("%s is not a valid field type for full-text indexing." % type_)
				
		self.response.out.write(et.tostring(tree, encoding='utf-8'))
		
	def render_batch(self, batch):
		" Render a batch of entities to XML. "
		props = self.get_query()._model_class.properties()
		kills = []
		
		for item in batch:
			el = et.Element('sphinx:document', { 'id':str(self.export_transform_key(item))})
			killed = False
			for field in self.FIELDS:
				if field.kill and getattr(item, field.name):
					# Kill the record
					kills.append(self.export_transform_key(item))
					killed = True
					break
					
				elem = et.Element(field.name)
				data = None

				if field.source:
					# If the field points to a source, call it or get it from the entity
					if callable(field.source):
						data = unicode(field.source(item))
					elif hasattr(item, field.source):
						data = unicode(getattr(item, field.source))
					else:
						logging.warn("Could not determine field source: %s: %s" % (
							field.name, field.source))
						continue
				else:	
					type_ = props[field.name].__class__.__name__
					data = unicode(getattr(item, field.name))

				if type_ == 'StringListProperty':
					data = u' '.join(data)
				
				elem.append(CDATA(data))
				el.append(elem)
			if not killed:
				self.response.out.write(et.tostring(el, encoding='utf-8'))
				
		if kills:
			el = et.Element('sphinx:killist')
			for kill in kills:
				sub = et.SubElement(el, 'id')
				sub.text=str(kill)
			self.response.out.write(et.tostring(el, encoding='utf-8'))
		
	def get(self):
		" Get data in chunks. "
		
		# If we defined a key on this handler, use it to validate
		# request from indexer.
		if self.INDEX_KEY and not self.check_signature():
			self.response.set_status(403)
			logging.warn("A request was made with an invalid or missing signature.")
			return self.response.out.write("Invalid signature.")
		
		self.response.headers['Content-Type'] = 'application/xml'
		
		if self.request.GET.get('header'):
			return self.render_header()
			
		if self.request.GET.get('footer'):
			return self.response.out.write('</sphinx:docset>')
			
		last_key_str = self.request.GET.get('last')
		chunk = int(self.request.GET.get('chunk', self.CHUNK_SIZE))
		
		query = self.get_query()
	
		if last_key_str:
			query.with_cursor(last_key_str)
		
		objs = query.fetch(chunk)
			
		if len(objs) == chunk:
			self.response.headers['X-HS-Key'] = str(query.cursor())
		else:
			logging.debug("Ending with len: %d" % len(objs))
	
		self.response.headers['X-HS-Length'] = len(objs)
		self.render_batch(objs)
		
	def check_signature(self):
		" Ensure the data signature is correct if supplied. "
		
		key = self.INDEX_KEY
		
		if not key:
			logging.warn("No key found on request handler.")
			return True
			
		if not 'sig' in self.request.params:
			logging.debug("No signature in request parameters.")
			return False
			
		candidate_sig = self.request.params['sig']
		
		sig = ''.join(['%s%s' % (x, self.request.params[x]) \
			for x in sorted(self.request.params.iterkeys()) if x != 'sig'])

		sig = hmac.new(key, 
					   msg=sig, 
					   digestmod=hashlib.sha256
					).digest().encode('base64').strip()
		return candidate_sig == sig
		
class SearchInfo(object):
	"""
	Extra information returned with the search results.
	"""
	def __init__(self, total, totalfound, sphinxtime, searchtime = None):
		self.total = total
		self.totalfound = totalfound
		self.searchtime = searchtime
		self.sphinxtime = sphinxtime

POST_THRESHOLD = 200

class Searchable(object):
	""" 
	A mix-in for model classes to implement search. 
	
	Add a INDEX class variable to derived classes that contains
	a list of the indices you want to search.
	
	Add a APP class variable to derived classes that contains
	the application to search in, or add a global default in a
	settings model called HOUNDSLEUTH_DEFAULT_APP.
	"""

	@classmethod
	def max_relevance(cls, q, weights):
		" An estimate of PROXIMITY_BM25 max relevance. "
		return len(q.split(' ')) * sum ( weights ) * 1000 + 999

	@classmethod
	def import_transform_key(cls, doc_id, properties):
		"""
		Transform the document ID into a usable GAE key.  Must return a 
		db.Key.  The default implementation creates a key for the query class.

		Derive this method to properly recreate a complex key, such as one
		that has a parent or string key_name.
		"""
		return db.Key.from_path(cls.__name__, doc_id)
	
	@classmethod
	def search(cls, phrase, limit=10, offset=None, keys_only=False,
			   filters=None, order=None, mode=None, app=None,
			   indices=None, weights=None):
		"""
		Makes a request to the HoundSleuth to perform a search.
		
		Arguments:
		 * phrase - the fulltext string to search for, can be complex expression.
		 * limit - the number of results to fetch.
		 * offset - the offset to start fetching from.
		 * keys_only - only return keys, do not get objects from datastore.
		 * filters - filter search by attribute values.
		 * order - order results by attribute or complex value (ie: "attr_name,@relevance").
		 * mode - matching mode for search, default is 'extended2', options are:
		   * all
		   * any
		   * boolean
		   * extended
		   * extended2
		   * phrase
		  * indices - which indices to search.
		  * weights - per-field weighting values.

		Notes:
		 - filters is a string with syntax like:
		   name:val[,val2,...]
		   name:val|name2:val2,val3|name3:val4
		"""
		
		headers, resp = {}, None
		
		stopwatch = time.time()
		
		if indices is None:
			if hasattr(cls, 'INDEX'):
				indices = getattr(cls, 'INDEX')
			elif hasattr(settings, 'HOUNDSLEUTH_DEFAULT_INDEX'):
				indices = getattr(settings, 'HOUNDSLEUTH_DEFAULT_INDEX')

		if indices is None:
			logging.warn("Cannot complete search without an index defined.")
			return [], SearchInfo(0,0,0.0)
			
		if app is None:
			if hasattr(cls, 'APP'):
				app = getattr(cls, 'APP')
			elif hasattr(settings, 'HOUNDSLEUTH_DEFAULT_APP'):
				app = getattr(settings, 'HOUNDSLEUTH_DEFAULT_APP')
			else:
				raise RuntimeError("You must define an application to search in.")
		
		params = {
			'q': phrase,
			'l': limit,
			'a': app,
			'o': offset if offset else 0,
			'f': filters if filters else '',
			'm': mode if mode else '',
			's': order if order else '',
			'i': ','.join(indices),
			'w': ','.join(map(str, weights)) if weights else '',
			'k': settings.HOUNDSLEUTH_API_KEY
		}
			
		logging.debug('Search params: %s' % params)

		# Prepare the params for transmission
		payload = urllib.urlencode(params)
		
		def do_request():
			# Do an HTTP GET if the params are short enough
			if len(payload) <= POST_THRESHOLD:
				url = u'%s/search/?%s' % (settings.HOUNDSLEUTH_HOST, payload)
				logging.debug('Searching via GET: %s' % url)
				return urlfetch.fetch(url, headers=headers).content

			else:
				# Do an HTTP POST otherwise (e.g., if we're given an enormously long
				# filter)
				logging.debug('Searching via POST')
			
				return urlfetch.fetch(
					url=settings.HOUNDSLEUTH_HOST,
					payload=payload,
					headers=headers,
					method=urlfetch.POST).content
		
		for x in range(3):
			try:
				resp = do_request()
			except DownloadError, msg:
				logging.warn(msg)
			else:
				break
				
		if resp is None:
			raise RuntimeError("Cannot contact HoundSleuth. See logs for details.")
			
		# Try to parse the response into JSON
		results = simplejson.loads(resp)
		
		hs_time = time.time() - stopwatch
		logging.debug("Round trip time for HoundSleuth: %f" % hs_time)

		if not 'results' in results:
			return [], SearchInfo(0,0,0.0, hs_time)

		info = SearchInfo(results['total'],
						  results['total_found'],
						  results['time'], 
						  hs_time)

		# Build a list of item keys based on the IDs in the response
		keys = [ cls.import_transform_key(r['doc_id'], r) for r in results['results']]

		if keys_only:
			return keys, info
		
		# Get the items from the datastore, filtering out any empty values
		items = db.get(keys)
	
		max_weight = cls.max_relevance(phrase, weights and weights or [1])

		for item, data in zip(items, results['results']):
			if item:
				setattr(item, 'weight', data['weight'])

		return filter(None, items), info
