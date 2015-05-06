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

try:
  import simplejson as json
except ImportError:
  import json


DEFAULT_BASE_URL = "http://api.cortical.io/rest"
DEFAULT_RETINA = "en_synonymous"
DEFAULT_CACHE_DIR = "/tmp/cortipy"
DEFAULT_VERBOSITY = 1
DEFAULT_FILL_SDR = "random"

# A retina is the cortical.io word space model:
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

TARGET_SPARSITY = 0.01



class CorticalClient():
  """
  Main class for making calls to the REST API. The function calls here are
  derived from the cortical.io Python SDK.
  """

  def __init__(self,
               apiKey=None,
               baseUrl=DEFAULT_BASE_URL,
               retina=DEFAULT_RETINA,
               cacheDir=DEFAULT_CACHE_DIR,
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


  def _queryAPI(self, resourcePath, method, queryParams, postData, headers={}):
    url = self.apiUrl + resourcePath
    headers['api-key'] = self.apiKey
    response = None
    
    if method == 'GET':
      response = requests.get(url, params=queryParams, headers=headers)
    elif method == 'POST':
      response = requests.post(
        url, params=queryParams, headers=headers, data=postData)
    else:
      raise Exception('Method ' + method + ' is not recognized.')
    if response.status_code != 200:
      raise Exception("Response " + str(response.status_code)
                      + ": " + response.content)

    return response


  def _writeToCache(self, path, data, ref):
    """Write to cache data that has been serialized to a json-formatted str."""
    # Lazily create cache directory.
    cacheDir = os.path.join(self.cacheDir, self.retina)
    if not os.path.exists(cacheDir):
      if self.verbosity > 0:
        print "\tcreating cache at %s" % cacheDir
      os.makedirs(cacheDir)
    if self.verbosity > 0:
        print "\twriting \'%s\' data to the cache" % ref
    with open(path, 'w') as f:
      f.write(data)


  def _fetchFromCache(self, path, ref):
    if self.verbosity > 0:
        print "\tfetching \'%s\' data from the cache" % ref
    return json.loads(open(path).read())


  def _placeholderFingerprint(self, string, option):
    """
    When the API returns a null fingerprint, fill with a random or empty bitmap.
    
    We seed the random number generator such that a given string will yield the
    same fingerprint each time this function is called.
    Saving the internal state of the generator reduces the likelihood of
    repeating values from previous inputs.
    """
    if option == "random":
      size = RETINA_SIZES[self.retina]
      total = int(float(size["width"]) * float(size["height"]))
      state = random.getstate()
      random.seed(string)
      fingerprint = random.sample(xrange(total), int(total*TARGET_SPARSITY))
      random.setstate(state)
      return {"positions":fingerprint}
        ## TODO: test if these need to be sorted... if so, use fingerprint.sort()
    else:
      return {"positions":[]}


  def getBitmap(self, term):
    """
    For the input term, return the SDR info; either from cache or the REST API.
    If the input term is longer than one token, a different class of the API
    will be queried, returning a fingerprint to represent the full string.
    
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
      return self.getTextBitmap(term)
    
    # Each term has a unique cache location:
    cachePath = os.path.join(self.cacheDir,
                  "fingerprint-" + hashlib.sha224(term).hexdigest() + ".json")
                  
    # Pull fingerprint from the cache if it's there, otherwise query the API.
    if os.path.exists(cachePath):
      return self._fetchFromCache(cachePath, term)
    if self.verbosity > 0:
      print "\tfetching \'%s\' fingerprint from REST API" % term
    response = self._queryAPI(resourcePath="/terms",
                             method="GET",
                             headers={"Accept": "Application/json",
                               "Content-Type": "application/json"},
                             queryParams = {
                               "retina_name":self.retina,
                               "term":term,
                               "start_index":0,
                               "max_results":10,
                               "get_fingerprint":True
                               },
                             postData=None)
    responseObj = json.loads(response.content)

    if isinstance(responseObj, list) and len(responseObj)>0:
      fpInfo = responseObj[0]
    else:
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

    self._writeToCache(cachePath, json.dumps(fpInfo), term)

    return fpInfo


  def getTextBitmap(self, string):
    """
    This function is called when a string of multiple tokens are passed to
    getBitmap().
    NOTE: this should only be called from w/in getBitmap(), not by the user.
    
    @param  term       (string)     A string of multiple tokens.
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
    # Each string has a unique cache location:
    cachePath = os.path.join(self.cacheDir,
                  "fingerprint-" + hashlib.sha224(string).hexdigest() + ".json")
                  
    # Pull fingerprint from the cache if it's there, otherwise query the API.
    if os.path.exists(cachePath):
      return self._fetchFromCache(cachePath, string)
    if self.verbosity > 0:
      print "\tfetching \'%s\' fingerprint from REST API" % string
    response = self._queryAPI(resourcePath="/text",
                             method="POST",
                             headers={"Accept": "Application/json",
                               "Content-Type": "application/json"},
                             queryParams = {
                               "retina_name":self.retina
                               },
                             postData=string)
    responseObj = json.loads(response.content)

    if isinstance(responseObj, list) and len(responseObj)>0:
      fpInfo = {"fingerprint":responseObj[0]}
    else:
      fpInfo = {}
      if self.verbosity > 0:
        print ("API could not return info for the text \'%s\'. Perhaps the "
              "text includes punctuation that should be ignored by the "
              "tokenizer.\nGenerating a placeholder fingerprint for \'%s\'..."
              % (string, string))
      fpInfo["score"] = None
      fpInfo["pos_types"] = None
      fpInfo["term"] = string
      fpInfo["fingerprint"] = self._placeholderFingerprint(
        string, DEFAULT_FILL_SDR)
    
    # Include values for SDR dimensions and sparsity.
    if (not "width" in fpInfo) or (not "height" in fpInfo):
      size = RETINA_SIZES[self.retina]
      fpInfo["width"] = size["width"]
      fpInfo["height"] = size["height"]
    total = float(fpInfo["width"]) * float(fpInfo["height"])
    on = len(fpInfo["fingerprint"]["positions"])
    sparsity = round((on / total) * 100)
    fpInfo["sparsity"] = sparsity

    self._writeToCache(cachePath, json.dumps(fpInfo), string)

    return fpInfo


  def bitmapToTerms(self, onBits):
    """
    For the given bitmap, returns the most likely terms for which it encodes.
    
    @param  onBits          (list)             Bitmap for a fingerprint.
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
    data = json.dumps({"positions": onBits})
    cachePath = os.path.join(self.cacheDir,
                  "similarTerms-" + hashlib.sha224(data).hexdigest() + ".json")
    
    # Pull terms from the cache if they're there, otherwise query the API.
    if os.path.exists(cachePath):
      return self._fetchFromCache(cachePath, "similar terms")
    if self.verbosity > 0:
      print "\tfetching similar terms from REST API"
    
    response = self._queryAPI(resourcePath="/expressions/similar_terms",
                             method="POST",
                             headers={"Accept": "Application/json",
                               "Content-Type": "application/json"},
                             queryParams = {
                               "retina_name":self.retina,
                               "start_index":0,
                               "max_results":10,
                               "get_fingerprint":False,
                               "pos_type":None,
                               "sparsity":TARGET_SPARSITY,
                               "context_id":None
                               },
                             postData=data)
    
    self._writeToCache(cachePath, response.content, "similar terms")

    # Return terms in human-readable format
    responseObj = json.loads(response.content)
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
      >>> c.tokenize('The cow jumped over the moon. Then it ran to the other '
                     'side. And then the sun came up.')
      ['the,cow,jumped,over,the,moon', 'then,it,ran,to,the,otherside', 
      'and,then,the,sun,came,up']
    
    Optional query params:
      - 'POStags': tokenizer will only return the specified parts of speech
    """
    # Each list of tokens has a unique cache location:
    cachePath = os.path.join(self.cacheDir,
                  "tokenize-" + hashlib.sha224(text).hexdigest() + ".json")
    # Pull tokens from the cache if they're there, otherwise query the API.
    if os.path.exists(cachePath):
      return self._fetchFromCache(cachePath, "tokens")
    if self.verbosity > 0:
      print "\ttokenizing the text by querying the REST API"
    response = self._queryAPI(resourcePath="/text/tokenize",
                             method="POST",
                             headers={"Accept": "Application/json",
                               "Content-Type": "application/json"},
                             queryParams = {
                               "retina_name":self.retina,
                               "POStags":None
                               },
                             postData=text)
    self._writeToCache(cachePath, response.content, "tokens")

    splits = response.content[1:-1].split("\"")
    return [splits[i] for i in range(len(splits)) if i%2 != 0]


  def slice(self, text):
    """
    Slice the text into meaningful sections; over a sequence of sdrs in a text,
    slices at significant changes in the meaning.
    
    Optional query params:
      - 'get_fingerprint': boolean, if the fingerprint should be returned with
      the results
    """
    # Each list of slices has a unique cache location:
    cachePath = os.path.join(self.cacheDir,
                  "slice-" + hashlib.sha224(text).hexdigest() + ".json")
    # Pull slices from the cache if they're there, otherwise query the API.
    if os.path.exists(cachePath):
      return self._fetchFromCache(cachePath, "slices")
    if self.verbosity > 0:
      print "\tslicing the text by querying the REST API"
    response = self._queryAPI(resourcePath="/text/slices",
                             method="POST",
                             headers={"Accept": "Application/json",
                               "Content-Type": "application/json"},
                             queryParams = {
                               "retina_name":self.retina,
                               "start_index":0,
                               "max_results":10,
                               "get_fingerprint":False
                               },
                             postData=text)
    self._writeToCache(cachePath, response.content, "slices")
#    import pdb; pdb.set_trace()  ## TODO: investigate returns slices as expected
    return response.content
  
  
  def compare(self, fingerprint1, fingerprint2):
    """
    Given two fingerprints, return the comparison of their bitmaps.
    
    @params fingerprintX    (dict)      Fingerprint dictionary, as returned by
                                        getBitmap().
    @return                 (dict)      Dictionary of the REST comparison
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
    bitmap1 = fingerprint1["fingerprint"]["positions"]
    bitmap2 = fingerprint2["fingerprint"]["positions"]
    # Each pair of fingerprints has a unique cache location:
    cachePath = os.path.join(self.cacheDir, "compare-" +
      hashlib.sha224(str(sorted(bitmap1+bitmap2))).hexdigest() +
      ".json")
    # Pull slices from the cache if they're there, otherwise query the API.
    if os.path.exists(cachePath):
      return self._fetchFromCache(cachePath, "comparison")
    if self.verbosity > 0:
      print "\tcomparing the bitmaps by querying the REST API"
    data = json.dumps(
      [
        {"positions": bitmap1},
        {"positions": bitmap2}
      ]
    )
    response = self._queryAPI(resourcePath="/compare",
                             method="POST",
                             headers={"Accept": "Application/json",
                                      "Content-Type": "application/json"},
                             queryParams = {"retina_name":self.retina},
                             postData=data)
    self._writeToCache(cachePath, response.content, "comparison")
    
    return json.loads(response.content)


  def getContext(self, term):
    """
    Get contexts for a given term. The context ids can be used as parameters in
    bitmapToTerms().
    
    @return     (list)        A list of dictionaries, where the keys are
                              'context_label', 'fingerprint' (the bitmap for the
                              context label), and 'context_id'.
    """
    # Each list of tokens has a unique cache location:
    cachePath = os.path.join(self.cacheDir,
                  "context-" + hashlib.sha224(term).hexdigest() + ".json")
    # Pull tokens from the cache if they're there, otherwise query the API.
    if os.path.exists(cachePath):
      return self._fetchFromCache(cachePath, "context")
    if self.verbosity > 0:
      print "\tfetching the term's context from the REST API"
    response = self._queryAPI(resourcePath="/terms/contexts",
                             method="GET",
                             headers={"Accept": "Application/json",
                               "Content-Type": "application/json"},
                             queryParams = {
                               "retina_name":self.retina,
                               "term":term,
                               "start_index":0,
                               "max_results":10,
                               "get_fingerprint":True,
                               },
                             postData=None)
    self._writeToCache(cachePath, response.content, "context")

    return response.content
  

  def getSDR(self, term):
    """Returns the SDR for the input term."""
    bitmap = self.getBitmap(term)
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
