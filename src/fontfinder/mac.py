import ctypes, ctypes.util
import platform

import semver

_core_foundation_lib = None
_core_text_lib = None

def get_mac_system_fonts():
    if platform.system() != "Darwin":
        raise Exception("get_mac_system_fonts() should only be called under macOS")
    
    if semver.Version.parse(platform.mac_ver()[0]) < semver.Version(10.6):
        raise Exception("get_mac_system_fonts() only supported by macOS 10.6 or later")
    
    load_libraries()

def load_libraries():
    global _core_foundation_lib, _core_text_lib

    core_foundation_pathname = ctypes.util.find_library("CoreFoundation")
    # Hack for compatibility with macOS 11.0 and later
    # From: https://github.com/pyglet/pyglet/blob/a44e83a265e7df8ece793de865bcf3690f66adbd/pyglet/libs/darwin/cocoapy/cocoalibs.py#L10-L14
    if core_foundation_pathname is None:
        core_foundation_pathname = "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
    _core_foundation_lib = ctypes.cdll.LoadLibrary(core_foundation_pathname)

    core_text_pathname = ctypes.util.find_library("CoreText")
    # Hack for compatibility with macOS greater or equals to 11.0.
    # From: https://github.com/pyglet/pyglet/blob/a44e83a265e7df8ece793de865bcf3690f66adbd/pyglet/libs/darwin/cocoapy/cocoalibs.py#L520-L524
    if core_text_pathname is None:
        core_text_pathname = "/System/Library/Frameworks/CoreText.framework/CoreText"
    _core_text_lib = ctypes.cdll.LoadLibrary(core_text_pathname)


