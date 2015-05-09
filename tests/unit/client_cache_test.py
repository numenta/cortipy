
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



if __name__ == '__main__':
  unittest.main()
