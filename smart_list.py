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


 def set_columns(self, columns):
  self.columns = columns
  for index, column in enumerate(columns):
   if self.use_dataview:
    self.control.AppendTextColumn(column.title)
   else:
    self.control.InsertColumn(index, column.title, width=column.width)

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
   self.index_map[item] = len(self.models)

 def find_index_of_item(self, model):
  if self.index_map is None:
   self._rebuild_index_map()
  return self.index_map.get(model, None)

 def find_item_from_index(self):
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

 def select_item(self, item):
  index = self.find_index_of_item(item)
  if self.use_dataview:
   self.control.SelectRow(index)
  else:
   self.control.Select(index)

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

class VirtualSmartList(SmartList):


 def __init__(self, *args, **kwargs):
  kwargs['style'] = kwargs.get('style', 0)|wx.LC_VIRTUAL
  super(VirtualSmartList, self).__init__(*args, **kwargs)
  self.list_items = []

 @freeze_and_thaw
 def add_items(self, items):
  for item in items:
   columns = self.get_columns_for(item)
   self.list_items.append(columns)
   self.models.append(item)
   self.index_map[item] = len(self.models)
  self.control.SetItemCount(len(self.models))

 def update_item(self, item):
  index = self.find_index_of_item(item)
  for i, col in enumerate(self.get_columns_for(item)):
   self.list_items[index][i] = col
  self.control.RefreshItem(index)

 def delete_items(self, items):
  for item in items:
   index = self.find_index_of_item(item)
   self.models.remove(item)
   del self.list_items[index]
  self.index_map = None
  self.control.SetItemCount(len(self.models))

 def insert_item(self, index, item):
  columns = self.get_columns_for(item)
  self.index_map = None
  self.models.insert(index, item)
  self.list_items.insert(index, columns)
  self.control.SetItemCount(len(self.models))
  self.control.RefreshItems(0, len(self.list_items)-1)

 def OnGetItemText(self, item, col):
  return self.list_items[item][col]

class Column(object):

 def __init__(self, title, model_field, width):
  self.title = title
  self.model_field = model_field
  self.width = width

 def get_model_value(self, model):
  value = getattr(model, self.model_field)
  if callable(value):
   return value()
  return value
