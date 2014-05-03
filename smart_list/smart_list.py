import os
import wx
from wx import dataview
from frozendict import frozendict

import collections
import functools
import platform
import logging
logger = logging.getLogger(__name__)
#Patch windows 8's broken UIA implementation
import resource_finder
if platform.system() == 'Windows':
 import commctrl
 from ctypes import *
 from ctypes.wintypes import *
 callback_type = WINFUNCTYPE(c_int, c_int, c_int, c_int, c_int)
 @callback_type
 def callback(hwnd, msg, wParam, lParam):
  if msg == commctrl.LVM_GETITEMCOUNT:
   return 0
  return old_proc(hwnd, msg, wParam, lParam)

def install_iat_hook():
 global old_proc
 iat_hook = cdll[resource_finder.find_application_resource('iat_hook.dll')]
 uiacore = windll.kernel32.LoadLibraryA("uiautomationcore.dll")
 if uiacore != 0:
  old_proc = callback_type()
  iat_hook.PatchIat(uiacore, "user32.dll", "SendMessageW", callback, pointer(old_proc))

if platform.system() == 'Windows' and platform.release() == '8':
 try:
  install_iat_hook()
 except:
  logger.exception("Unable to install IAT hook")

def freeze_and_thaw(func):
 @functools.wraps(func)
 def closure(self, *args, **kwargs):
  self.control.Freeze()
  func(self, *args, **kwargs)
  self.control.Thaw()
 return closure

def freeze_dict(d):
 for k, v in d.iteritems():
  if isinstance(v, collections.MutableMapping):
   d[k] = freeze_dict(v)
  if isinstance(v, collections.MutableSequence):
   d[k] = freeze_list(v)
 return frozendict(d)

def freeze_list(l):
 for n, i in enumerate(l):
  if isinstance(i, collections.MutableSequence):
   l[n] = freeze_list(i)
  if isinstance(i, collections.MutableMapping):
   l[n] = freeze_dict(i)
 return tuple(l)

class VirtualDataViewModel(dataview.PyDataViewVirtualListModel):
 def __init__(self, parent_obj):
  self.count = 0
  super(VirtualDataViewModel, self).__init__(self.count)
  self.parent = parent_obj
  self.columns = []

 def GetCount(self):
  return self.count

 def SetCount(self, count):
  self.count = count
  self.Reset(count)

 def GetColumnCount(self):
  return len(self.columns)

 def GetColumnType(self, col):
  return "string"

 def GetValueByRow(self, row, col):
  res = ''
  try:
   res = self.parent.OnGetItemText(row, col)
  except Exception as e:
   logger.exception("Error retrieving row %r col %r" % (row, col))
   raise
  if res is None:
   res = ''
  return res

