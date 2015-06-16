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

import hashlib
import os
import random
import requests

from cortipy.exceptions import UnsuccessfulEncodingError, RequestMethodError
from functools import wraps

try:
  import simplejson as json
except ImportError:
  import json


DEFAULT_BASE_URL = "http://api.cortical.io/rest"
DEFAULT_RETINA = "en_synonymous"
DEFAULT_CACHE_DIR = "/tmp/cortipy"
DEFAULT_VERBOSITY = 0
DEFAULT_FILL_SDR = "random"

# A retina is the Cortical.io word space model:
# http://documentation.cortical.io/retinas.html#the-retinas
RETINA_SIZES = {
      "en_synonymous": {
        "width": 128,
        "height": 128
      },
      "en_associative": {
        "width": 128,
        "height": 128
      }
    }

TERM_SPARSITY = 0.01


def cacheDecorator(func):
  """
  Created to wrap the CorticalClient's _queryAPI() method. If the client's
  cache is enabled, will try to load API responses from the local cache before
  going to the API. Then before returning control to the calling function, will
  cache the API responses into the local file system.
  """
  @wraps(func)
  def cacheWrapper(*args, **kwargs):
    client = args[0]
    cacheDir = client.cacheDir
    method = args[1]
    resourcePath = args[2]
    queryParams = args[3]
    postData = ""
    if "postData" in kwargs:
      postData = kwargs["postData"]
    requestString = json.dumps([
      resourcePath, method, json.dumps(queryParams), postData
    ])
    cacheKey = hashlib.sha224(requestString).hexdigest()
    cachePath = os.path.join(cacheDir, cacheKey + ".json")

    if client.useCache and os.path.exists(cachePath):
      if client.verbosity > 0:
        print "Fetching API data from the cache at %s" % cachePath
        print "\tRequest string: %s" % requestString
      return json.loads(open(cachePath, "r").read())

    else:
      # Wrapped function gets executed here.
      result = func(*args, **kwargs)

      if client.useCache:
        # Lazily create cache directory.
        if not os.path.exists(client.cacheDir):
          if client.verbosity > 0:
            print "Creating cache at %s" % client.cacheDir
          os.makedirs(client.cacheDir)
        if client.verbosity > 0:
          print "Writing API response to the cache at %s" % cachePath
          print "\t%s" % result
        with open(cachePath, "w") as f:
          f.write(json.dumps(result))

      return result

  return cacheWrapper



