import os
import cortipy

import unittest2 as unittest
from mock import patch

class CorticalClientTestCase(unittest.TestCase):
  
  def testConstructionDoesNotTouchFileSystem(self):
    with patch.object(os, 'makedirs') as mock_mkdirs:
      # Construct the client.
      cortipy.CorticalClient()
    assert(mock_mkdirs.call_count == 0)
    
    