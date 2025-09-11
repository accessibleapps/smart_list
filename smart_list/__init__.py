from __future__ import absolute_import

from .smart_list import Column, SmartList, VirtualSmartList


def find_datafiles():
    import os
    import platform

    if platform.system() != "Windows":
        return []
    import sys

    import smart_list

    path = os.path.join(smart_list.__path__[0])
    return [
        (
            "",
            [
                os.path.join(path, "iat_hook32.dll"),
                os.path.join(path, "iat_hook64.dll"),
            ],
        )
    ]
