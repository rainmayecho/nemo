import os

from cffi import FFI
from typing import Tuple

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
EXT_EXISTS = False
lib = None

def __build():
    try:
        from cffi import FFI
        ffi = FFI()
        ffi.cdef("unsigned long long lsb(unsigned long long v);")
        ffi.cdef("unsigned long long bb(unsigned long long v);")
        ffi.cdef("unsigned long popcnt(unsigned long);")
        ffi.cdef("int bitScanForward(unsigned long long bb);")
        # ffi.set_source("pyutils",'#include "utils.h"', sources=["utils.c"])
        # print(ffi.compile())
        lib = ffi.dlopen(f"{DIR_PATH}/pyutils.pypy37-pp73-darwin.so")
        EXT_EXISTS = lib is not None
        return EXT_EXISTS, lib
    except Exception as e:
        print(e)


def build_library() -> Tuple[bool, "CLib"]:
    return __build()