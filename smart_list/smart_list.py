from __future__ import absolute_import

import logging

import wx

from . import iat_patch
from .unified_list import UnifiedList

try:
    unicode
except NameError:
    unicode = str

try:
    from collections.abc import Callable, MutableMapping, MutableSequence
except ImportError:
    from collections import Callable, MutableMapping, MutableSequence
import functools
import platform

from frozendict import frozendict

is_windows = platform.system() == "Windows"
logger = logging.getLogger(__name__)

if is_windows and platform.release() in {
    "8",
    "10",
}:
    try:
        iat_patch.install_iat_hook()
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
    for k, v in d.items():
        if isinstance(v, MutableMapping):
            d[k] = freeze_dict(v)
        if isinstance(v, MutableSequence):
            d[k] = freeze_list(v)
    return frozendict(d)


def freeze_list(l):
    for n, i in enumerate(l):
        if isinstance(i, MutableSequence):
            l[n] = freeze_list(i)
        if isinstance(i, MutableMapping):
            l[n] = freeze_dict(i)
    return tuple(l)


class SmartList(object):
    def __init__(self, parent=None, id=-1, *args, **kwargs):
        choices = kwargs.pop("choices", [])
        self.control = UnifiedList(
            parent_obj=self, parent=parent, id=id, *args, **kwargs
        )
        # somewhere to store our model objects
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
            if isinstance(item, MutableMapping):
                item = freeze_dict(item)
            self.index_map[item] = len(self.models) - 1

    def find_index_of_item(self, model):
        if self.index_map is None:
            self._rebuild_index_map()
        if isinstance(model, dict):
            model = freeze_dict(model)
        index = self.index_map.get(model)
        if index is None:
            raise ValueError("Unable to find index of item %r " % model)
        return index

    def find_item_from_index(self, index):
        if len(self.models) <= index:
            return None
        return self.models[index]

    def _rebuild_index_map(self):
        self.index_map = {}
        for i, model in enumerate(self.models):
            if isinstance(model, dict) or isinstance(model, MutableMapping):
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
            if isinstance(item, MutableMapping):
                item = freeze_dict(item)
            self.models.remove(item)
            self.control.Delete(self.index_map[item])
        self.index_map = None

    def get_selected_items(self):
        for item in self.control.GetSelectedItems():
            yield self.find_item_from_index(item)

    def get_selected_item(self):
        try:
            return next(self.get_selected_items())
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
            # Updating column 0 causes the entire row to be read, so only do it if needed
            if i == 0 and self.control.GetColumnText(index, i) == c:
                continue
            self.control.SetColumnText(index, i, c)

        self.models[index] = item
        if self.index_map is not None:
            del self.index_map[original]
            self.index_map[item] = index

    def freeze_item(self, item):
        if isinstance(item, MutableMapping):
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

    def CanAcceptFocus(self):
        return self.control.CanAcceptFocus()


class VirtualSmartList(SmartList):
    allowed_navigation_keys = [
        getattr(wx, "WXK_%s" % key.upper())
        for key in "up down left right home end pageup pagedown space return f4".split()
    ]

    def __init__(self, get_virtual_item=None, update_cache=None, *args, **kwargs):
        if get_virtual_item is None:
            raise RuntimeError("get_virtual_item cannot be None")

        kwargs["style"] = kwargs.get("style", 0) | wx.LC_VIRTUAL
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
        if (
            self.update_cache is not None
            and self.cache
            and self.caching_from <= item
            and self.caching_to >= item
        ):
            wanted = item - self.caching_from
            # print "from %d to %d wanted %d len %d" % (self.caching_from, self.caching_to, wanted, len(self.cache))
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
        self.control.RefreshItems(0, self.control.GetItemCount() - 1)
        self.cache = []
        self.caching_from = 0
        self.caching_to = 0

    def find_index_of_item(self, item):
        for i in range(self.control.GetItemCount()):
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
            return ""
        if is_callable(self.model_field):
            return unicode(self.model_field(model))
        try:
            value = getattr(model, self.model_field)
        except (AttributeError, TypeError):
            try:
                value = model[self.model_field]
            except (KeyError, TypeError):
                raise RuntimeError(
                    "Unable to find a %r attribute or key on model %r"
                    % (self.model_field, model)
                )
        if hasattr(value, "__unicode__"):
            return unicode(value)
        if is_callable(value):
            value = value()
        return unicode(value)


def is_callable(obj):
    return isinstance(obj, (Callable, classmethod, staticmethod))
