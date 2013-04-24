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
 def get_item(self, row, col):
  return models[row]

 def __init__(self, parent, title):
  super(MyFrame, self).__init__(parent, title=title, size=(500, 500))
  panel = wx.Panel(self, size=(500, 500))
  self.lst = VirtualSmartList(parent=panel, style=wx.LC_REPORT, get_item=self.get_item)
  self.lst.set_columns([Column(title="title", model_field="title", width=100),
Column(title="description", model_field="desc", width=200)])
  self.lst.update_count(len(models))
  self.button = wx.Button(parent=panel, label="test")
  self.button.Bind(wx.EVT_BUTTON, self.click)
  self.Show(True)

 def click(self, event):
  #self.lst.insert_item(3, SampleModel('something', 'something else'))
  #models[5].desc = 'x'
  #self.lst.update_item(models[5])
  self.lst.update_models(models)
  #self.lst.delete_item(models[-1])

app = wx.App()
frame = MyFrame(None, "Smart List Test")
app.MainLoop()
