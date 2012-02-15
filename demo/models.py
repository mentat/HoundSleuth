# coding=utf-8
# Copyright (c) 2010-2012 - Jesse Lovelace - houndsleuth.com

from google.appengine.ext import db

import houndsleuth as hs
import settings as s
    
class Work(db.Model):
    " A work of literature. "
    # The title of the work
    title = db.StringProperty(multiline=True)
    # The author of the work
    author = db.StringProperty()
    # The genre of the work
    genre = db.StringProperty()
    
class Scene(db.Model):
    " A scene from a work. "

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
    def _get_index(cls):
        """ Helper to return index API. """
        return hs.Index(s.HOUNDSLEUTH_INDEX, s.HOUNDSLEUTH_HOST)
        
    def index(self):
        """ Index this data with Houndsleuth. """
        fields = {
            'text': self.text,
            'work_title': self.work_title,
            'scene_title': self.title,
        }
        variables = {
            1:self.act_num,
            2:self.scene_num
        }
        Scene._get_index().add(
            str(self.key()), fields, variables=variables)

    @classmethod
    def search(cls, query, limit, offset=None, cursor=None):
        """ Execute a FTS on the index. """
        response = cls._get_index().search(query, limit, offset)
        keys = [db.Key(x['docid']) for x in response['results']]
        return db.get(keys), response