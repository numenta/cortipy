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
import requests

try:
  import simplejson as json
except ImportError:
  import json


DEFAULT_BASE_URL = "http://api.cortical.io/rest"
DEFAULT_RETINA = "en_synonymous"
DEFAULT_CACHE_DIR = "/tmp/cortipy"
DEFAULT_VERBOSITY = 0
DEFAULT_PARTOFPSEECH = None

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

TARGET_SPARSITY = 0.03



class CorticalClient(): ## TO DO: move rest of pycept/cept.py over
  """
  Main class for making calls to the REST API.
  """

  def __init__(self,
               apiKey=None,
               baseUrl=DEFAULT_BASE_URL,
               retina=DEFAULT_RETINA,
               cacheDir=DEFAULT_CACHE_DIR,
               verbosity=DEFAULT_VERBOSITY):
    # Instantiate API credentials
    if apiKey:
      self.apiKey = apiKey
    else:
      self.apiKey = os.environ["REST_API_KEY"]
    self.apiUrl = baseUrl
    
    # Create the cache directory if necessary.
    cacheDir = os.path.join(cacheDir, retina)
    if not os.path.exists(cacheDir):
      os.makedirs(cacheDir)
    self.cacheDir = cacheDir
    
    self.verbosity = verbosity
    self.retina = retina


  def _callAPI(self, resourcePath, method, queryParams, postData, headers={}):
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


#  def _writeToCache(self, data, type):
#    # Create a cache location for the data, where it will be fetched from.
#    cachePath = os.path.join(self.cacheDir,
#                  type + "-" + hashlib.sha224(term).hexdigest() + ".json")
#
#    return path
#
#
#  def _fetchFromCache(self, path):
#
#
#    return data


  def getBitmap(self, term):
    # -> Will this also work for larger pieces of text? If not, need to use Text api
    """
    For the input term, return the SDR info; either from cache or the REST API.
    
    @param  term        (string)        A single token.
    @return sdrInfo     (dict)          Dictionary object with fields to describe the
                                       SDR -- 'positions' of ON bits, 'sparsity'
                                       percentage, and 'width and 'height' 
                                       dimensions.
    """
    # Create a cache location for each term, where it will be read in from.
    # If we need the REST API for the SDR, this is where it will be cached.
    cachePath = os.path.join(self.cacheDir,
                  "bitmap-" + hashlib.sha224(term).hexdigest() + ".json")
                  
    # Pull SDR from the cache if it's there
    sdrInfo = {}
    if os.path.exists(cachePath):
      if self.verbosity > 0:
        print "\tfetching %s sdr from the cache" % term
      sdrInfo = json.loads(open(cachePath).read())

    # Or instead query the REST API for the SDR
    else:
      if self.verbosity > 0:
        print "\tfetching %s sdr from REST API" % term
