import cortipy
import os
import requests
import unittest2 as unittest

from mock import Mock, patch



class CorticalClientTestCase(unittest.TestCase):
  
  def testConstructionDoesNotTouchFileSystem(self):
    with patch.object(os, 'makedirs') as mock_mkdirs:
      # Construct the client.
      cortipy.CorticalClient()
    self.assertEqual(mock_mkdirs.call_count, 0)
    

  def testWriteToCache(self):
    pass


  def testFetchFromCache(Self):
    pass
  
  
  def testGetQueryToAPI(self):
    # Patch the request in cortipy.CorticalCLient._queryAPI().
    with patch.object(requests, 'get') as mock_get:
      mock_get.return_value = mock_response = Mock()
      mock_response.status_code = 200
      client = cortipy.CorticalClient("apikey")
      response = client._queryAPI("path", 'GET', {}, None, {})
      self.assertEqual(response.status_code, 200)


  def testPostQueryToAPI(self):
    # Patch the request in cortipy.CorticalCLient._queryAPI().
    with patch.object(requests, 'post') as mock_post:
      mock_post.return_value = mock_response = Mock()
      mock_response.status_code = 200
      client = cortipy.CorticalClient("apikey")
      response = client._queryAPI("path", 'POST', {}, None, {})
      self.assertEqual(response.status_code, 200)


  def testCompare(self):
    client = cortipy.CorticalClient("apikey")
  
    # Test bitmaps of identical SDRs.
    fp1 = {"width":4,
          "height":4,
          "fingerprint":{"positions":[0,13]}
          }
    fp2 = {"width":4,
          "height":4,
          "fingerprint":{"positions":[0,13]}
          }
    distances = client.compare(fp1, fp2)
    self.assertEqual(distances["euclideanDistance"], 0.0,
      "Euclidean distance is incorrect.")
    self.assertEqual(distances["overlappingAll"], 2,
      "Overlap count is incorrect.")
    
    # Test bitmaps of orthogonal SDRs.
    fp1 = {"width":4,
          "height":4,
          "fingerprint":{"positions":[0]}
          }
    fp2 = {"width":4,
          "height":4,
          "fingerprint":{"positions":[15]}
          }
    distances = client.compare(fp1, fp2)
    self.assertEqual(distances["euclideanDistance"], 1.0,
      "Euclidean distance is incorrect.")
    self.assertEqual(distances["overlappingAll"], 0,
      "Overlap count is incorrect.")
    
    # Test bitmaps of similar SDRs, w/ overlap, to be closer than those of
    # dissimilar SDRs.
    fp1 = {"width":4,
          "height":4,
          "fingerprint":{"positions":[0,1]}
          }
    fp2 = {"width":4,
          "height":4,
          "fingerprint":{"positions":[1,3]}
          }
    fp3 = {"width":4,
          "height":4,
          "fingerprint":{"positions":[10,11]}
          }
    distances_similar = client.compare(fp1, fp2)
    distances_dissimilar = client.compare(fp1, fp3)
    self.assertTrue((distances_similar["euclideanDistance"] <
            distances_dissimilar["euclideanDistance"]), ("Euclidean for "
            "dissimilar SDRs is incorrectly less than that of similar SDRs."))
    self.assertTrue((distances_similar["overlappingAll"] <
            distances_dissimilar["overlappingAll"]), ("Overlap for dissimilar "
            "SDRs is incorrectly less than that of similar SDRs."))


  def testGetContextReturnFields(self):
    client = cortipy.CorticalClient("apikey")
    contexts = client.getContext("android")
    
    # Test for correct fields.
    self.assertTrue(isinstance(contexts, list))
    self.assertTrue(("context_label" and "fingerprint" and "context_id")
      in contexts[0], "Data structure returned by getContext() does not contain"
      " req'd fields.")
    
    # Test context fields have contents as expected.
    self.assertTrue(isinstance(contexts[0]["context_label"], str))
    self.assertEqual(contexts[0]["context_id"], 0)
    

  def testGetSDRFromFingerprint(self):
    client = cortipy.CorticalClient("apikey")
    
    fp = {"width":4,
          "height":4,
          "fingerprint":{"positions":[0,13]}
          }
    self.assertEqual(client.getSDR(fp), '1000000000000100')

    fp = {"width":4,
          "height":4,
          "fingerprint":{"positions":[]}
          }
    self.assertEqual(client.getSDR(fp), '0000000000000000')


if __name__ == '__main__':
  unittest.main()
