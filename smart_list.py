import wx
from wx import dataview

import functools

def freeze_and_thaw(func):
 @functools.wraps(func)
 def closure(self, *args, **kwargs):
  self.control.Freeze()
  func(self, *args, **kwargs)
  self.control.Thaw()
 return closure

class VirtualCtrl(wx.ListCtrl):

 def __init__(self, parent_obj, *args, **kwargs):
  super(VirtualCtrl, self).__init__(*args, **kwargs)
  self.parent = parent_obj

 def OnGetItemText(self, col, idx):
  return self.parent.OnGetItemText(col, idx)

class SmartList(object):

 def __init__(self, parent=None, id=-1, *args, **kwargs):
  choices = kwargs.pop('choices', [])
  self.use_dataview = False
  if not self.use_dataview:
   self.control = VirtualCtrl(self, parent=parent, id=id, *args, **kwargs)
  else:
   self.control = dataview.DataViewListCtrl(parent=parent, id=id, style=wx.LC_REPORT)
  #somewhere to store our model objects
  self.models = []
  self.list_items = []
  self.index_map = {}
  self.columns = []
  self.add_items(choices)


 def set_columns(self, columns):
  self.columns = columns
  for index, column in enumerate(columns):
   if self.use_dataview:
    self.control.AppendTextColumn(column.title, width=column.width)
   else:
    self.control.InsertColumn(index, unicode(column.title), width=column.width)

 def get_columns_for(self, model):
  cols = []
  for c in self.columns:
   cols.append(c.get_model_value(model))
  return cols

 @freeze_and_thaw
 def add_items(self, items):
  if self.index_map is None:
   self._rebuild_index_map()
  for item in items:
   columns = self.get_columns_for(item)
   if self.use_dataview:
    self.control.AppendItem(columns)
   else:
    self.control.Append(columns)
   self.models.append(item)
   self.index_map[item] = len(self.models)-1

 def find_index_of_item(self, model):
  if self.index_map is None:
   self._rebuild_index_map()
  return self.index_map.get(model, None)

 def find_item_from_index(self, index):
  if len(self.models)-1 <= index:
   return None
  return self.models[index]

 def _rebuild_index_map(self):
  self.index_map = {}
  for i, model in enumerate(self.models):
   self.index_map[model] = i

 def clear(self):
  self.control.DeleteAllItems()
  self.index_map = None
  del self.models[:]

 def add_item(self, item):
  self.add_items((item,))

 append = add_item

 def delete_item(self, item):
  self.delete_items((item,))

 @freeze_and_thaw
 def delete_items(self, items):
  for item in items:
   self.control.DeleteItem(self.index_map[item])
   self.models.remove(item)
  self.index_map = None


 def get_selected_items(self):
  if self.use_dataview:
   yield self.find_item_from_index(self.control.GetSelectedRow())
  else:
   yield self.find_item_from_index(self.control.GetFirstSelected())
  for selection in xrange(1, self.control.GetSelectedItemCount()):
   yield self.find_item_from_index(self.control.GetNextSelected(selection))

 def get_selected_item(self):
  try:
   return self.get_selected_items().next()
  except StopIteration:
   return

 def get_selected_index(self):
  if self.use_dataview:
   return self.control.GetSelectedRow()
  else:
   return self.control.GetFirstSelected()

 def select_model(self, item):
  index = self.find_index_of_item(item)
  if self.use_dataview:
   self.control.SelectRow(index)
  else:
   self.control.Select(index)
   self.control.Focus(index)

 def set_selected_index(self, index):
  if self.use_dataview:
   return self.control.SelectRow(index)
  else:
   return self.control.Select(index)

 def insert_item(self, index, item):
  columns = self.get_columns_for(item)
  if self.use_dataview:
   self.control.InsertItem(index, columns)
  else:
   self.control.InsertStringItem(index, columns[0])
   for i, col in enumerate(columns[1:]):
    self.control.SetStringItem(index, i+1, col)
  self.index_map = None
  self.models.insert(index, item)

 def update_item(self, item):
  index = self.find_index_of_item(item)
  for i, col in enumerate(self.get_columns_for(item)):
   self.control.SetStringItem(index, i, col)

 def update_models(self, models):
  if self.index_map is None:
   self._rebuild_index_map()
  for model in models:
   if model in self.index_map:
    self.update_item(model)
   else:
    self.add_item(model)

class VirtualSmartList(SmartList):


 def __init__(self, get_virtual_item=None, update_cache=None, *args, **kwargs):
  if get_virtual_item is None:
   raise RuntimeError, 'get_virtual_item cannot be None'
  if update_cache is None:
   raise RuntimeError, 'update_cache cannot be None'

  kwargs['style'] = kwargs.get('style', 0)|wx.LC_VIRTUAL
  super(VirtualSmartList, self).__init__(*args, **kwargs)
  self.get_virtual_item = get_virtual_item
  if update_cache is not None:
   self.control.Bind(wx.EVT_LIST_CACHE_HINT, self.handle_cache)
  self.caching_from = 0
  self.caching_to = 0
  self.update_cache = update_cache

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

class Column(object):

 def __init__(self, title=None, width=-1, model_field=None):
  self.title = title
  self.model_field = model_field
  self.width = width

 def get_model_value(self, model):
  if self.model_field is None:
   return
  if callable(self.model_field):
   return unicode(self.model_field(model))
  value = getattr(model, self.model_field)
  if callable(value):
   value = value()
  return unicode(value)
