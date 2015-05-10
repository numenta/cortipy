
import cortipy
import httpretty
import os
import unittest2 as unittest

from mock import patch

MOCK_API_DATA_DIR = os.path.join(
  os.path.dirname(os.path.abspath(__file__)),
  "mock-api-data"
)


def getMockApiData(name):
  with open(os.path.join(MOCK_API_DATA_DIR, name)) as dataFile:
    return dataFile.read()



class CorticalClientTestCase(unittest.TestCase):


  @patch.object(os, 'makedirs')
  def testConstructionDoesNotTouchFileSystem(self, mockMkdirs):
    # Construct the client.
    cortipy.CorticalClient()
    assert(mockMkdirs.call_count == 0)


  @httpretty.activate
  def whenUsingCache_ApiCallsWriteToCache(self):
    client = cortipy.CorticalClient(useCache=True)
    client._queryAPI()
    pass



  def whenUsingCache_ApiCallsReadFromCache(self):
    client = cortipy.CorticalClient(useCache=True)
    pass



  def whenNotUsingCache_ApiCallsDontWriteToCache(self):
    client = cortipy.CorticalClient(useCache=False)
    pass



  def whenNotUsingCache_ApiCallsDontReadFromCache(self):
    client = cortipy.CorticalClient(useCache=False)
    pass


if __name__ == '__main__':
  unittest.main()
