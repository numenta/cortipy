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

class ExtractKeywordsTest(unittest.TestCase):
  """Requires CORTICAL_API_KEY to be set"""
  def testGetContextReturnFields(self):
    """
    Tests client.getContext() for a sample term.
    Asserts the returned object contains the correct fields and have contents as
    expected.
    """
    # Act: create the client object we'll be testing.
    client = cortipy.CorticalClient(useCache=False)

    keywords = client.extractKeywords("This is about food")

    # Assert: check the result object.
    self.assertIsInstance(keywords, list,
      "Returned object is not of type list as expected.")


if __name__ == '__main__':
  unittest.main()
