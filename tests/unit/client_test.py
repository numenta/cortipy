import os

import sure
import httpretty

import cortipy

import unittest2 as unittest
from mock import patch

MOCK_API_DATA_DIR = os.path.join(
  os.path.dirname(os.path.abspath(__file__)),
  "mock-api-data"
)



def getMockApiData(name):
  with open(os.path.join(MOCK_API_DATA_DIR, name)) as dataFile:
    return dataFile.read()



class CorticalClientTestCase(unittest.TestCase):


  def testConstructionDoesNotTouchFileSystem(self):
    with patch.object(os, 'makedirs') as mock_mkdirs:
      # Construct the client.
      cortipy.CorticalClient()
    assert(mock_mkdirs.call_count == 0)



  @httpretty.activate
  @patch.object(os.path, 'exists', return_value=False)
  @patch.object(cortipy.CorticalClient, '_writeToCache')
  def testClientRespectsOptionNotToCache_getBitmap(self, mockWriteToCache, _mockExists):
    """
    Tests that the client will not read or write the cache when useCache=False 
    for client.getBitmap().
    """
    
    # Arrange.
    # --------
    # Mock JSON response from API:
    mockResponseString = getMockApiData("terms-cat.json")

    # Mock out the API endpoint we expect to be called
    httpretty.register_uri(httpretty.GET, "http://api.cortical.io/rest/terms",
                           body=mockResponseString,
                           content_type="application/json")
    # Create the clinet object we'll be testing.
    client = cortipy.CorticalClient(useCache=False)

    # Act.
    # --------
    client.getBitmap("cat")

    # Assert.
    # --------
    (mockWriteToCache.called).should.be(False)



  def testClientRespectsOptionNotToCache_getTextBitmap(self):
    """
    Tests that the client will not read or write the cache when useCache=False 
    for client.getTextBitmap().
    """
    # TODO: Implement.
    pass



  def testClientRespectsOptionNotToCache_bitmapToTerms(self):
    """
    Tests that the client will not read or write the cache when useCache=False 
    for client.bitmapToTerms().
    """
    # TODO: Implement.
    pass



  def testClientRespectsOptionNotToCache_tokenize(self):
    """
    Tests that the client will not read or write the cache when useCache=False 
    for client.tokenize().
    """
    # TODO: Implement.
    pass



  @httpretty.activate
  def testGetBitmap(self):
    """
    Tests client.getBitmap(). Asserts the proper query parameters are passed
    to the API, returns a complete JSON string in response, and asserts that 
    string is converted into the expected result object for the client code.
    """
    
    # Arrange.
    # --------
    # Mock JSON response from API:
    mockResponseString = getMockApiData("terms-cat.json")

    # Mock out the API endpoint we expect to be called
    httpretty.register_uri(httpretty.GET, "http://api.cortical.io/rest/terms",
                           body=mockResponseString,
                           content_type="application/json")
    # Create the client object we'll be testing.
    client = cortipy.CorticalClient(verbosity=0, useCache=False)

    # Act.
    # --------
    bitmap = client.getBitmap("cat")

    # Assert.
    # --------
    # Check result object.
    (bitmap).should.have.key("term").being.equal("cat")
    (bitmap).should.have.key("fingerprint").being.a("dict")
    (bitmap["fingerprint"]).should.have.key("positions").being.a("list")
    
    # Get the request sent to the API and check it.
    request = httpretty.last_request()
    (request.method).should.equal('GET')
    (request.headers['content-type']).should.equal('application/json')
    (request).should.have.property("querystring").being.equal({
        "retina_name": ["en_synonymous"],
        "term": ["cat"],
        "start_index": ["0"],
        "max_results": ["10"],
        "get_fingerprint": ["True"]
    })

