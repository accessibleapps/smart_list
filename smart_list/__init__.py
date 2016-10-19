from __future__ import absolute_import
from .smart_list import SmartList, VirtualSmartList, Column

def find_datafiles():
 if platform.system() != 'Windows':
  return []
 import sys
 import smart_list
 path = os.path.join(smart_list.__path__[0])
 return [('', [os.path.join(path, 'iat_hook.dll')])]
