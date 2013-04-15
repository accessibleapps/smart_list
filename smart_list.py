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

 def add_item(self, item):
  self.add_items((item,))

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
