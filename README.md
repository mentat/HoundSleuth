# HoundSleuth

A python/GAE friendly external fulltext service.

## Usage

### Add the HoundSleuth library to your application.

	* For python use python/houndsleuth.py

### Create indexing endpoint

	* Derive a web handler from houndsleuth.IndexHandler.
	* Make sure to define the class variables QUERY and FIELDS.

    import houndsleuth
    
    class MyIndexHandler(houndsleuth.IndexHandler):
        # The list of fields to index.
        FIELDS = (
            # Index 'title' and store it on the index.
            houndsleuth.Field(name='title', store=True),
            # Index 'text'--some text to search.
            houndsleuth.Field(name='text'),
            # Non-text properties are stored as attributes on the index.
            houndsleuth.Field(name='coolness')
        )
    
        def get_query(self, hourly=False, daily=False, weekly=False):
            """
            Return the query needed to generate the index feed.
            """
            return MyModel.all()
    
    # Also, give it a route in your WSGI app.  See example on github.
	
### Add Searchable to Model(s)

	* Use the houndsleuth.Searchable mixin for the models you have indexed.
	* Call YourModel.search("search terms") to search.

    import houndsleuth
    
    class MyModel(db.Model, houndsleuth.Searchable):
        """ Be sure to use the Searchable mixin to enable the 
        search() function.  """
        # This is setup in your HoundSleuth account online
        INDEX = ['my_index_name'] 
    
        title = db.StringProperty()
        text = db.TextProperty()
        coolness = db.IntegerProperty()


## Running the Demo

	* Pull down input data from http://hawatian.com/shakespeare.xml.gz
	* Import it with the provided bulkloader.
      * Something like: 
        * bulkloader.py --filename=shakespeare.xml --config_file=bulkloader.yaml --application=houndsleuth-demo-app --url=http://localhost:8080/_ah/remote_api --kind=Work 
        * bulkloader.py --filename=shakespeare.xml --config_file=bulkloader.yaml --application=houndsleuth-demo-app --url=http://localhost:8080/_ah/remote_api --kind=Scene
	* Use the provided API key to test that it works locally.


