from ctypes import c_bool, c_char_p, c_long, c_uint32, c_void_p, CFUNCTYPE
import ctypes.util
import platform

import semver


def get_mac_system_fonts():
    if platform.system() != "Darwin":
        raise Exception("get_mac_system_fonts() should only be called under macOS")
    
    if semver.Version.parse(platform.mac_ver()[0]) < semver.Version(10.6):
        raise Exception("get_mac_system_fonts() only supported by macOS 10.6 or later")
    
    cf = CoreFoundationLibrary()
    ct = CoreTextLibrary()

    font_collection = ct.CTFontCollectionCreateFromAvailableFonts(None)
    font_array = ct.CTFontCollectionCreateMatchingFontDescriptors(font_collection)
    font_array_len = cf.CFArrayGetCount(font_array)
    for i in range(font_array_len):
        font_descriptor = cf.CFArrayGetValueAtIndex(font_array, i)
        attribute = ct.CTFontDescriptorCopyAttribute(font_descriptor, ct.kCTFontDisplayNameAttribute)

        cf.CFRelease(attribute)
    cf.CFRelease(font_array)
    cf.CFRelease(font_collection)


class CTypesLibrary:
    IN:  int    = 1
    OUT: int    = 2
    IN0: int    = 4

    def __init__(self, library_name: str, alt_pathname: str = None):
        '''`alt_pathname` is an alternative pathname to try if a library named `library_name` cannot be found.
        '''
        lib_pathname = ctypes.util.find_library("library_name")
        if lib_pathname is None:
            lib_pathname = alt_pathname
        self.lib = ctypes.cdll.LoadLibrary(lib_pathname)

    # Inspired by https://www.cs.unc.edu/~gb/blog/2007/02/11/ctypes-tricks/
    def prototype(self, result_type, func_name, *arg_items):
        '''
        Each arg_item should be
        (in_or_out_const, arg_type[, param_name_str[, default_value]])
        '''
        arg_types = []
        param_flags = []
        for arg_item in arg_items:
            arg_types.append(arg_item[1])
            param_flag = [arg_item[0]]
            if len(arg_item) > 2:
                param_flag.append(arg_item[2])
            if len(arg_item) > 3:
                param_flag.append(arg_item[3])
            param_flags.append(tuple(param_flag))
        return CFUNCTYPE(result_type, *arg_types)((func_name, self.lib), tuple(param_flags))

class CoreFoundationLibrary(CTypesLibrary):
    def __init__(self):
        super().__init__("CoreFoundation", "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        # Note hack for compatibility with macOS 11.0 and later
        # From: https://github.com/pyglet/pyglet/blob/a44e83a265e7df8ece793de865bcf3690f66adbd/pyglet/libs/darwin/cocoapy/cocoalibs.py#L10-L14

        self.CFArrayGetCount = self.prototype(
            c_long, "CFArrayGetCount", (self.IN, c_void_p, "cf_array"))

        self.CFArrayGetValueAtIndex = self.prototype(
            c_void_p, "CFArrayGetValueAtIndex", (self.IN, c_void_p, "cf_array"), (self.IN, c_long, "index"))

        self.CFRelease = self.prototype(
            None, "CFRelease", (self.IN, c_void_p, "cf_object"))

        self.kCFStringEncodingUTF8 = c_uint32(0x08000100)

class CoreTextLibrary(CTypesLibrary):
    def __init__(self):
        super().__init__("CoreText", "/System/Library/Frameworks/CoreText.framework/CoreText")
        # Note hack for compatibility with macOS greater or equals to 11.0.
        # From: https://github.com/pyglet/pyglet/blob/a44e83a265e7df8ece793de865bcf3690f66adbd/pyglet/libs/darwin/cocoapy/cocoalibs.py#L520-L524

        self.CTFontCollectionCreateFromAvailableFonts = self.prototype(
            c_void_p, "CTFontCollectionCreateFromAvailableFonts", (self.IN, c_void_p, "options"))

        self.CTFontCollectionCreateMatchingFontDescriptors = self.prototype(
            c_void_p, "CTFontCollectionCreateMatchingFontDescriptors", (self.IN, c_void_p, "font_collection"))
        
        self.CTFontDescriptorCopyAttribute = self.prototype(
            c_void_p, "CTFontDescriptorCopyAttribute", (self.IN, c_void_p, "font_descriptor"),
                                                       (self.IN, c_void_p, "attribute_name")
        )

        self.kCTFontDisplayNameAttribute = c_void_p.in_dll(self.lib, "kCTFontDisplayNameAttribute")