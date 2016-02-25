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
import httpretty
import os
import requests
import shutil
import tempfile
import unittest2 as unittest
import warnings

from mock import Mock, patch

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


  @httpretty.activate
  @patch.object(requests.sessions.Session, "get")
  def testNotUsingCache_ApiCallsDontReadFromCache(self, mockGet):
    """
    When not using the cache, API calls do not write responses to the cache.
    """
    mockGet.__name__ = "get"
    mockGet.return_value = Mock(status_code=200,
                                content='{"dummy": "mock body"}')

    resourcePath = "/mockResourcePath"
    method = "GET"
    queryParams = {}
    postData = "mock postData"

    cacheDir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, cacheDir)

    # Act.  Make two identical calls.
    client = cortipy.CorticalClient(apiKey="fakeKey", useCache=False)
    result1 = client._queryAPI(
      method, resourcePath, queryParams, postData=postData)
    result2 = client._queryAPI(
      method, resourcePath, queryParams, postData=postData)

    # Assert.  Assert only one request made, both responses equal
    self.assertEqual(mockGet.call_count, 2)
    self.assertDictEqual(result1, result2)


  @patch.object(requests.sessions.Session, "get")
  def testUsingCache_ApiCallsReadFromCache(self, mockGet):
    """
    When using the cache, API calls that are already cached are read from the
    cache instead of making a new API call.
    """
    # Arrange.
    #mockOpen = mock_open(read_data='{"dummy": "mock body"}')

    mockGet.__name__ = "get"
    mockGet.return_value = Mock(status_code=200,
                                content='{"dummy": "mock body"}')

    resourcePath = "/mockResourcePath"
    method = "GET"
    queryParams = {}
    postData = "mock postData"

    cacheDir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, cacheDir)

    # Act.  Make two identical calls.
    client = cortipy.CorticalClient(apiKey="fakeKey",
                                    useCache=True,
                                    cacheDir=cacheDir)
    result1 = client._queryAPI(
      method, resourcePath, queryParams, postData=postData)
    result2 = client._queryAPI(
      method, resourcePath, queryParams, postData=postData)

    # Assert.  Assert only one request made, both responses equal, and only one
    # cache file created
    self.assertEqual(mockGet.call_count, 1)
    self.assertDictEqual(result1, result2)
    self.assertEqual(len(os.listdir(cacheDir)), 1,
                     "More than one cache file generated for duplicate "
                     "requests")


  @patch.object(requests.sessions.Session, "get")
  def testUsingCache_RandomEncodingsSubstituteEmptyResponses(self, mockGet):
    """
    Random encodings are returned by getBitmap() and duplicate requests
    prevented
    """
    # Arrange.
    bogusTerm = "bogus"
    mockGet.__name__ = "get"

    # Mock an empty response, regardless of bogus term
    mockGet.return_value = Mock(status_code=200, content='[]')

    cacheDir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, cacheDir)

    # Act.  Make two identical calls.
    client = cortipy.CorticalClient(apiKey="fakeKey",
                                    useCache=True,
                                    cacheDir=cacheDir)
    result1 = client.getBitmap(bogusTerm)
    result2 = client.getBitmap(bogusTerm)

    # Assert.  Assert only one request made, both responses equal, and only one
    # cache file created
    self.assertEqual(mockGet.call_count, 1)
    self.assertDictEqual(result1, result2)

    self.assertEqual(result1["fingerprint"],
                     client._placeholderFingerprint(bogusTerm))
    self.assertEqual(len(os.listdir(cacheDir)), 1,
                     "More than one cache file generated for duplicate "
                     "requests")


  @patch.object(requests.sessions.Session, "get")
  def testUsingCache_CachedRandomEncodingsAreUnique(self, mockGet):
    """
    Random encodings are returned by getBitmap() and unique for unique terms
    """
    # Arrange.
    bogusTerm = "bogus"
    mockGet.__name__ = "get"

    # Mock an empty response, regardless of bogus term
    mockGet.return_value = Mock(status_code=200, content='[]')

    cacheDir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, cacheDir)

    # Act.  Make two identical calls.
    client = cortipy.CorticalClient(apiKey="fakeKey",
                                    useCache=True,
                                    cacheDir=cacheDir)
    result1 = client.getBitmap(bogusTerm)
    result2 = client.getBitmap(bogusTerm[::-1])

    # Assert.  Assert only one request made, both responses equal, and only one
    # cache file created
    self.assertEqual(mockGet.call_count, 2)
    self.assertNotEqual(result1, result2)


  @patch.object(requests.sessions.Session, "get")
  def testUsingCache_RandomEncodingsSubstituteErrors(self, mockGet):
    """
    Random encodings are returned by getBitmap() and unique for unique terms
    """
    # Arrange.
    bogusTerm = "bogus"
    mockGet.__name__ = "get"

    # Mock a broken response which would otherwise cause json.loads() to fail,
    # regardless of bogus term
    mockGet.return_value = Mock(status_code=200, content='[')


    cacheDir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, cacheDir)

    # Act.  Make two identical calls.
    client = cortipy.CorticalClient(apiKey="fakeKey",
                                    useCache=True,
                                    cacheDir=cacheDir)

    with warnings.catch_warnings(record=True) as allWarnings:
      result1 = client.getBitmap(bogusTerm)
      result2 = client.getBitmap(bogusTerm)

    # Assert.  Assert only one request made, both responses equal, and only one
    # cache file created
    self.assertEqual(mockGet.call_count, 1)
    self.assertDictEqual(result1, result2)
    self.assertEqual(result1["fingerprint"],
                     client._placeholderFingerprint(bogusTerm))
    self.assertEqual(len(os.listdir(cacheDir)), 1,
                     "More than one cache file generated for duplicate "
                     "requests")

    for warning in allWarnings:
      if str(warning.message).startswith(
          "Suppressing error in parsing response"):
        break
    else:
      self.fail("Warning not raised as expected")



if __name__ == '__main__':
  unittest.main()