#      response = self._callAPI(resourcePath="/text",
#                               method="POST",
#                               headers={"Accept": "Application/json",
#                                 "Content-Type": "application/json"},
#                               queryParams = {
#                                 "retina_name":self.retina
#                                 },
#                               postData=term)
      response = self._callAPI(resourcePath="/terms",
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
#      import pdb; pdb.set_trace()
      if isinstance(responseObj, list) and len(responseObj)>0:
        sdrInfo = responseObj[0]
#      elif responseObj==[]:
#        # no fingerprint generated
#        "==> Why am I here???"  ## Remove if this never happens
#        import pdb; pdb.set_trace()
#        sdrInfo = {"positions": []}
      else:
        sdrInfo["term"]=term
        sdrInfo["score"]=None
        sdrInfo["pos_types"]=None
        sdrInfo["fingerprint"]={"positions":[]}
      if (not "width" in sdrInfo) or (not "height" in sdrInfo):
        size = RETINA_SIZES[self.retina]
        sdrInfo["width"] = size["width"]
        sdrInfo["height"] = size["height"]

#      import pdb; pdb.set_trace()
      # attach the sparsity for reference
      total = float(sdrInfo["width"]) * float(sdrInfo["height"])
      on = len(sdrInfo["fingerprint"]["positions"])
      sparsity = round((on / total) * 100)
      sdrInfo["sparsity"] = sparsity
      ## TO DO: unit test (and raise exception here?) for sparsity w/in range of TARGET_SPARSITY

      # write to cache
      with open(cachePath, 'w') as f:
        f.write(json.dumps(sdrInfo))

    return sdrInfo


  def bitmapToTerms(self, onBits):
    """
    
    @param  onBits        ()
    @return similar       ()
    
    add this info: https://github.com/BoltzmannBrain/python-client-sdk/blob/master/python-client-sdk/expressionsApi.py#L77
    
    """
    if len(onBits) is 0:
      raise Exception("Cannot convert empty bitmap to term!")
    
    # Create a cache location for each term, where it will be read in from.
    # If we need the REST API for the SDR, this is where it will be cached.
    data = json.dumps({"positions": onBits})
    cachePath = os.path.join(self.cacheDir,
                  "similarTerms-" + hashlib.sha224(data).hexdigest() + ".json")
    
    # Pull from the cache if it's there
    if os.path.exists(cachePath):
      if self.verbosity > 0:
        print "\tfetching raw (similar) terms from the cache"
      responseObj = json.loads(open(cachePath).read())

    # Or instead query the REST API for the raw (similar) terms
    else:
      if self.verbosity > 0:
        print "\tfetching raw (similar) terms from REST API"
      # include part of speech?
      if DEFAULT_PARTOFPSEECH:
        pos = data["pos_types"]
      else:
        pos = None
      response = self._callAPI(resourcePath="/expressions/similar_terms",
                               method="POST",
                               headers={"Accept": "Application/json",
                                 "Content-Type": "application/json"},
                               queryParams = {
                                 "retina_name":self.retina,
                                 "start_index":0,
                                 "max_results":10,
                                 "get_fingerprint":False,
                                 "pos_type":pos,
                                 "sparsity":TARGET_SPARSITY,
                                 "context_id":None
                                 },
                               postData=data)
      # Cache the response data
      with open(cachePath, 'w') as f:
        f.write(response.content)
      responseObj = json.loads(response.content)

#    import pdb; pdb.set_trace()
    # Return terms in a readable format
    similar = []
    for term in responseObj:
      similar.append(
        {"term": term["term"], "score": term["score"]}
      )
    return similar


  def tokenize(self, text): ## TODO - only text, no fingerprint... python-client-sdk/textApi.py line 65
    """Get a list of sentence tokens from a text string.
    
    @param text     (str)               Text string to tokenize
    @return         (list)              List of lists where each inner list 
                                        contains the string tokens from a
                                        sentence in the input text
    
    Example:
      >>> c = cc.CorticalClient(apiKey)
      >>> cc.tokenize('The cow jumped over the moon. Then it ran to the other '
                     'side. And then the sun came up.')
      [[u'cow', u'jumped', u'moon'], [u'ran', u'other side'], [u'sun', u'came']]
    """
    cachePath = os.path.join(self.cacheDir,
                  "tokenize-" + hashlib.sha224(text).hexdigest() + ".json")
    if os.path.exists(cachePath):
      with open(cachePath) as cacheFile:
        response = json.load(cacheFile)
#    else:


      with open(cachePath, 'w') as f:
        json.dump(response, f)

    return [sentence.split(",") for sentence in response]


  def compare(self, bitmap1, bitmap2): ## TODO
    """
    Given two bitmaps, return their comparison, i.e. a dict with the CEPT
    comparison metrics.
    Here's an example return dict:
      {
        "Cosine-Similarity": 0.6666666666666666,
        "Euclidean-Distance": 0.3333333333333333,
        "Jaccard-Distance": 0.5,
        "Overlapping-all": 6,
        "Overlapping-left-right": 0.6666666666666666,
        "Overlapping-right-left": 0.6666666666666666,
        "Size-left": 9,
        "Size-right": 9,
        "Weighted-Scoring": 0.4436476984102028
      }
    """
    
    pass


  def getSdr(self, term):
    bitmap = self.getBitmap(term)
    size = bitmap["width"] * bitmap["height"]
    positions = bitmap["positions"]
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
