# coding=utf-8
# Copyright (c) 2010-2012 - Jesse Lovelace - houndsleuth.com
#
# HoundSleuth python library.
# @version 1.0.0
#
import logging
import urllib
import httplib
import base64

try:
    import json
except ImportError:
    import simplejson as json

import settings

VERSION = '0.1'
USER_AGENT = 'Houndslueth-Python/%s' % VERSION

class IndexError(Exception):
    pass

class Index(object):
    
    def __init__(self, index_name, host, appid = None, api_key = None, ):
        self.index_name = index_name
        self.key = api_key
        self.host = host.replace('http://','')
        self.appid = appid
        
        if '@' in host:
            self.key, self.host = host.split('@')
            self.user, self.key = self.key.split(':')
        
    def add(self, docid, fields, categories=None, variables=None):
        """
        Add a document to the index. 
        
         * docid - a unique identifier for this document.
         * fields - a dictionary mapping of fields to values, the default
           indexed field is "text":
           { "text": "Great document for searching", "author":"Jesse" }
         * categories - a dictionary mapping of category names to values.
           { "color": "red", "genre": "horror" }
         * variables - a dictionary mapping of variable ids to ints/floats.
           { 1: 0.5, 2: 1.222, 3: 500 }
        """
        data = {
            'docid':docid
        }
        data['fields'] = fields
        if categories:
            data['categories'] = categories
        if variables:
            data['variables'] = variables

        self._request('/v1/indexes/%s/docs' % self.index_name, 'PUT', data, True)
        
        
    def search(self, query, limit=10, offset=None, fields=None, category_filters=None, cursor=None,
               function=None):
        """
        Do a fulltext search.
        """
        return self._request('/v1/indexes/%s/search' % self.index_name, 'GET', {
            'q':query, 
            'start': offset and offset or 0, 
            'len':limit,
            'fetch':fields and (u','.join(fields)).encode('utf-8') or '',
            'function':function and function or 0,
            'cursor':cursor and cursor or ''
        }, False)
        
    def _request(self, path, method, data, json_body=False):
        """ Do an HTTP request. """
        
        headers = {'User-Agent':USER_AGENT}
        if self.key:
            headers['Authorization'] = base64.b64encode("%s:%s" % (self.user, self.key)).strip()
        
        if '%s' in self.host and self.appid:
            host = self.host % self.appid

        if self.appid and json_body:
            path = '%s?appid=%s' % (path, self.appid)
        elif self.appid:
            data['appid'] = self.appid

        if json_body:
            data = json.dumps(data)
            headers['Content-Type'] = 'application/json'
        else:
            data = urllib.urlencode(data)
            if method=='GET':
                path = '%s?%s' % (path, data)
                data = None

        conn = httplib.HTTPConnection(self.host)
        conn.request(method, path, data, headers)
        try:
            resp = conn.getresponse()
        except Exception:
            logging.error("Problem contacting host: %s" % self.host)
            raise IndexError("Cannot contact HoundSleuth.")

        raw_data = resp.read()
        
        try:
            data = json.loads(raw_data)
        except:
            data = { 'message': raw_data }
            
        if resp.status > 299:
            raise IndexError(raw_data)
            
        return data

if __name__ == '__main__':
    import sys
    
    host, index, infile = sys.argv
    
    dex = Index(index, host=host)
    
    data = json.loads(open(infile, 'r').read())
    
    for x in data:
        dex.add(x['docid'], x['fields'], x.get('categories'), x.get('variables'))
        