class ListWrapper(object):
 """Provides a standard abstraction over a ListView and DataView"""

 def __init__(self, parent=None, id=None, parent_obj=None, *args, **kwargs):
  self.use_dataview = platform.system() == 'Darwin'
  self.virtual = (kwargs.get("style", 0) & wx.LC_VIRTUAL)
  if not self.use_dataview:
   kwargs['style'] = kwargs.get('style', 0)|wx.LC_REPORT
   self.control = VirtualCtrl(parent_obj, parent=parent, id=id, *args, **kwargs)
  else:
   kwargs = kwargs.copy()
   if "style" in kwargs:
    del kwargs["style"]
   if self.virtual:
    self.control = dataview.DataViewCtrl(parent=parent, id=id, *args, **kwargs)
    self.wx_model = VirtualDataViewModel(parent_obj)
    self.control.AssociateModel(self.wx_model)
   else:
    self.control = dataview.DataViewListCtrl(parent=parent, id=id, *args, **kwargs)
    self.wx_model = self.control.GetStore()

 def Append(self, item):
  if self.use_dataview:
   self.control.AppendItem(item)
  else:
   self.control.Append(item)

 def GetItemCount(self):
  if self.use_dataview:
   return self.wx_model.GetCount()
  return self.control.GetItemCount()

 def Insert(self, index, item, columns):
  if self.use_dataview:
   self.control.InsertItem(index, columns)
  else:
   self.control.InsertStringItem(index, columns[0])
   for i, col in enumerate(columns[1:]):
    self.SetColumnText(index, i+1, col)

 def SetColumnText(self, index, column, text):
  if self.use_dataview:
   self.control.SetTextValue(text, index, column)
  else:
   self.control.SetStringItem(index, column, text)

 def GetColumnText(self, index, column):
  if self.use_dataview:
   return self.control.GetTextValue(index, column)
  else:
   return self.control.GetItem(index, column).m_text

 def Freeze(self):
  self.control.Freeze()

 def Thaw(self):
  self.control.Thaw()

 def Select(self, index, select=True):
  if self.use_dataview:
   if index == -1:
    return
   self.control.Select(self.wx_model.GetItem(index))
  else:
   self.control.Select(index, select)

 def Destroy(self):
  return self.control.Destroy()

 def Bind(self, event, func):
  if self.use_dataview:
   if event == wx.EVT_CONTEXT_MENU:
    event = dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU
   elif event == wx.EVT_LIST_ITEM_ACTIVATED:
    event = wx.EVT_MENU_OPEN
  return self.control.Bind(event, func)

 def SetLabel(self, *args, **kwargs):
  return self.control.SetLabel(*args, **kwargs)

 def AppendColumn(self, title, width):
  if self.use_dataview:
   if self.virtual:
    self.wx_model.columns.append(title)
    self.control.AppendTextColumn(unicode(title), width=width, model_column=len(self.wx_model.columns) - 1)
   else:
    self.control.AppendTextColumn(unicode(title), width=width)
  else:
   index = self.control.GetColumnCount() + 1
   self.control.InsertColumn(index, unicode(title), width=width)

 def Clear(self):
  self.control.DeleteAllItems()

 def Delete(self, index):
  self.control.DeleteItem(index)

 def GetSelectedItems(self):
  if self.use_dataview:
   yield self.wx_model.GetRow(self.control.GetSelection())
  else:
   yield self.control.GetFirstSelected()
  for selection in xrange(1, self.control.GetSelectedItemCount()):
   yield self.control.GetNextSelected(selection)

 def GetSelectedIndex(self):
  if self.use_dataview:
   selection = self.control.GetSelection()
   if not selection.IsOk():
    return -1
   return self.wx_model.GetRow(self.control.GetSelection())
  else:
   return self.control.GetFirstSelected()

 def Unselect(self, index):
  self.Select(index, False)

 def SetFocus(self):
  self.control.SetFocus()

 def HasFocus(self):
  return self.control.HasFocus()

 def SetSelectedIndex(self, index):
  if self.use_dataview:
   if index <= self.GetItemCount()-1:
    self.control.SelectRow(index)
  else:
   self.control.Select(index)
   self.control.Focus(index)

 def SetItemCount(self, count):
  if self.use_dataview:
   self.wx_model.SetCount(count)
  else:
   self.control.SetItemCount(count)

 def RefreshItems(self, from_item, to_item):
  self.control.RefreshItems(from_item, to_item)

 def SetLabel(self, label):
  self.control.SetLabel(label)

class VirtualCtrl(wx.ListCtrl):

 def __init__(self, parent_obj, *args, **kwargs):
  super(VirtualCtrl, self).__init__(*args, **kwargs)
  self.parent = parent_obj

 def OnGetItemText(self, idx, col):
  return self.parent.OnGetItemText(idx, col)

class SmartList(object):

 def __init__(self, parent=None, id=-1, *args, **kwargs):
  choices = kwargs.pop('choices', [])
  self.control = ListWrapper(parent_obj=self, parent=parent, id=id, *args, **kwargs)
  #somewhere to store our model objects
  self.models = []
  self.list_items = []
  self.index_map = {}
  self.columns = []
  self.add_items(choices)


 def set_columns(self, columns):
  self.columns = columns
  for column in columns:
   self.control.AppendColumn(column.title, column.width)

 def get_columns_for(self, model):
  cols = []
  for c in self.columns:
   cols.append(c.get_model_value(model))
  return cols

 def get_items(self):
  return self.models

 @freeze_and_thaw
 def add_items(self, items):
  if self.index_map is None:
   self._rebuild_index_map()
  for item in items:
   columns = self.get_columns_for(item)
   self.control.Append(columns)
   self.models.append(item)
   if isinstance(item, collections.MutableMapping):
    item = freeze_dict(item)
   self.index_map[item] = len(self.models) - 1


 def find_index_of_item(self, model):
  if self.index_map is None:
   self._rebuild_index_map()
  if isinstance(model, dict):
   model = freeze_dict(model)
  index = self.index_map.get(model)
  if index is None:
   raise ValueError("Unable to find index of item %r " % item)
  return index

 def find_item_from_index(self, index):
  if len(self.models) <= index:
   return None
  return self.models[index]

 def _rebuild_index_map(self):
  self.index_map = {}
  for i, model in enumerate(self.models):
   if isinstance(model, dict) or isinstance(model, collections.MutableMapping):
    model = freeze_dict(model)
   self.index_map[model] = i

 def clear(self):
  self.control.Clear()
  self.index_map = None
  del self.models[:]

 def add_item(self, item):
  self.add_items((item,))

 append = add_item

 def delete_item(self, item):
  self.delete_items((item,))

 @freeze_and_thaw
 def delete_items(self, items):
  if self.index_map is None:
   self._rebuild_index_map()
  for item in items:
   if isinstance(item, collections.MutableMapping):
    item = freeze_dict(item)
   self.models.remove(item)
   self.control.Delete(self.index_map[item])
  self.index_map = None

 def get_selected_items(self):
  for item in self.control.GetSelectedItems():
   yield self.find_item_from_index(item)

 def get_selected_item(self):
  try:
   return self.get_selected_items().next()
  except StopIteration:
   return

 def get_selected_index(self):
  return self.control.GetSelectedIndex()

 def select_model(self, item):
  index = self.find_index_of_item(item)
  self.control.SetSelectedIndex(index)

 select_item = select_model

 def set_selected_index(self, index):
  self.control.SetSelectedIndex(index)

 def insert_item(self, index, item):
  columns = self.get_columns_for(item)
  self.control.Insert(index, item, columns)
  self.index_map = None
  self.models.insert(index, item)

 def update_item(self, item, original=None):
  if original is None:
   original = item
  index = self.find_index_of_item(original)
  if index is None:
   logger.warn("item %r not found" % item)
  item = self.freeze_item(item)
  original = self.freeze_item(original)
  columns = self.get_columns_for(item)
  for i, c in enumerate(columns):
   #Updating column 0 causes the entire row to be read, so only do it if needed
   if i == 0 and self.control.GetColumnText(index, i) == c:
    continue
   self.control.SetColumnText(index, i, c)

  self.models[index] = item
  if self.index_map is not None:
   del self.index_map[original]
   self.index_map[item] = index

 def freeze_item(self, item):
  if isinstance(item, collections.MutableMapping):
   item = freeze_dict(item)
  return item

 def update_models(self, models):
  if self.index_map is None:
   self._rebuild_index_map()
  for model in models:
   if model in self.index_map:
    self.update_item(model)
   else:
    self.add_item(model)

 def SetMinSize(self, size):
  self.control.control.SetMinSize(size)

 def Hide(self):
  return self.control.control.Hide()

 def SetLabel(self, label):
  self.control.SetLabel(label)

