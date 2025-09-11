import platform
from logging import getLogger

import wx

logger = getLogger("smart_list.unified_list")
try:
    unicode
except NameError:
    unicode = str


try:
    from wx import dataview
except ImportError:
    dataview = None


is_mac = platform.system() == "Darwin"

""" Unified List
"""


class UnifiedList(object):
    """Provides a standard abstraction over a ListView and DataView

    Since a WX ListView is not accesible on Mac and a DataView is, this class does its best to provide the same interface for both
    """

    def __init__(self, parent=None, id=None, parent_obj=None, *args, **kwargs):
        self.use_dataview = is_mac
        if self.use_dataview and dataview is None:
            raise RuntimeError("wx.dataview required and not available")
        self.virtual = kwargs.get("style", 0) & wx.LC_VIRTUAL
        if not self.use_dataview:
            kwargs["style"] = kwargs.get("style", 0) | wx.LC_REPORT
            self.control = VirtualCtrl(
                parent_obj=parent_obj, parent=parent, id=id, *args, **kwargs
            )
        else:
            kwargs = kwargs.copy()
            if "style" in kwargs:
                del kwargs["style"]
            if "name" in kwargs:
                del kwargs["name"]
            if self.virtual:
                self.control = dataview.DataViewCtrl(
                    parent=parent, id=id, *args, **kwargs
                )
                self.wx_model = VirtualDataViewModel(parent_obj)
                self.control.AssociateModel(self.wx_model)
            else:
                self.control = dataview.DataViewListCtrl(
                    parent=parent, id=id, *args, **kwargs
                )
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
                self.SetColumnText(index, i + 1, col)

    def SetColumnText(self, index, column, text):
        if self.use_dataview:
            self.control.SetTextValue(text, index, column)
        else:
            self.control.SetStringItem(index, column, text)

    def GetColumnText(self, index, column):
        if self.use_dataview:
            return self.control.GetTextValue(index, column)
        else:
            return self.control.GetItem(index, column).GetText()

    def Freeze(self):
        self.control.Freeze()

    def Thaw(self):
        self.control.Thaw()

    def CanAcceptFocus(self):
        return self.control.CanAcceptFocus()

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
                self.control.AppendTextColumn(
                    unicode(title),
                    width=width,
                    model_column=len(self.wx_model.columns) - 1,
                )
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
        for selection in range(1, self.control.GetSelectedItemCount()):
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
            if index <= self.GetItemCount() - 1:
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


if dataview is not None:

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
            res = ""
            try:
                res = self.parent.OnGetItemText(row, col)
            except Exception as e:
                logger.exception("Error retrieving row %r col %r" % (row, col))
                raise
            if res is None:
                res = ""
            return res


class VirtualCtrl(wx.ListCtrl):
    def __init__(self, parent_obj=None, *args, **kwargs):
        super(VirtualCtrl, self).__init__(*args, **kwargs)
        self.parent = parent_obj

    def OnGetItemText(self, idx, col):
        return self.parent.OnGetItemText(idx, col)
