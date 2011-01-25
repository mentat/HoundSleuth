# HoundSleuth

A python/GAE friendly external fulltext service.

## Usage

### Add the HoundSleuth library to your application.

	* For python use python/houndsleuth.py

### Create indexing endpoint

	* Derive a web handler from houndsleuth.IndexHandler.
	* Make sure to define the class variables QUERY and FIELDS.
	
### Add Searchable to Model(s)

	* Use the houndsleuth.Searchable mixin for the models you have indexed.
	* Call YourModel.search("search terms") to search.

## Running the Demo

	* Pull down input data from http://hawatian.com/shakespeare.xml.gz
	* Import it with the provided bulkloader.
      * Something like: 
        * bulkloader.py --filename=shakespeare.xml --config_file=bulkloader.yaml --application=houndsleuth-demo-app --url=http://localhost:8080/_ah/remote_api --kind=Work 
        * bulkloader.py --filename=shakespeare.xml --config_file=bulkloader.yaml --application=houndsleuth-demo-app --url=http://localhost:8080/_ah/remote_api --kind=Scene
	* Use the provided API key to test that it works locally.