class VirtualSmartList(SmartList):

 allowed_navigation_keys = [getattr(wx, 'WXK_%s' % key.upper()) for key in "up down left right home end pageup pagedown space return".split()]

 def __init__(self, get_virtual_item=None, update_cache=None, *args, **kwargs):
  if get_virtual_item is None:
   raise RuntimeError, 'get_virtual_item cannot be None'

  kwargs['style'] = kwargs.get('style', 0)|wx.LC_VIRTUAL
  super(VirtualSmartList, self).__init__(*args, **kwargs)
  self.get_virtual_item = get_virtual_item
  if update_cache is not None:
   self.control.Bind(wx.EVT_LIST_CACHE_HINT, self.handle_cache)
  self.caching_from = 0
  self.caching_to = 0
  self.update_cache = update_cache
  self.cache = []
  self.control.Bind(wx.EVT_CHAR, self.on_list_key_down)

 def on_list_key_down(self, evt):
  if evt.KeyCode in self.allowed_navigation_keys:
   evt.Skip()

 def OnGetItemText(self, item, col):
  if self.update_cache is not None and self.cache and self.caching_from <= item and self.caching_to >= item:
   wanted = item-self.caching_from
   #print "from %d to %d wanted %d len %d" % (self.caching_from, self.caching_to, wanted, len(self.cache))
   model = self.cache[wanted]
  else:
   model = self.get_virtual_item(item)
  return self.columns[col].get_model_value(model)

 def update_count(self, count):
  self.control.SetItemCount(count)

 def handle_cache(self, event):
  from_row = event.GetCacheFrom()
  to_row = event.GetCacheTo()
  if self.caching_from <= from_row and self.caching_to >= to_row:
   return
  self.caching_from = from_row
  self.caching_to = to_row
  self.cache = self.update_cache(from_row, to_row)

 def refresh(self):
  self.control.RefreshItems(0, self.control.GetItemCount()-1)
  self.cache = []
  self.caching_from = 0
  self.caching_to = 0

 def find_index_of_item(self, item):
  for i in xrange(self.control.GetItemCount()):
   model = self.get_virtual_item(i)
   if model == item:
    return i
  raise ValueError("Unable to find index of item %r " % item)

 def Freeze(self):
  self.control.Freeze()

 def Thaw(self):
  self.control.Thaw()

class Column(object):

 def __init__(self, title=None, width=-1, model_field=None):
  self.title = title
  self.model_field = model_field
  self.width = width

 def get_model_value(self, model):
  if self.model_field is None:
   return ''
  if callable(self.model_field):
   return unicode(self.model_field(model))
  try:
   value = getattr(model, self.model_field)
  except (AttributeError, TypeError):
   try:
    value = model[self.model_field]
   except (KeyError, TypeError):
    raise RuntimeError("Unable to find a %r attribute or key on model %r" % (self.model_field, model))
  if hasattr(value, '__unicode__'):
   return unicode(value)
  if callable(value):
   value = value()
  return unicode(value)

def find_datafiles():
 if platform.system() != 'Windows':
  return []
 import sys
 path = os.path.split(os.path.abspath(sys.modules[find_datafiles.__module__].__file__))[0]
 return [('', [os.path.join(path, 'iat_hook.dll')])]
