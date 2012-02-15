# HoundSleuth

A python/GAE friendly external fulltext service.

## Changes

 * 1.0 - HoundSleuth is now API compatible with IndexTank (rip).

## Usage

### Add the HoundSleuth library to your application.

 * For python use python/houndsleuth.py

### Index your Data

    import houndsleuth
    index = houndsleuth.Index(HOUNDSLEUTH_INDEX, HOUNDSLEUTH_HOST)
    index.add('MyUniqueID', {'text': 'My text to index.'})

    # Also, give it a route in your WSGI app.  See example on github.

### Search your Data

    import houndsleuth
    index = houndsleuth.Index(HOUNDSLEUTH_INDEX, HOUNDSLEUTH_HOST)
    response = index.search('my text')

## Running your own copy of the Demo

 * Pull down input data from http://hawatian.com/shakespeare.xml.gz
 * Import it with the provided bulkloader.
   * Something like: 
     * bulkloader.py --filename=shakespeare.xml --config_file=bulkloader.yaml --application=houndsleuth-demo-app --url=http://localhost:8080/_ah/remote_api --kind=Work 
     * bulkloader.py --filename=shakespeare.xml --config_file=bulkloader.yaml --application=houndsleuth-demo-app --url=http://localhost:8080/_ah/remote_api --kind=Scene


