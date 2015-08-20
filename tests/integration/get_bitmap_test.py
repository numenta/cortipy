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

"""
  This test verifies that getBitmap correctly does the call to Cortical.io's
  API and returns a bitmap
"""

import cortipy
import unittest



class GetBitmapTest(unittest.TestCase):
  """Requires CORTICAL_API_KEY to be set"""

  def testValidResponse(self):
    client = cortipy.CorticalClient(useCache=False)
    bitmap = client.getBitmap("computer")

    self._checkValidBitmap(bitmap, "computer")

    
  def testMultipleTokens(self):
    client = cortipy.CorticalClient(useCache=False)
    with self.assertRaises(ValueError):
      client.getBitmap("this should use getTextBitmap")
      

  def testNoFPFromAPI(self):
    client = cortipy.CorticalClient(useCache=False)
    bitmap = client.getBitmap("thisisnotarealword.")

    self._checkValidBitmap(bitmap, "thisisnotarealword.")


  def _checkValidBitmap(self, bitmap, term):
    self.assertIsInstance(bitmap, dict,
        "The returned object is not a dictionary")
    self.assertIn("term", bitmap,
        "No \'term\' field in the returned object.")
    self.assertEqual(bitmap["term"], term,
        "The returned term is incorrect.")
    self.assertIsInstance(bitmap["fingerprint"], dict,
        "The returned object does not contain a \'fingerprint'\ dictionary.")
    self.assertIn("positions", bitmap["fingerprint"],
        "The returned object does not contain a \'positions\' field for the "
        "\'fingerprint\'.")
    self.assertIsInstance(bitmap["fingerprint"]["positions"], list,
        "The returned object does not contain a \'positions\' list within its "
        " \'fingerprint\' dictionary.")



if __name__ == '__main__':
  unittest.main()
