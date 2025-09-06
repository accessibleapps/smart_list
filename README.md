# Smart List

wxPython smart list control with model-based data display and virtual scrolling.

## Features

- Cross-platform ListView/DataView abstraction
- Model-based data display with configurable columns
- Virtual lists for large datasets
- Windows performance optimizations (IAT hooking)
- Supports attributes, dict keys, and callables

## Installation

```bash
uv add smart_list
# or
pip install smart_list
```

## Usage

```python
import wx
from smart_list import SmartList, Column

class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

people = [Person("Alice", 30), Person("Bob", 25)]

class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Smart List", size=(400, 300))
        panel = wx.Panel(self)
        
        self.list = SmartList(parent=panel, style=wx.LC_REPORT)
        self.list.set_columns([
            Column(title="Name", model_field="name", width=150),
            Column(title="Age", model_field="age", width=100)
        ])
        self.list.add_items(people)
        self.Show()

app = wx.App()
MyFrame()
app.MainLoop()
```

### Virtual Lists

```python
from smart_list import VirtualSmartList

class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, size=(400, 300))
        panel = wx.Panel(self)
        
        self.data = [{"name": f"Item {i}", "value": i} for i in range(10000)]
        
        self.list = VirtualSmartList(
            parent=panel, style=wx.LC_REPORT,
            get_virtual_item=lambda i: self.data[i],
            update_cache=lambda start, end: self.data[start:end+1]
        )
        self.list.set_columns([
            Column(title="Name", model_field="name"),
            Column(title="Value", model_field="value")
        ])
        self.list.update_count(len(self.data))
        self.Show()
```

## API

### SmartList
- `set_columns(columns)`: Set column definitions
- `add_items(items)`: Add items to list
- `get_items()`: Get all model objects
- `update_models(models)`: Update all models and refresh
- `insert_item(index, item)`: Insert item at position
- `delete_item(item)`: Remove item
- `update_item(item)`: Update specific item

### VirtualSmartList
- Requires `get_virtual_item(index)` function
- Optional `update_cache(from_row, to_row)` for batch loading
- `update_count(count)`: Set total item count
- `refresh()`: Refresh display and clear cache
- `find_index_of_item(item)`: Find item index

### Column
- `title`: Header text
- `width`: Column width (-1 for auto)
- `model_field`: Attribute name, dict key, or callable

```python
Column(title="Name", model_field="name")
Column(title="Email", model_field="email") 
Column(title="Full", model_field=lambda p: f"{p.first} {p.last}")
```

## Requirements

- wxPython
- frozendict
- resource_finder
- pywin32 (Windows only)