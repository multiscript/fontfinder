# Code in this module derived from FindSystemFontFilename project,
# under the MIT Licence:
# https://github.com/moi15moi/FindSystemFontsFilename/

from comtypes import COMError, GUID, HRESULT, IUnknown, STDMETHOD, WINFUNCTYPE
import ctypes
from ctypes import byref, create_unicode_buffer, POINTER, windll, wintypes
from enum import IntEnum
import platform
from sys import getwindowsversion
from typing import Set

from fontfinder.all_platforms import CTypesLibrary

def all_installed_families():
    if platform.system() != "Windows":
        raise Exception("fontfinder.mac.all_installed_families() should only be called under macOS")
    
    dw = DirectWriteLibrary()
    dw_factory = POINTER(IDWriteFactory)()
    dw.DWriteCreateFactory(dw.DWRITE_FACTORY_TYPE_ISOLATED, IDWriteFactory._iid_, byref(dw_factory))
    print(dw_factory)

    return []


class IDWriteFontList(IUnknown):
    # https://learn.microsoft.com/en-us/windows/win32/api/dwrite/nn-dwrite-idwritefontlist
    _iid_ = GUID("{1a0d8438-1d97-4ec1-aef9-a2fb86ed6acb}")
    _methods_ = [
        STDMETHOD(None, "GetFontCollection"),       # Not implemented here
        STDMETHOD(wintypes.UINT, "GetFontCount"),   # Not implemented here
        STDMETHOD(HRESULT, "GetFont"),              # Not implemented here
    ]


class IDWriteFontFamily(IDWriteFontList):
    # https://learn.microsoft.com/en-us/windows/win32/api/dwrite/nn-dwrite-idwritefontfamily
    _iid_ = GUID("{da20d8ef-812a-4c43-9802-62ec4abd7add}")
    _methods_ = [
        STDMETHOD(None, "GetFamilyNames"),          # Not implemented here
        STDMETHOD(None, "GetFirstMatchingFont"),    # Not implemented here
        STDMETHOD(None, "GetMatchingFonts"),        # Not implemented here
    ]

class IDWriteFontCollection(IUnknown):
    # https://learn.microsoft.com/en-us/windows/win32/api/dwrite/nn-dwrite-idwritefontcollection
    _iid_ = GUID("{a84cee02-3eea-4eee-a827-87c1a02a0fcc}")
    _methods_ = [
        STDMETHOD(wintypes.UINT, "GetFontFamilyCount"),
        STDMETHOD(HRESULT, "GetFontFamily", [wintypes.UINT, POINTER(POINTER(IDWriteFontFamily))]),
        STDMETHOD(None, "FindFamilyName"),          # Not implemented here
        STDMETHOD(None, "GetFontFromFontFace"),     # Not implemented here
    ]

class IDWriteFactory(IUnknown):
    # https://learn.microsoft.com/en-us/windows/win32/api/dwrite/nn-dwrite-idwritefactory
    _iid_ = GUID("{b859ee5a-d838-4b5b-a2e8-1adc7d93db48}")
    _methods_ = [
        STDMETHOD(HRESULT, "GetSystemFontCollection", [POINTER(POINTER(IDWriteFontCollection)), wintypes.BOOLEAN]),
        STDMETHOD(None, "CreateCustomFontCollection"),      # Not implemented here
        STDMETHOD(None, "RegisterFontCollectionLoader"),    # Not implemented here
        STDMETHOD(None, "UnregisterFontCollectionLoader"),  # Not implemented here
        STDMETHOD(None, "CreateFontFileReference"),         # Not implemented here
        STDMETHOD(None, "CreateCustomFontFileReference"),   # Not implemented here
        STDMETHOD(None, "CreateFontFace"),                  # Not implemented here
        STDMETHOD(None, "CreateRenderingParams"),           # Not implemented here
        STDMETHOD(None, "CreateMonitorRenderingParams"),    # Not implemented here
        STDMETHOD(None, "CreateCustomRenderingParams"),     # Not implemented here
        STDMETHOD(None, "RegisterFontFileLoader"),          # Not implemented here
        STDMETHOD(None, "UnregisterFontFileLoader"),        # Not implemented here
        STDMETHOD(None, "CreateTextFormat"),                # Not implemented here
        STDMETHOD(None, "CreateTypography"),                # Not implemented here
        STDMETHOD(None, "GetGdiInterop"),                   # Not implemented here
        STDMETHOD(None, "CreateTextLayout"),                # Not implemented here
        STDMETHOD(None, "CreateGdiCompatibleTextLayout"),   # Not implemented here
        STDMETHOD(None, "CreateEllipsisTrimmingSign"),      # Not implemented here
        STDMETHOD(None, "CreateTextAnalyzer"),              # Not implemented here
        STDMETHOD(None, "CreateNumberSubstitution"),        # Not implemented here
        STDMETHOD(None, "CreateGlyphRunAnalysis"),          # Not implemented here
    ]


class DirectWriteLibrary(CTypesLibrary):
    def __init__(self):
        super().__init__(ctypes.windll, "dwrite")

        # I couldn't make this work using the ctypes function protype technique, so we just use the 
        # standard foreign function attribute technique.
        self.DWriteCreateFactory = self.lib.DWriteCreateFactory
        self.DWriteCreateFactory.restype = HRESULT
        self.DWriteCreateFactory.argtypes = [wintypes.UINT, GUID, POINTER(POINTER(IUnknown))]

        self.DWRITE_FACTORY_TYPE_SHARED = 0
        self.DWRITE_FACTORY_TYPE_ISOLATED = 1
