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
  # Patching os.path.exists and os.mkdir to prevent caching logic from fetching
  # and storing to cache.
  @patch.object(os.path, 'exists', return_value=False)
  @patch.object(os, 'mkdir')
  def testGetBitmap(self, mockPathExists, mockMkdirs):
    # Arrange.
    # --------
    # Mock JSON response from API:
    mockResponseString = getMockApiData("terms-cat.json")

    # Mock out the API endpoint we expect to be called
    httpretty.register_uri(httpretty.GET, "http://api.cortical.io/rest/terms",
                           body=mockResponseString,
                           content_type="application/json")
    # Create the clinet object we'll be testing.
    client = cortipy.CorticalClient(verbosity=0)

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
    (request.path).should.equal('/rest/terms?get_fingerprint=True&term=cat&max_results=10&retina_name=en_synonymous&start_index=0')
    (request.headers['content-type']).should.equal('application/json')
    (request).should.have.property("querystring").being.equal({
        "retina_name": ["en_synonymous"],
        "term": ["cat"],
        "start_index": ["0"],
        "max_results": ["10"],
        "get_fingerprint": ["True"]
    })
