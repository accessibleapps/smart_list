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
   self.control = VirtualCtrl(self, parent, id, style=wx.LC_REPORT|wx.LC_VIRTUAL)
  else:
   self.control = dataview.DataViewListCtrl(parent, id, style=wx.LC_REPORT)

  #somewhere to store our model objects
  self.models = []
  self.list_items = []

 def set_columns(self, columns):
  self.columns = columns
  for i, c in enumerate(columns):
   if self.use_dataview:
    self.control.AppendTextColumn(c.title)
   else:
    self.control.InsertColumn(i, c.title)

 def add(self, model):
  self.models.append(model)

 def get_columns_for(self, model):
  cols = []
  for c in self.columns:
   cols.append(getattr(model, c.value_getter))
  return cols

 def refresh(self):
  for model in self.models:
   columns = self.get_columns_for(model)
   if self.use_dataview:
    self.control.AppendItem(columns)
   else:
    self.list_items.append(columns)
  self.control.SetItemCount(len(self.list_items))

 def OnGetItemText(self, item, col):
  return self.list_items[item][col]

class ColumnDef(object):

 def __init__(self, title, value_getter):
  self.title = title
  self.value_getter = value_getter