class CorticalClient():
  """
  Main class for making calls to the Cortical.io REST API. The function calls
  here are derived from the Cortical.io Python SDK.
  """

  def __init__(self,
               apiKey=None,
               baseUrl=DEFAULT_BASE_URL,
               retina=DEFAULT_RETINA,
               cacheDir=DEFAULT_CACHE_DIR,
               useCache=True,
               verbosity=DEFAULT_VERBOSITY):
    # Instantiate API credentials.
    if apiKey:
      self.apiKey = apiKey
    else:
      self.apiKey = os.environ["CORTICAL_API_KEY"]
    self.apiUrl = baseUrl
    self.cacheDir = cacheDir
    self.verbosity = verbosity
    self.retina = retina
    self.useCache = useCache


  @cacheDecorator
  def _queryAPI(self, method, resourcePath, queryParams,
                postData=None, headers=None):
    url = self.apiUrl + resourcePath
    if headers is None:
      headers = {}
    headers['api-key'] = self.apiKey
    response = None

    if self.verbosity > 0:
      print "\tCalling API: %s %s" % (method, url)
      print "\tHeaders:\n\t%s" % json.dumps(headers)
      print "\tQuery params:\n\t%s" % json.dumps(queryParams)
      if method == "POST":
        print "\tPost data: \n\t%s" % postData

    if method == 'GET':
      response = requests.get(url, params=queryParams, headers=headers)
    elif method == 'POST':
      response = requests.post(
        url, params=queryParams, headers=headers, data=postData)
    else:
      raise RequestMethodError("Method " + method + " is not recognized.")
    if response.status_code != 200:
      raise UnsuccessfulEncodingError(
        "Response " + str(response.status_code) + ": " + response.content)
    if self.verbosity > 1:
      print "API Response content:"
      print response.content
    try:
      responseObj = json.loads(response.content)
    except ValueError("Could not decode the query response."):
      responseObj = []
    return responseObj


  def _placeholderFingerprint(self, text, option=random):
    """
    When the API returns a null fingerprint, fill with a random or empty bitmap.

    We seed the random number generator such that a given string will yield the
    same fingerprint each time this function is called.
    """
    if option == "random":
      size = RETINA_SIZES[self.retina]
      total = int(float(size["width"]) * float(size["height"]))
      random.seed(text)
      bitmap = random.sample(xrange(total), int(total*TERM_SPARSITY))
      return {"positions":sorted(bitmap)}
    else:
      return {"positions":[]}


  def getBitmap(self, term):
    """
    For the input term, return the fingerprint info; either from cache or the
    REST API.

    @param  term       (string)     A single token.
    @return fpInfo     (dict)       Dictionary object with fields to describe
                                    the returned fingerprint:
                                      - 'term'
                                      - 'sparsity' of the bitmap (%)
                                      - 'df': the fraction of documents in the
                                        corpus for which this term appears
                                      - 'height' and 'width' dimensions
                                      - 'fingerprint' bitmap given by the
                                        'positions' of ON bits
                                      - 'pos_types': list of parts of speech
    """
    # Is term actually multiple tokens?
    if " " in term:
      raise ValueError("The input term '%s' is multiple tokens. Perhaps you "
        "did not yet tokenize the input, or you should call getTextBitmap()."
        % term)

    responseObj = self._queryAPI("GET",
                                 "/terms",
                                 {
                                   "retina_name": self.retina,
                                   "term": term,
                                   "start_index": 0,
                                   "max_results": 10,
                                   "get_fingerprint": True
                                 },
                                 headers={
                                   "Accept": "Application/json",
                                   "Content-Type": "application/json"
                                 })

    if isinstance(responseObj, list) and len(responseObj)>0:
      fpInfo = responseObj[0]
    else:
      print "no FP for ", term
      fpInfo = {}
      if self.verbosity > 0:
        print ("\tAPI could not return info for the text \'%s\'. Perhaps the "
              "text includes punctuation that should be ignored by the "
              "tokenizer.\n\tGenerating a placeholder fingerprint for \'%s\'..."
              % (term, term))
      fpInfo["score"] = None
      fpInfo["pos_types"] = None
      fpInfo["term"] = term
      fpInfo["fingerprint"] = self._placeholderFingerprint(
        term, DEFAULT_FILL_SDR)

    # Include values for SDR dimensions and sparsity.
    if (not "width" in fpInfo) or (not "height" in fpInfo):
      size = RETINA_SIZES[self.retina]
      fpInfo["width"] = size["width"]
      fpInfo["height"] = size["height"]
    total = float(fpInfo["width"]) * float(fpInfo["height"])
    on = len(fpInfo["fingerprint"]["positions"])
    sparsity = round((on / total) * 100)
    fpInfo["sparsity"] = sparsity

    return fpInfo


  def getTextBitmap(self, text):
    """
    For the input string of text, return the fingerprint info; either from
    cache or the REST API.

    @param  term       (string)     Non-tokenized text.
    @return fpInfo     (dict)       Dictionary object with fields to describe
                                    the returned fingerprint:
                                      - 'text'
                                      - 'sparsity' of the bitmap (%)
                                      - 'df': the fraction of documents in the
                                        corpus for which this term appears
                                      - 'height' and 'width' dimensions
                                      - 'fingerprint' bitmap given by the
                                        'positions' of ON bits
                                      - 'pos_types': list of parts of speech
    """
    responseObj = self._queryAPI("POST",
                                 "/text",
                                 {
                                   "retina_name": self.retina
                                 },
                                 postData=text,
                                 headers={
                                   "Accept": "Application/json",
                                   "Content-Type": "application/json"
                                 })

    if isinstance(responseObj, list) and len(responseObj)>0:
      fpInfo = responseObj[0]
    else:
      fpInfo = {}
      if self.verbosity > 0:
        print ("API could not return info for the text \'%s\'. Perhaps the "
              "text includes punctuation that should be ignored by the "
              "tokenizer.\nGenerating a placeholder fingerprint for \'%s\'..."
              % (text, text))
      fpInfo["positions"] = self._placeholderFingerprint(
        text, DEFAULT_FILL_SDR)

    # Include values for SDR dimensions and sparsity.
    if (not "width" in fpInfo) or (not "height" in fpInfo):
      size = RETINA_SIZES[self.retina]
      fpInfo["width"] = size["width"]
      fpInfo["height"] = size["height"]
    total = float(fpInfo["width"]) * float(fpInfo["height"])
    on = len(fpInfo["positions"])
    sparsity = round((on / total) * 100)
    fpInfo["sparsity"] = sparsity
    fpInfo["text"] = text
    fpInfo["fingerprint"] = {}
    fpInfo["fingerprint"]["positions"] = fpInfo["positions"]
    del fpInfo["positions"]

    return fpInfo


  def bitmapToTerms(self, onBits, numTerms=10):
    """
    For the given bitmap, returns the most likely terms for which it encodes.

    @param  onBits          (list)             Bitmap for a fingerprint.
    @param  numTerms        (int)              The max number of terms to
                                               return.
    @return similar         (list)             List of dictionaries, where keys
                                               are terms and likelihood scores.
    Optional query params:
      - 'pos_type': what part of speech (e.g. 'NOUN') to return
      - 'context_id': id returned by getContext, specifying the context of the
        returned terms
    """
    if len(onBits) is 0:
      raise Exception("Cannot convert empty bitmap to term!")

    # Each list of similar terms has a unique cache location:
    dumpedData = json.dumps({"positions": onBits})
    if self.verbosity > 0:
      print "\tfetching similar terms from REST API"

    responseObj = self._queryAPI("POST",
                                  "/expressions/similar_terms",
                                  {
                                    "retina_name":self.retina,
                                    "start_index":0,
                                    "max_results":numTerms,
                                    "get_fingerprint":False,
                                    "pos_type":None,
                                    "sparsity":TERM_SPARSITY,
                                    "context_id":None
                                  },
                                  postData=dumpedData,
                                  headers={
                                    "Accept": "Application/json",
                                    "Content-Type": "application/json"
                                  })
    # Return terms in human-readable format
    similar = []
    for term in responseObj:
      similar.append(
        {"term": term["term"], "score": term["score"]}
      )
    return similar


  def tokenize(self, text):
    """Get a list of sentence tokens from a text string. Non-alphanumeric and
    end-of-sentence characters are exlcuded. Only returns terms found in the
    corpus.

    @param text     (str)               Text string to tokenize
    @return         (list)              List where each entry contains the
                                        string tokens from a sentence in the
                                        input text

    Example:
      >>> c = cortipy.CorticalClient(apiKey)
      >>> c.tokenize("This is Deckard. How much is an electric ostrich?")
      ['this,is,deckard', 'how,much,is,an,electric,ostrich']

    Optional query params:
      - 'POStags': tokenizer will only return the specified parts of speech
    """
    responseObj = self._queryAPI("POST",
                                "/text/tokenize",
                                {
                                  "retina_name":self.retina,
                                  "POStags":None
                                },
                                postData=text,
                                headers={
                                  "Accept": "Application/json",
                                  "Content-Type": "application/json"
                                })

    return responseObj


  # NOTE: slice() does not yet work properly; Cortical.io is working on it
  # def slice(self, text):
  #   """
  #   Slice the text into meaningful sections; over a sequence of SDRs in a text,
  #   slices at significant changes in the meaning.

  #   Optional query params:
  #   - 'get_fingerprint': boolean, if the fingerprint should be returned with
  #   the results
  #   """
  #   response = self._queryAPI("POST",
  #                             "/text/slices",
  #                             {
  #                               "retina_name":self.retina,
  #                               "start_index":0,
  #                               "max_results":10,
  #                               "get_fingerprint":False
  #                             },
  #                             postData=text,
  #                             headers={
  #                               "Accept": "Application/json",
  #                               "Content-Type": "application/json"
  #                             })
  #   import pdb; pdb.set_trace()  ## TODO: investigate returns slices as expected
  #   return json.loads(response.content)


  def compare(self, bitmap1, bitmap2):
    """
    Given two bitmaps, return their comparison for several distance metrics.
    Bitmaps that to be compared can be returned from getBitmap(),
    getTextBitmap(), and createClassification().

    @params bitmap          (list)      Bitmap to compare.
    @return                 (dict)      Dictionary of the API's comparison
                                        metrics.

    Example return dict:
      {
        "cosineSimilarity": 0.6666666666666666,
        "euclideanDistance": 0.3333333333333333,
        "jaccardDistance": 0.5,
        "overlappingAll": 6,
        "overlappingLeftRight": 0.6666666666666666,
        "overlappingRightLeft": 0.6666666666666666,
        "sizeLeft": 9,
        "sizeRight": 9,
        "weightedScoring": 0.4436476984102028
      }
    """
    dumpedData = json.dumps([
                              {"positions":bitmap1},
                              {"positions":bitmap2}
                            ])
    responseObj = self._queryAPI("POST",
                                "/compare",
                                {"retina_name":self.retina},
                                postData=dumpedData,
                                headers={
                                  "Accept": "Application/json",
                                  "Content-Type": "application/json"
                                })

    return responseObj


  def getContext(self, term):
    """
    Get contexts for a given term. The context ids can be used as parameters in
    bitmapToTerms().

    @return     (list)        A list of dictionaries, where the keys are
                              'context_label', 'fingerprint' (the bitmap for the
                              context label), and 'context_id'.
    """
    responseObj = self._queryAPI("GET",
                                "/terms/contexts",
                                {
                                  "retina_name":self.retina,
                                  "term":term,
                                  "start_index":0,
                                  "max_results":10,
                                  "get_fingerprint":False,
                                },
                                headers={
                                  "Accept": "Application/json",
                                  "Content-Type": "application/json"
                                })

    return responseObj


  def createClassification(self, category, positives, negatives=[]):
    """
    Create a 'category filter' fingerprint with positive (and negative) examples
    that would fit (or not fit) into the category.

    @param positives      (list)        Positive example strings; fit into this
                                        category.
    @param negatives      (list)        Negative example strings; specifically
                                        do not fit into this category.

    @return               (dict)        Dictionary object with fields to
                                        describe the returned fingerprint:
                                        - 'categoryName': category string
                                        - 'positions': fingerprint bitmap (list
                                          of ON bit positions)
    """
    positiveExamples = []
    negativeExamples = []
    [positiveExamples.append({"text":p}) for p in positives]
    [negativeExamples.append({"text":n}) for n in negatives]
    dumpedData=json.dumps(
      {"positiveExamples":positiveExamples,
       "negativeExamples":negativeExamples}
    )

    responseObj = self._queryAPI("POST",
                                "/classify/create_category_filter",
                                {
                                  "retina_name": self.retina,
                                  "filter_name": category
                                },
                                postData=dumpedData,
                                headers={
                                  "Accept": "Application/json",
                                  "Content-Type": "application/json"
                                })

    return responseObj


  def getSDR(self, bitmap):
    """
    Returns the SDR for the input bitmap, which is a dictionary as returned by
    getBitmap().
    """
    size = bitmap["width"] * bitmap["height"]
    positions = bitmap["fingerprint"]["positions"]
    sdr = ""
    if len(positions) is 0:
      nextOn = None
    else:
      nextOn = positions.pop(0)

    for sdrIndex in range(0, size):

      if nextOn is None or nextOn != sdrIndex:
        sdr += "0"
      else:
        sdr += "1"
        if len(positions) is 0:
          nextOn = None
        else:
          nextOn = positions.pop(0)

    return sdr
