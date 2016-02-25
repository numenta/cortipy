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
import unittest2 as unittest

from cortipy.exceptions import UnsuccessfulEncodingError, RequestMethodError
from mock import Mock, patch


MOCK_API_DATA_DIR = os.path.join(
  os.path.dirname(os.path.abspath(__file__)),
  "mock-api-data"
)


def getMockApiData(name):
  with open(os.path.join(MOCK_API_DATA_DIR, name)) as dataFile:
    return dataFile.read()



class CorticalClientTestCase(unittest.TestCase):



  def testWhenConstructingClientProperDefaultPropertiesAreSet(self):
    client = cortipy.CorticalClient(apiKey="fakeKey")

    self.assertEqual(client.apiUrl, "http://api.cortical.io/rest",
      "Wrong default API URL")
    self.assertEqual(client.cacheDir, "/tmp/cortipy",
      "Wrong default cache directory")
    self.assertEqual(client.verbosity, 0,
      "Wrong default verbosity")
    self.assertEqual(client.retina, "en_synonymous",
      "Wrong default retina")
    self.assertEqual(client.useCache, True,
      "Wrong default cache on/off setting")


  @patch.object(requests.sessions.Session, "get")
  def testGetQueryToAPI(self, mockGet):
    """
    Tests the client can send a 'GET' query to the API, asserting we receive
    an HTTP status code reflecting successful operation.
    """
    # Arrange: patch the request in cortipy.CorticalClient._queryAPI().
    # with patch.object(requests.sessions.Session,
    #                   'get', return_value=) as mock_get:
    mockGet.return_value = Mock(
      content='{"dummy": "mock body"}', status_code=200)
    # Act:
    client = cortipy.CorticalClient(apiKey="fakeKey", useCache=False)
    response = client._queryAPI("GET", "/path", {})

    # Assert:
    self.assertEqual({"dummy": "mock body"}, response)


  @patch.object(requests.sessions.Session, "post")
  def testPostQueryToAPI(self, mockPost):
    """
    Tests the client can send a 'POST' query to the API, asserting we receive
    an HTTP status code reflecting successful operation.
    """
    mockPost.__name__ = "post"
    mockPost.return_value = Mock(
      content='{"dummy": "mock body"}', status_code=200)

    # Act:
    client = cortipy.CorticalClient(apiKey="fakeKey")
    response = client._queryAPI("POST", "path", {})

    # Assert:
    self.assertEqual({"dummy": "mock body"}, response)


  @patch.object(requests.sessions.Session, "post")
  def testBadQueryMethodToAPI(self, mockPost):
    """
    Tests the client sending an invalid query method to the API, asserting we
    receive a RequestMethodError.
    """
    mockPost.return_value = Mock(
      content='{"dummy": "mock body"}', status_code=None)

    # Act:
    client = cortipy.CorticalClient(apiKey="fakeKey")

    # Assert:
    with self.assertRaises(RequestMethodError):
      client._queryAPI("BAD_METHOD", "path", {})


  @patch.object(requests.sessions.Session, "get")
  def testGracefulHandlingOfAPIError(self, mockGet):
    """
    Tests the client receiving an HTTP error code from the API returns an empty
    encoding.
    """
    mockGet.__name__ = "get"
    mockGet.return_value = Mock(
      content='{"dummy": "mock body"}', status_code=400)

    # Act:
    client = cortipy.CorticalClient(apiKey="fakeKey")

    # Assert:
    result = client._queryAPI("GET", "path", {})

    self.assertEqual(result, [])


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
      apiKey="fakeKey", verbosity=0, useCache=False, retina="en_synonymous")
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
      apiKey="fakeKey", verbosity=0, useCache=False, retina="en_synonymous")
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


  @httpretty.activate
  def testCompareIdenticalFPs(self):
    """
    Tests client.Compare() for fingerprints with identical SDRs, asserting the
    method returns distances reflecting the minimum.
    """
    # Arrange: mock JSON response from API, mock out the API endpoint we expect
    # to be called, init identical FPs.
    mockResponseString = getMockApiData("compare_identicalSDRs.json")
    httpretty.register_uri(httpretty.POST,
                           "http://api.cortical.io/rest/compare",
                           body=mockResponseString,
                           content_type="application/json")
    fp1 = [0,13]
    fp2 = [0,13]

    # Act: create the client object we'll be testing.
    client = cortipy.CorticalClient(
      apiKey="fakeKey", verbosity=0, useCache=False)
    distances = client.compare(fp1, fp2)

    # Assert: expected distance metrics are returned, and result should reflect
    # minimum distances.
    self.assertTrue({"cosineSimilarity", "overlappingAll", "jaccardDistance",
                     "weightedScoring", "sizeRight", "sizeLeft",
                     "overlappingLeftRight", "euclideanDistance",
                     "overlappingRightLeft"} == set(distances),
      "The returned dictionary does not contain the expected distance metrics.")
    self.assertEqual(distances["euclideanDistance"], 0.0,
      "Euclidean distance is incorrect. Expected 0.0 but received %0.1f"
      % distances["euclideanDistance"])
    self.assertEqual(distances["overlappingAll"], 2,
      "Overlap count is incorrect. Expected 2 but received %d"
      % distances["overlappingAll"])


  @httpretty.activate
  def testCompareOrthogonalFPs(self):
    """
    Tests client.Compare() for fingerprints with orthogonal SDRs, asserting the
    method returns distances reflecting the maximum.
    """
    # Arrange: mock JSON response from API, mock out the API endpoint we expect
    # to be called, init identical FPs.
    mockResponseString = getMockApiData("compare_orthogonalSDRs.json")
    httpretty.register_uri(httpretty.POST,
                           "http://api.cortical.io/rest/compare",
                           body=mockResponseString,
                           content_type="application/json")
    fp1 = [0]
    fp2 = [13]

    # Act: create the client object we'll be testing.
    client = cortipy.CorticalClient(
      apiKey="fakeKey", verbosity=0, useCache=False)
    distances = client.compare(fp1, fp2)

    # Assert: expected distance metrics are returned, and result should reflect
    # maximum distances.
    self.assertTrue({"cosineSimilarity", "overlappingAll", "jaccardDistance",
                     "weightedScoring", "sizeRight", "sizeLeft",
                     "overlappingLeftRight", "euclideanDistance",
                     "overlappingRightLeft"} == set(distances),
      "The returned dictionary does not contain the expected distance metrics.")
    self.assertEqual(distances["euclideanDistance"], 1.0,
      "Euclidean distance is incorrect. Expected 1.0 but received %0.1f"
      % distances["euclideanDistance"])
    self.assertEqual(distances["overlappingAll"], 0,
      "Overlap count is incorrect. Expected 0 but received %d"
      % distances["overlappingAll"])


  @httpretty.activate
  def testCompareSimilarFPs(self):
    """
    Tests client.Compare() for similar SDRs, with overlapping bits, and for
    dissimilar SDRs, asserting the method returns distances reflecting the
    similar SDRs are closer than the dissimilar SDRs.
    """
    # Arrange: mock JSON response from API, mock out the API endpoint we expect
    # to be called, init identical FPs.
    mockResponseStringSimilar = getMockApiData("compare_similarSDRs.json")
    mockResponseStringDissimilar = getMockApiData("compare_dissimilarSDRs.json")
    httpretty.register_uri(httpretty.POST,
                           "http://api.cortical.io/rest/compare",
                           body=mockResponseStringSimilar,
                           content_type="application/json")
    fp1 = [0,1]
    fp2 = [1,3]
    fp3 = [10,11]

    # Act: create the client object we'll be testing.
    client = cortipy.CorticalClient(
      apiKey="fakeKey", verbosity=0, useCache=False)
    distances_similar = client.compare(fp1, fp2)

    httpretty.register_uri(httpretty.POST,
                           "http://api.cortical.io/rest/compare",
                           body=mockResponseStringDissimilar,
                           content_type="application/json")
    distances_dissimilar = client.compare(fp1, fp3)

    # Assert: result should reflect distances = 0.
    self.assertTrue((distances_similar["euclideanDistance"] <
            distances_dissimilar["euclideanDistance"]), ("Euclidean for "
            "dissimilar SDRs is incorrectly less than that of similar SDRs."))
    self.assertTrue((distances_similar["overlappingAll"] >
            distances_dissimilar["overlappingAll"]), ("Overlap for dissimilar "
            "SDRs is incorrectly less than that of similar SDRs."))


  @httpretty.activate
  def testGetContextReturnFields(self):
    """
    Tests client.getContext() for a sample term.
    Asserts the returned object contains the correct fields and have contents as
    expected.
    """
    # Arrange: mock JSON response from API, mock out the API endpoint we expect
    # to be called.
    mockResponseString = getMockApiData("context_android.json")
    httpretty.register_uri(httpretty.GET,
                           "http://api.cortical.io/rest/terms/contexts",
                           body=mockResponseString,
                           content_type="application/json")

    # Act: create the client object we'll be testing.
    client = cortipy.CorticalClient(
      apiKey="fakeKey", verbosity=0, useCache=False)
    contexts = client.getContext("android")

    # Assert: check the result object.
    self.assertTrue(isinstance(contexts, list),
      "Returned object is not of type list as expected.")
    self.assertTrue(("context_label" and "fingerprint" and "context_id")
      in contexts[0], "Data structure returned by getContext() does not contain"
      " the required fields.")
    self.assertTrue(isinstance(contexts[0]["context_label"], str),
      "The \'context_label\' field is not of type string.")
    self.assertEqual(contexts[0]["context_id"], 0,
      "The top context does not have ID of zero.")


  @httpretty.activate
  def testCreateClassification(self):
    """
    Tests client.createClassification(). Asserts the returned object has fields
    with expected values for both the classifciation name and bitmap.
    """
    # Arrange: mock JSON response from API, mock out the API endpoint we expect
    # to be called.
    mockResponseString = getMockApiData("dfw_category.json")
    httpretty.register_uri(
      httpretty.POST,
      "http://api.cortical.io/rest/classify/create_category_filter",
      body=mockResponseString,
      content_type="application/json")

    # Act: create the client object we'll be testing.
    client = cortipy.CorticalClient(
      apiKey="fakeKey", verbosity=0, useCache=False, retina="en_synonymous")
    positives = ["The truth will set you free. But not until it is finished \
      with you.", "You will become way less concerned with what other people \
      think of you when you realize how seldom they do."]
    negatives = ["It was the best of times, it was the worst of times, it was \
      the age of wisdom, it was the age of foolishness, it was the epoch of \
      belief, it was the epoch of incredulity, it was the season of Light, \
      it was the season of Darkness, it was the spring of hope, it was the \
      winter of despair, we had everything before us, we had nothing before \
      us, we were all going direct to Heaven, we were all going direct the \
      other way -- in short, the period was so far like the present period, \
      that some of its noisiest authorities insisted on its being received, \
      for good or for evil, in the superlative degree of comparison only."]
    response = client.createClassification("dfw", positives, negatives)

    # Assert: check the result object.
    self.assertTrue("positions" in response,
      "No \'positions\' field in the returned object.")
    self.assertTrue("categoryName" in response,
      "No \'categoryName\' field in the returned object.")

    self.assertEqual(response["categoryName"], "dfw",
      "The returned category name is incorrect.")
    self.assertIsInstance(response["positions"], list,
      "The returned object does not contain a \'positions\' list.")

    # Assert: get the request sent to the API and check it.
    request = httpretty.last_request()
    self.assertEqual(request.method, 'POST', "Incorrect request method.")
    self.assertEqual(request.headers['content-type'], 'application/json',
      "Incorrect request headers.")
    self.assertTrue(hasattr(request, 'querystring'),
      "The request field \'queryString\' does not exist")
    self.assertEqual(request.querystring, {"retina_name": ["en_synonymous"],
                                           "filter_name": ["dfw"]},
      "The request field \'queryString\' does not have the expected values.")


  def testGetSDRFromFingerprint(self):
    """
    Tests client.getSDR(). Asserts the correct binary string is returned for a
    sample bitmap.
    """
    # Arrange:
    fp = {"width":4,
          "height":4,
          "fingerprint":{"positions":[0,13]}
          }
    # Act:
    client = cortipy.CorticalClient(apiKey="fakeKey")
    sdr = client.getSDR(fp)

    # Assert:
    self.assertIsInstance(sdr, str, "Result is not of type string as expected.")
    self.assertEqual(sdr, '1000000000000100',
      "The resulting SDR does not match the input bitmap. Expected "
      "[1000000000000100] but instead received [%s]" % sdr)


  def testGetSDRFromNullFingerprint(self):
    """
    Tests client.getSDR(). Asserts the correct binary string is returned for an
    empty bitmap.
    """
    # Arrange:
    fp = {"width":4,
          "height":4,
          "fingerprint":{"positions":[]}
          }
    # Act:
    client = cortipy.CorticalClient(apiKey="fakeKey")
    sdr = client.getSDR(fp)

    # Assert:
    self.assertIsInstance(sdr, str, "Result is not of type string as expected.")
    self.assertEqual(sdr, '0000000000000000',
      "The resulting SDR does not match the input bitmap. Expected "
      "[0000000000000000] but instead received [%s]" % sdr)


  def testForUniquePlaceholderFingerprints(self):
    """
    Tests client._placeholderFingerprint() returns different random bitmaps for
    different input terms.
    """
    # Arrange:
    term1 = "Deckard"
    term2 = "Holden"

    # Act:
    client = cortipy.CorticalClient(apiKey="fakeKey")
    fp1 = client._placeholderFingerprint(term1, option="random")
    fp2 = client._placeholderFingerprint(term2, option="random")

    # Assert:
    self.assertNotEqual(fp1, fp2,
      "The generated bitmaps are identical, but should be different.")


  def testForIdenticalPlaceholderFingerprints(self):
    """
    Tests client._placeholderFingerprint() returns the same bitmap for when
    repeatedly called for the same input term.
    """
    # Arrange:
    term = "Rosen"

    # Act:
    client = cortipy.CorticalClient(apiKey="fakeKey")
    fp1 = client._placeholderFingerprint(term, option="random")
    fp2 = client._placeholderFingerprint(term, option="random")

    # Assert:
    self.assertEqual(fp1, fp2,
      "The generated bitmaps are different, but should be identical.")


if __name__ == '__main__':
  unittest.main()
