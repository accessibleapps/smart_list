import wx
import wx.stc
from smart_list import SmartList, ColumnDef

class SampleModel(object):
 def __init__(self, title, desc):
  self.title = title
  self.desc = desc

models = []
for i in range(10):
 models.append(SampleModel(str(i), "desc for %d" % i))

class MyFrame(wx.Frame):
 def __init__(self, parent, title):
  wx.Frame.__init__(self, parent, title=title, size=(500, 500))
  self.lst = SmartList(self)
  self.lst.set_columns([ColumnDef("title", "title"),
ColumnDef("description", "desc")])
  self.lst.add_items(models)
  self.Show(True)

app = wx.App()
frame = MyFrame(None, "styled text test")
app.MainLoop()
