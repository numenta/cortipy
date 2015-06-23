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
  This test verifies that getContext correctly does the call to Cortical.io's
  API and gets a list of contexts
"""

import cortipy

import unittest2 as unittest

class GetContextTest(unittest.TestCase):
  """Requires CORTICAL_API_KEY to be set"""
  def testGetContext(self):
    """
    Tests client.getContext() for a sample term.
    Asserts the returned object contains the correct fields and have contents as
    expected.
    """
    # Act: create the client object we'll be testing.
    client = cortipy.CorticalClient(useCache=False)

    contexts = client.getContext("android")
    self._checkValidContexts(contexts)
    
  def _checkValidContexts(self, contexts):
    # Assert: check the result object.
    self.assertIsInstance(contexts, list,
      "Returned object is not of type list as expected.")
    self.assertGreaterEqual(len(contexts), 1, "Returned object did not contain any elements")
    self.assertIsInstance(contexts[0], dict)
    self.assertIn("context_label", contexts[0], "Context does not contain \'context_label\'")
    self.assertIn("fingerprint", contexts[0], "Context does not contain \'fingerprint\'")
    self.assertIn("context_id", contexts[0], "Context does not contain \'context_id\'")
    self.assertIsInstance(contexts[0]["context_label"], str,
      "The \'context_label\' field is not of type string.")
    self.assertEqual(contexts[0]["context_id"], 0,
      "The top context does not have ID of zero.")
    self.assertIsInstance(contexts[0]["fingerprint"], dict,
      "The \'context_label\' field is not of type string.")
    self.assertIn("positions", contexts[0]["fingerprint"],
      "The returned object does not contain a \'positions\' field for the "
      "\'fingerprint\'.")
    self.assertIsInstance(contexts[0]["fingerprint"]["positions"], list,
      "The returned object does not contain a \'positions\' list within its "
      " \'fingerprint\' dictionary.")


if __name__ == '__main__':
  unittest.main()
