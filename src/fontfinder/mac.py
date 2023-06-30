from ctypes import c_bool, c_char_p, c_long, c_uint32, c_void_p, CFUNCTYPE, create_string_buffer
import ctypes.util
import platform
from pprint import pprint

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
    font_dict = {}
    for i in range(font_array_len):
        font_descriptor = cf.CFArrayGetValueAtIndex(font_array, i)

        family_cfstr = ct.CTFontDescriptorCopyAttribute(font_descriptor, ct.kCTFontFamilyNameAttribute)
        family_name = cf.cf_string_ref_to_python_str(family_cfstr)
        cf.CFRelease(family_cfstr)

        style_cfstr = ct.CTFontDescriptorCopyAttribute(font_descriptor, ct.kCTFontStyleNameAttribute)
        style_name = cf.cf_string_ref_to_python_str(style_cfstr)
        cf.CFRelease(style_cfstr)

        display_cfstr = ct.CTFontDescriptorCopyAttribute(font_descriptor, ct.kCTFontDisplayNameAttribute)
        display_name = cf.cf_string_ref_to_python_str(display_cfstr)
        cf.CFRelease(display_cfstr)

        postscript_cfstr = ct.CTFontDescriptorCopyAttribute(font_descriptor, ct.kCTFontNameAttribute)
        postscript_name = cf.cf_string_ref_to_python_str(postscript_cfstr)
        cf.CFRelease(postscript_cfstr)

        if family_name not in font_dict:
            font_dict[family_name] = {}
        
        font_dict[family_name][style_name] = postscript_name

    cf.CFRelease(font_array)
    cf.CFRelease(font_collection)

    pprint(font_dict)


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

        self.CFRelease = self.prototype(
            None, "CFRelease", (self.IN, c_void_p, "cf_object"))

        self.CFArrayGetCount = self.prototype(
            c_long, "CFArrayGetCount", (self.IN, c_void_p, "cf_array"))

        self.CFArrayGetValueAtIndex = self.prototype(
            c_void_p, "CFArrayGetValueAtIndex", (self.IN, c_void_p, "cf_array"), (self.IN, c_long, "index"))

        self.CFStringGetMaximumSizeForEncoding = self.prototype(
            c_long, "CFStringGetMaximumSizeForEncoding", (self.IN, c_long, "length"), (self.IN, c_uint32, "encoding"))

        self.CFStringGetLength = self.prototype(
            c_long, "CFStringGetLength", (self.IN, c_void_p, "the_string"))

        self.CFStringGetCString = self.prototype(
            c_bool, "CFStringGetCString", (self.IN, c_void_p, "the_string"),
                                          (self.IN, c_char_p, "buffer"),
                                          (self.IN, c_long,   "buffer_size"),
                                          (self.IN, c_uint32, "encoding")
        )

        self.kCFStringEncodingUTF8 = c_uint32(0x08000100)

    def cf_string_ref_to_python_str(self, cf_string_ref: c_void_p):
        cf_str_len = self.CFStringGetLength(cf_string_ref)
        buffer_size = self.CFStringGetMaximumSizeForEncoding(cf_str_len, self.kCFStringEncodingUTF8)
        buffer = create_string_buffer(buffer_size)
        success = self.CFStringGetCString(cf_string_ref, buffer, buffer_size, self.kCFStringEncodingUTF8)
        if not success:
            raise Exception("Couldn't encode string as UTF-8 into buffer")
        python_str = buffer.raw.strip(b'\x00').decode(encoding='utf-8')
        return python_str


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

        self.kCTFontFamilyNameAttribute = c_void_p.in_dll(self.lib, "kCTFontFamilyNameAttribute")
        self.kCTFontStyleNameAttribute = c_void_p.in_dll(self.lib, "kCTFontStyleNameAttribute")
        self.kCTFontDisplayNameAttribute = c_void_p.in_dll(self.lib, "kCTFontDisplayNameAttribute")
        self.kCTFontNameAttribute = c_void_p.in_dll(self.lib, "kCTFontNameAttribute")
