import wx
import wx.stc
from smart_list import SmartList, Column, VirtualSmartList

class SampleModel(object):
 def __init__(self, title, desc):
  self.title = title
  self.desc = desc

models = []
for i in range(10):
 models.append(SampleModel(str(i), "desc for %d" % i))

class MyFrame(wx.Frame):
 def __init__(self, parent, title):
  super(MyFrame, self).__init__(parent, title=title, size=(500, 500))
  panel = wx.Panel(self, size=(500, 500))
  self.lst = VirtualSmartList(parent=panel, style=wx.LC_REPORT)
  self.lst.set_columns([Column("title", "title", 100),
Column("description", "desc", 200)])
  self.lst.add_items(models)
  self.button = wx.Button(parent=panel, label="test")
  self.button.Bind(wx.EVT_BUTTON, self.click)
  self.Show(True)

 def click(self, event):
  self.lst.insert_item(3, SampleModel('something', 'something else'))
  models[5].desc = 'x'
  self.lst.update_item(models[5])
  self.lst.delete_item(models[-1])

app = wx.App()
frame = MyFrame(None, "Smart List Test")
app.MainLoop()
