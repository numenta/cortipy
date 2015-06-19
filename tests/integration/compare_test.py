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
  This test verifies that compare correctly does the call to Cortical.io's
  API and gets a dictionary of distances
"""

import cortipy

import unittest2 as unittest

class CompareTest(unittest.TestCase):
  """Requires CORTICAL_API_KEY to be set"""

  def testCompare(self):
    """
    Tests client.createClassification(). Asserts the returned object has fields
    with expected values for both the classifciation name and bitmap.
    """
    client = cortipy.CorticalClient(useCache=False)
    bitmap1 = client.getBitmap("one")["fingerprint"]["positions"]
    bitmap2 = client.getBitmap("two")["fingerprint"]["positions"]

    distances = client.compare(bitmap1, bitmap2)

    types = ["cosineSimilarity", "euclideanDistance", "jaccardDistance",
        "overlappingAll", "overlappingLeftRight", "overlappingRightLeft",
        "sizeLeft", "sizeRight", "weightedScoring"]

    self.assertIsInstance(distances, dict,
        "The returned object is not a dictionary")

    for t in types:
      self.assertIn(t, distances,
          "No \'{}\' field in the distances".format(t))

    for t in types:
      self.assertIsInstance(distances[t], (float, int),
          "No \'{}\' field in the distances".format(t))


if __name__ == '__main__':
  unittest.main()
