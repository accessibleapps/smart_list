"""Windows 8/10 UI Automation performance fix.

Windows 8/10 UIA implementation has a bug where it enumerates all items
in a virtual list by calling LVM_GETITEMCOUNT repeatedly. For large virtual
lists (e.g., 1 million items), this causes unacceptable delays.

This module uses IAT (Import Address Table) hooking to intercept SendMessageW
calls within uiautomationcore.dll and return 0 for LVM_GETITEMCOUNT queries,
preventing the enumeration without breaking accessibility.
"""
import platform

import resource_finder

is_windows = platform.system() == "Windows"
if is_windows:
    from ctypes import *
    from ctypes.wintypes import *

    import commctrl

    SendMessageW = windll.user32.SendMessageW

    callback_type = WINFUNCTYPE(c_int, c_int, c_int, c_int, c_int)

    @callback_type
    def callback_8(hwnd, msg, wParam, lParam):
        if msg == commctrl.LVM_GETITEMCOUNT:
            return 0
        return old_proc(hwnd, msg, wParam, lParam)

    @callback_type
    def callback_10(hwnd, msg, wParam, lParam):
        if msg == commctrl.LVM_GETITEMCOUNT:
            return 0
        return SendMessageW(hwnd, msg, wParam, lParam)


def install_iat_hook():
    """Install IAT hook to fix Windows 8/10 virtual list performance.

    Patches SendMessageW in uiautomationcore.dll to intercept and suppress
    LVM_GETITEMCOUNT queries that would enumerate all virtual list items.

    Uses architecture-specific DLL (iat_hook32.dll or iat_hook64.dll).
    Windows 8 and 10+ require different hooking strategies.
    """
    global old_proc
    arch = platform.architecture()[0][:2]
    iat_hook_path = resource_finder.find_application_resource(
        "iat_hook{arch}.dll".format(arch=arch)
    )
    iat_hook = cdll[iat_hook_path]
    uiacore = windll.kernel32.LoadLibraryA("uiautomationcore.dll")
    if uiacore != 0:
        old_proc = callback_type()
        if platform.release() == "8":
            iat_hook.PatchIat(
                uiacore, "user32.dll", "SendMessageW", callback_8, pointer(old_proc)
            )
        else:
            iat_hook.PatchDelayedIat(
                uiacore,
                "ext-ms-win-rtcore-ntuser-window-ext-l1-1-0.dll",
                "SendMessageW",
                callback_10,
                pointer(old_proc),
            )
