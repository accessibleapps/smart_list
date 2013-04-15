import wx
from wx import dataview

class VirtualCtrl(wx.ListCtrl):

 def __init__(self, parent_obj, *args, **kwargs):
  super(VirtualCtrl, self).__init__(*args, **kwargs)
  self.parent = parent_obj

 def OnGetItemText(self, col, idx):
  return self.parent.OnGetItemText(col, idx)

class SmartList(object):

 def __init__(self, parent=None, id=-1):
  self.use_dataview = False
  if not self.use_dataview:
   self.control = VirtualCtrl(self, parent, id, style=wx.LC_REPORT)
  else:
   self.control = dataview.DataViewListCtrl(parent, id, style=wx.LC_REPORT)

  #somewhere to store our model objects
  self.models = []
  self.list_items = []
  self.index_map = {}

 def set_columns(self, columns):
  self.columns = columns
  for index, column in enumerate(columns):
   if self.use_dataview:
    self.control.AppendTextColumn(column.title)
   else:
    self.control.InsertColumn(index, column.title)

 def get_columns_for(self, model):
  cols = []
  for c in self.columns:
   cols.append(c.get_model_value(model))
  return cols

 def add_items(self, items):
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

 def _rebuild_index_map(self):
  self.index_map = {}
  for i, model in enumerate(self.models):
   self.index_map[model] = i

 def add_item(self, item):
  self.add_items((item,))

 append = add_item

 def delete_item(self, item):
  self.delete_items((item,))

 def delete_items(self, items):
  for item in items:
   self.control.DeleteItem(self.index_map[item])
   self.models.remove(item)
  self.index_map = None

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

 def OnGetItemText(self, item, col):
  return self.list_items[item][col]

class Column(object):

 def __init__(self, title, value_getter):
  self.title = title
  self.value_getter = value_getter

 def get_model_value(self, model):
  value = getattr(model, self.value_getter)
  if callable(value):
   return value()
  return value
