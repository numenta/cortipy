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
  This test verifies that createClassification correctly does the call to Cortical.io's
  API and returns a bitmap
"""

import cortipy

import unittest2 as unittest

class CreateClassificationTest(unittest.TestCase):
  """Requires CORTICAL_API_KEY to be set"""

  def testCreateClassification(self):
    """
    Tests client.createClassification(). Asserts the returned object has fields
    with expected values for both the classifciation name and bitmap.
    """
    client = cortipy.CorticalClient(useCache=False)

    name = "programming languages"
    positives = [
      "Always code as if the guy who ends up maintaining your code will be a \
      violent psychopath who knows where you live.",
      "To iterate is human, to recurse divine.",
      "First learn computer science and all the theory. Next develop a \
      programming style. Then forget all that and just hack." ]
    negatives = ["To err is human, to forgive divine."]

    response = client.createClassification(name, positives, negatives)

    self._checkValidResponse(response, name)

  def testCreateClassificationOnlyPositives(self):
    """
    Tests client.createClassification(). Asserts the returned object has fields
    with expected values for both the classifciation name and bitmap.
    """
    client = cortipy.CorticalClient(useCache=False)

    name = "programming languages"
    positives = [
      "Always code as if the guy who ends up maintaining your code will be a \
      violent psychopath who knows where you live.",
      "To iterate is human, to recurse divine.",
      "First learn computer science and all the theory. Next develop a \
      programming style. Then forget all that and just hack." ]

    response = client.createClassification(name, positives)

    self._checkValidResponse(response, name)
  
  def _checkValidResponse(self, response, name):
    # Assert: check the result object.
    self.assertIn("positions", response,
      "No \'positions\' field in the returned object.")
    self.assertIn("categoryName", response,
      "No \'categoryName\' field in the returned object.")

    self.assertEqual(response["categoryName"], name,
      "The returned category name is incorrect.")
    self.assertIsInstance(response["positions"], list,
      "The returned object does not contain a \'positions\' list.")


if __name__ == '__main__':
  unittest.main()
