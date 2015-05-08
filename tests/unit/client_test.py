
import cortipy
import httpretty
import os
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
  @patch.object(os.path, 'exists', return_value=True)
  @patch.object(cortipy.CorticalClient, '_fetchFromCache')
  @patch.object(cortipy.CorticalClient, '_writeToCache')
  def testClientRespectsOptionNotToCache_getBitmap(self, 
                                                   mockFetchFromCache, 
                                                   mockWriteToCache, 
                                                   _mockExists):
    """
    Tests that the client will not read or write the cache when useCache=False 
    for client.getBitmap().
    """
    # Arrange: mock JSON response from API, mock out the API endpoint we expect
    # to be called.
    mockResponseString = getMockApiData("terms_owl.json")
    httpretty.register_uri(httpretty.GET, "http://api.cortical.io/rest/terms",
                           body=mockResponseString,
                           content_type="application/json")
    
    # Act: create the client object we'll be testing.
    client = cortipy.CorticalClient(useCache=False)
    client.getBitmap("owl")

    # Assert:
    self.assertFalse(mockFetchFromCache.called)
    self.assertFalse(mockWriteToCache.called)


  @httpretty.activate
  @patch.object(os.path, 'exists', return_value=True)
  @patch.object(cortipy.CorticalClient, '_fetchFromCache')
  @patch.object(cortipy.CorticalClient, '_writeToCache')
  def testClientRespectsOptionNotToCache_getTextBitmap(self,
                                                       mockFetchFromCache,
                                                       mockWriteToCache,
                                                       _mockExists):
    """
    Tests that the client will not read or write the cache when useCache=False 
    for client.getTextBitmap().
    """
    # Arrange: mock JSON response from API, mock out the API endpoint we expect
    # to be called.
    mockResponseString = getMockApiData("text_androids.json")
    httpretty.register_uri(httpretty.POST, "http://api.cortical.io/rest/text",
                           body=mockResponseString,
                           content_type="application/json")
    
    # Act: create the client object we'll be testing.
    client = cortipy.CorticalClient(useCache=False)
    client.getTextBitmap("do androids dream of electric sheep")

    # Assert:
    self.assertFalse(mockFetchFromCache.called)
    self.assertFalse(mockWriteToCache.called)


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
    # Arrange: mock JSON response from API, mock out the API endpoint we expect
    # to be called.
    mockResponseString = getMockApiData("terms_owl.json")
    httpretty.register_uri(httpretty.GET, "http://api.cortical.io/rest/terms",
                           body=mockResponseString,
                           content_type="application/json")
                           
    # Act: create the client object we'll be testing.
    client = cortipy.CorticalClient(
      verbosity=0, useCache=False, retina="en_synonymous")
    bitmap = client.getBitmap("owl")

    # Assert: check the result object.
    self.assertTrue("term" in bitmap,
      "No \'term\' field in the returned object.")
    self.assertEqual(bitmap["term"], "owl",
      "The returned term is incorrect.")
    self.assertIsInstance(bitmap["fingerprint"], dict,
      "The returned object does not contain a \'fingerprint'\ dictionary.")
    self.assertTrue("positions" in bitmap["fingerprint"],
      "The returned object does not contain a \'positions\' field for the "
      "\'fingerprint\'.")
    self.assertIsInstance(bitmap["fingerprint"]["positions"], list,
      "The returned object does not contain a \'positions\' list within its "
      " \'fingerprint\' dictionary.")
    
    # Assert: get the request sent to the API and check it.
    request = httpretty.last_request()
    self.assertEqual(request.method, 'GET', "Incorrect request method.")
    self.assertEqual(request.headers['content-type'], 'application/json',
      "Incorrect request headers.")
    self.assertTrue(hasattr(request, 'querystring'),
      "The request field \'queryString\' does not exist")
    self.assertEqual(request.querystring, {"retina_name": ["en_synonymous"],
                                        "term": ["owl"],
                                        "start_index": ["0"],
                                        "max_results": ["10"],
                                        "get_fingerprint": ["True"]},
      "The request field \'queryString\' does not have the expected values.")


  @httpretty.activate
  def testGetTextBitmap(self):
    """
    Tests client.getTextBitmap(). Asserts the proper query parameters are passed
    to the API, returns a complete JSON string in response, and asserts that 
    string is converted into the expected result object for the client code.
    """
    # Arrange: mock JSON response from API, mock out the API endpoint we expect
    # to be called.
    mockResponseString = getMockApiData("text_androids.json")
    httpretty.register_uri(httpretty.POST, "http://api.cortical.io/rest/text",
                           body=mockResponseString,
                           content_type="application/json")
                           
    # Act: create the client object we'll be testing.
    client = cortipy.CorticalClient(
      verbosity=0, useCache=False, retina="en_synonymous")
    bitmap = client.getTextBitmap("do androids dream of electric sheep")

    # Assert: check the result object.
    self.assertTrue("text" in bitmap,
      "No \'text\' field in the returned object.")
    self.assertEqual(bitmap["text"], "do androids dream of electric sheep",
      "The returned term is incorrect.")
    self.assertTrue("positions" in bitmap["fingerprint"],
      "The returned object does not contain a \'positions\' field for the "
      "\'fingerprint\'.")
    self.assertIsInstance(bitmap["fingerprint"]["positions"], list,
      "The returned object does not contain a \'positions\' list within its "
      " \'fingerprint\' dictionary.")
    
    # Assert: get the request sent to the API and check it.
    request = httpretty.last_request()
    self.assertEqual(request.method, 'POST', "Incorrect request method.")
    self.assertEqual(request.headers['content-type'], 'application/json',
      "Incorrect request headers.")
    self.assertTrue(hasattr(request, 'querystring'),
      "The request field \'queryString\' does not exist")
    self.assertEqual(request.querystring, {"retina_name": ["en_synonymous"]},
      "The request field \'queryString\' does not have the expected values.")


if __name__ == '__main__':
  unittest.main()
