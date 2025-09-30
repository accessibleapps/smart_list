# Smart List

Model-based list control for wxPython with virtual scrolling support for large datasets.

## Features

- **Model-based**: Display any Python object (classes, dicts, dataclasses)
- **Virtual lists**: Handle millions of items without loading into memory
- **Cross-platform**: Automatic ListView (Windows/Linux) or DataView (macOS)
- **Flexible columns**: Extract values via attributes, dict keys, or callables
- **Performance optimized**: Windows IAT hooking prevents UIA enumeration delays

## Installation

```bash
uv add smart_list
# or
pip install smart_list
```

## Usage

### Basic List

For datasets that fit in memory (< 10K items):

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

For large datasets (> 10K items) or database-backed data:

```python
from smart_list import VirtualSmartList, Column

class MyFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, size=(400, 300))
        panel = wx.Panel(self)

        # Example: Database with 1 million rows
        def get_item(index):
            return db.query("SELECT * FROM users LIMIT 1 OFFSET ?", index)

        def load_batch(start, end):
            # Optional: batch loading for performance
            return db.query("SELECT * FROM users LIMIT ? OFFSET ?", end - start + 1, start)

        self.list = VirtualSmartList(
            parent=panel,
            style=wx.LC_REPORT,
            get_virtual_item=get_item,
            update_cache=load_batch  # Optional but recommended
        )
        self.list.set_columns([
            Column(title="ID", model_field="id"),
            Column(title="Name", model_field="name"),
            Column(title="Email", model_field="email")
        ])
        self.list.update_count(1000000)  # Total rows
        self.Show()
```

**Virtual list requirements:**
- Provide `get_virtual_item(index)` callback
- Call `update_count(n)` with total items
- Optionally provide `update_cache(start, end)` for batch loading

## Column Field Resolution

Columns extract values using three strategies:

```python
# 1. Attribute access
Column(title="Name", model_field="name")  # obj.name

# 2. Dict key access
Column(title="Email", model_field="email")  # obj["email"]

# 3. Callable
Column(title="Full Name", model_field=lambda p: f"{p.first} {p.last}")
Column(title="Age", model_field=lambda p: datetime.now().year - p.birth_year)
```

Resolution order: callable → attribute → dict key

## API Reference

### SmartList

| Method | Description |
|--------|-------------|
| `set_columns(columns)` | Configure column definitions |
| `add_items(items)` | Add multiple items (uses freeze/thaw) |
| `add_item(item)` | Add single item |
| `get_items()` | Return all model objects |
| `update_models(models)` | Update or add models, refresh display |
| `insert_item(index, item)` | Insert at specific position |
| `delete_item(item)` | Remove item by value |
| `update_item(item)` | Refresh single item display |
| `get_selected_items()` | Iterator of selected models |
| `get_selected_item()` | First selected model or None |
| `select_model(item)` | Select item by value |
| `find_index_of_item(model)` | Get list index for model |
| `clear()` | Remove all items |

### VirtualSmartList

Inherits SmartList methods plus:

| Method | Description |
|--------|-------------|
| `update_count(count)` | Set total number of virtual items |
| `refresh()` | Refresh display and clear cache |
| `find_index_of_item(item)` | Linear search for item (O(n)) |

**Constructor requirements:**
- `get_virtual_item(index)`: Required callback returning model for index
- `update_cache(from_row, to_row)`: Optional batch loader returning list of models

### Column

```python
Column(title="Header", model_field="field", width=100)
```

| Parameter | Description |
|-----------|-------------|
| `title` | Column header text |
| `model_field` | Field name (str) or callable for extracting values |
| `width` | Column width in pixels (-1 for auto) |

## Performance Considerations

### When to Use Virtual Lists

| Scenario | Use | Reason |
|----------|-----|--------|
| < 10K items in memory | `SmartList` | Simple, full API |
| > 10K items | `VirtualSmartList` | Memory efficient |
| Database-backed | `VirtualSmartList` | Load on demand |
| Frequent add/remove | `SmartList` | O(1) index lookup |
| Read-only large dataset | `VirtualSmartList` | No memory overhead |

### Bulk Operations

Use `add_items()` instead of multiple `add_item()` calls. The freeze/thaw decorator prevents UI flicker:

```python
# Good: Single batch
list.add_items(1000_items)

# Bad: 1000 separate updates
for item in items:
    list.add_item(item)
```

### Windows Performance

On Windows 8/10, the library automatically installs an IAT hook to fix a UIA bug that enumerates all virtual list items. Without this fix, virtual lists with > 100K items experience multi-second delays.

## Platform Differences

The library provides a unified API but uses different underlying controls:

| Platform | Control | Reason |
|----------|---------|--------|
| macOS | DataView | Required for accessibility |
| Windows | ListView | Better performance |
| Linux | ListView | Better performance |

Code using SmartList works identically on all platforms.

## Requirements

- wxPython (>= 4.0)
- frozendict
- resource_finder
- pywin32 (Windows only, for IAT hooking)