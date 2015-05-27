# The MIT License (MIT)
#
# Copyright (c) 2015 Numenta, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import cortipy
import hashlib
import httpretty
import os
import unittest2 as unittest

from mock import patch, mock_open

try:
  import simplejson as json
except ImportError:
  import json


MOCK_API_DATA_DIR = os.path.join(
  os.path.dirname(os.path.abspath(__file__)),
  "mock-api-data"
)


def getMockApiData(name):
  with open(os.path.join(MOCK_API_DATA_DIR, name)) as dataFile:
    return dataFile.read()



class CorticalClientTestCase(unittest.TestCase):


  @patch.object(os, 'makedirs')
  def testConstructionDoesNotTouchFileSystem(self, mockMkdirs):
    cortipy.CorticalClient(apiKey="fakeKey")
    assert(mockMkdirs.call_count == 0)


  @httpretty.activate
  @patch.object(os.path, 'exists', return_value=False)
  @patch.object(os, 'makedirs')
  def testUsingCache_CacheDirIsLazilyCreated(self,
                                                  mockMkDirs, 
                                                  _mockPathExists):
    """
    When using cache, a cache directory is created on the first call to query 
    the API if it does not exist.
    """
    # Arrange.
    mockOpen = mock_open()
    httpretty.register_uri(httpretty.GET,
                           "http://api.cortical.io/rest/mockResourcePath",
                           body='{"dummy":"mock body"}',
                           status=200,
                           content_type="application/json")
    resourcePath = "/mockResourcePath"
    method = "GET"
    queryParams = "mock queryParams"
    postData = "mock postData"

    # Patching file open
    with patch('__builtin__.open', mockOpen, create=True):
      # Act.
      client = cortipy.CorticalClient(apiKey="fakeKey", useCache=True)
      client._queryAPI(method, resourcePath, queryParams, postData=postData)

    # Assert.
    mockMkDirs.assert_called_once_with("/tmp/cortipy")


  @httpretty.activate
  @patch.object(os.path, 'exists', return_value=False)
  @patch.object(os, 'makedirs')
  def testNotUsingCache_CacheDirIsNotCreated(self,
                                                  mockMkDirs, 
                                                  _mockPathExists):
    """
    When using not using the cache, a cache directory is not created when
    querying the API.
    """
    # Arrange.
    mockOpen = mock_open()
    httpretty.register_uri(httpretty.GET,
                           "http://api.cortical.io/rest/mockResourcePath",
                           body='{"dummy":"mock body"}',
                           status=200,
                           content_type="application/json")
    resourcePath = "/mockResourcePath"
    method = "GET"
    queryParams = "mock queryParams"
    postData = "mock postData"
  
    # Patching file open
    with patch('__builtin__.open', mockOpen, create=False):
      # Act.
      client = cortipy.CorticalClient(apiKey="fakeKey", useCache=False)
      client._queryAPI(method, resourcePath, queryParams, postData=postData)
  
    # Assert.
    assert(mockMkDirs.call_count == 0)
  
  
  @httpretty.activate
  @patch.object(os.path, 'exists', return_value=False)
  def testUsingCache_ApiGetCallsWriteToCache(self, mockPathExists):
    """
    When using the cache, GET API response is written to the cache directory in
    a new JSON file, using a cache key created by the hashed request string.
    """
    # Arrange.
    mockOpen = mock_open()
    httpretty.register_uri(httpretty.GET,
                           "http://api.cortical.io/rest/mockResourcePath",
                           body='{"dummy":"mock body"}',
                           status=200,
                           content_type="application/json")
    resourcePath = "/mockResourcePath"
    method = "GET"
    queryParams = '{"get_fingerprint": true, \
                    "retina_name": "en_synonymous", \
                    "max_results": 10, \
                    "term": "cat", \
                    "start_index": 0}'
    postData = None
    
    # os.path.exists() will be called twice. First to see if the cache path to
    # the resource being fetched exists (we'll return False), and the 2nd time
    # after the API call to decide whether to lazily create the cache directory.
    # To this call we'll return True so it doesn't try to create it.
    def existsSideEffect(arg):
      if arg == "/tmp/cortipy":
        return True
  
    mockPathExists.side_effect = existsSideEffect 
    # Patching file open
    with patch('__builtin__.open', mockOpen, create=True):
      # Act.
      client = cortipy.CorticalClient(apiKey="fakeKey", useCache=True)
      client._queryAPI(method, resourcePath, queryParams, postData=postData)
    expectedCacheString = hashlib.sha224(json.dumps([
      resourcePath, method, json.dumps(queryParams), postData
    ])).hexdigest()
    expectedCachePath = "/tmp/cortipy/" + expectedCacheString + ".json"
    
    # Assert.
    mockOpen.assert_called_once_with(expectedCachePath, "w")
    handle = mockOpen()
    handle.write.assert_called_once_with('{"dummy": "mock body"}')
  

  @httpretty.activate
  @patch.object(os.path, 'exists', return_value=False)
  def testUsingCache_ApiPostCallsWriteToCache(self, mockPathExists):
    """
    When using the cache, POST API response is written to the cache directory in
    a new JSON file, using a cache key created by the hashed request string.
    """
    # Arrange.
    mockOpen = mock_open()
    httpretty.register_uri(httpretty.POST,
                           "http://api.cortical.io/rest/mockResourcePath",
                           body='{"dummy":"mock body"}',
                           status=200,
                           content_type="application/json")
    resourcePath = "/mockResourcePath"
    method = "POST"
    queryParams = '{"get_fingerprint": true, \
                    "retina_name": "en_synonymous", \
                    "max_results": 10, \
                    "term": "cat", \
                    "start_index": 0}'
    postData = "dummy post data"
    
    # os.path.exists() will be called twice. First to see if the cache path to
    # the resource being fetched exists (we'll return False), and the 2nd time
    # after the API call to decide whether to lazily create the cache directory.
    # To this call we'll return True so it doesn't try to create it.
    def existsSideEffect(arg):
      if arg == "/tmp/cortipy":
        return True
  
    mockPathExists.side_effect = existsSideEffect 
    # Patching file open
    with patch('__builtin__.open', mockOpen, create=True):
      # Act.
      client = cortipy.CorticalClient(apiKey="fakeKey", useCache=True)
      client._queryAPI(method, resourcePath, queryParams, postData=postData)
    
    expectedCacheString = hashlib.sha224(json.dumps([
      resourcePath, method, json.dumps(queryParams), postData
    ])).hexdigest()
    expectedCachePath = "/tmp/cortipy/" + expectedCacheString + ".json"
    
    # Assert.
    mockOpen.assert_called_once_with(expectedCachePath, "w")
    handle = mockOpen()
    handle.write.assert_called_once_with('{"dummy": "mock body"}')
  

  @httpretty.activate
  @patch.object(os.path, 'exists', return_value=False)
  def testNotUsingCache_ApiCallsDontWriteToCache(self, mockExists):
    """
    When not using the cache, API calls do not write responses to the cache.
    """
    # Arrange.
    mockOpen = mock_open()
    httpretty.register_uri(httpretty.GET,
                           "http://api.cortical.io/rest/mockResourcePath",
                           body='{"dummy":"mock body"}',
                           status=200,
                           content_type="application/json")
    resourcePath = "/mockResourcePath"
    method = "GET"
    queryParams = "mock queryParams"
    postData = "mock postData"
  
    # Patching file open
    with patch('__builtin__.open', mockOpen, create=True):
      # Act.
      client = cortipy.CorticalClient(apiKey="fakeKey", useCache=False)
      client._queryAPI(method, resourcePath, queryParams, postData=postData)
    
    # Assert.
    self.assertEqual(0, mockOpen.call_count,
      "Caching was attempted when useCache=False.")
  
  
  @patch.object(os.path, 'exists', return_value=True)
  def testUsingCache_ApiCallsReadFromCache(self, _mockExists):
    """
    When using the cache, API calls that are already cached are read from the 
    cache instead of making a new API call.
    """
    # Arrange.
    mockOpen = mock_open(read_data='{"dummy": "mock body"}')
  
    resourcePath = "/mockResourcePath"
    method = "GET"
    queryParams = "mock queryParams"
    postData = "mock postData"
  
    # Patching file open
    with patch('__builtin__.open', mockOpen, create=True):
      # Act.
      client = cortipy.CorticalClient(apiKey="fakeKey", useCache=True)
      result = client._queryAPI(
        method, resourcePath, queryParams, postData=postData)
    
    expectedCacheString = hashlib.sha224(json.dumps([
      resourcePath, method, json.dumps(queryParams), postData
      ])).hexdigest()
    expectedCachePath = "/tmp/cortipy/" + expectedCacheString + ".json"
    
    # Assert.
    mockOpen.assert_called_once_with(expectedCachePath, "r")
    self.assertEqual({"dummy": "mock body"}, result)
  
  
  @httpretty.activate
  @patch.object(os.path, 'exists', return_value=False)
  def testNotUsingCache_ApiCallsDontReadFromCache(self, _mockExists):
    """
    When not using the cache, API calls that are already cached are not read 
    from the cache instead.
    """
    # Arrange.
    mockOpen = mock_open()
    httpretty.register_uri(httpretty.GET,
                           "http://api.cortical.io/rest/mockResourcePath",
                           body='{"dummy":"mock body"}',
                           status=200,
                           content_type="application/json")
    resourcePath = "/mockResourcePath"
    method = "GET"
    queryParams = "mock queryParams"
    postData = "mock postData"
  
    client = cortipy.CorticalClient(apiKey="fakeKey", useCache=False)
    client._queryAPI(method, resourcePath, queryParams, postData=postData)
  
    # Assert.
    self.assertEqual(0, mockOpen.call_count,
      "Caching was attempted when useCache=False.")


if __name__ == '__main__':
  unittest.main()
