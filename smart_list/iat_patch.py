#Patch windows 8's broken UIA implementation
# This hook disables the query which will attempt to enumerate all items in a list, which breaks with virtual listview implementations

import platform
import resource_finder

is_windows = platform.system() == 'Windows'
if is_windows:
 import commctrl
 from ctypes import *
 from ctypes.wintypes import *

 SendMessageW = windll.user32.SendMessageW

 callback_type = WINFUNCTYPE(c_int, c_int, c_int, c_int, c_int)
 @callback_type
 def callback_8(hwnd, msg, wParam, lParam):
  if msg == commctrl.LVM_GETITEMCOUNT:
   return 0
  return old_proc(hwnd, msg, wParam, lParam)

 @callback_type
 def callback_10(hwnd, msg, wParam, lParam):
  if msg == commctrl.LVM_GETITEMCOUNT:
   return 0
  return SendMessageW(hwnd, msg, wParam, lParam)

def install_iat_hook():
 global old_proc
 iat_hook = cdll[resource_finder.find_application_resource('iat_hook.dll')]
 uiacore = windll.kernel32.LoadLibraryA("uiautomationcore.dll")
 if uiacore != 0:
  old_proc = callback_type()
  if platform.release() == '8':
   iat_hook.PatchIat(uiacore, "user32.dll", "SendMessageW", callback_8, pointer(old_proc))
  else:
   iat_hook.PatchDelayedIat(uiacore, "ext-ms-win-rtcore-ntuser-window-ext-l1-1-0.dll", "SendMessageW", callback_10, pointer(old_proc))

