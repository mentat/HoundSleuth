# coding=utf-8
# Copyright (c) 2011 - Jesse Lovelace - houndsleuth.com

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import views

application = webapp.WSGIApplication([
	(r'/demo/fulltext/$', views.ShakespeareIndexHandler),
	(r'/demo/$', views.SearchWorksHandler),
	(r'/$', views.SearchWorksHandler),
	(r'/demo/works/([0-9]+)$', views.WorksHandler),
	(r'/demo/works/([0-9]+)/scenes/([0-9]+)$', views.ScenesHandler)
], debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
    main()
