# The following comment should be removed at some point in the future.
# mypy: strict-optional=False

from __future__ import absolute_import

import os
import sys

from stickybeak.vendored.pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from typing import Optional, Tuple


def glibc_version_string():
    # type: () -> Optional[str]
    "Returns glibc version string, or None if not using glibc."
    return glibc_version_string_confstr() or glibc_version_string_ctypes()


def glibc_version_string_confstr():
    # type: () -> Optional[str]
    "Primary implementation of glibc_version_string using os.confstr."
    # os.confstr is quite a bit faster than ctypes.DLL. It's also less likely
    # to be broken or missing. This strategy is used in the standard library
    # platform module:
    # https://github.com/python/cpython/blob/fcf1d003bf4f0100c9d0921ff3d70e1127ca1b71/Lib/platform.py#L175-L183
    if sys.platform == "win32":
        return None
    try:
        # os.confstr("CS_GNU_LIBC_VERSION") returns a string like "glibc 2.17":
        _, version = os.confstr("CS_GNU_LIBC_VERSION").split()
    except (AttributeError, OSError, ValueError):
        # os.confstr() or CS_GNU_LIBC_VERSION not available (or a bad value)...
        return None
    return version


def glibc_version_string_ctypes():
    # type: () -> Optional[str]
    "Fallback implementation of glibc_version_string using ctypes."

    try:
        import ctypes
    except ImportError:
        return None

    # ctypes.CDLL(None) internally calls dlopen(NULL), and as the dlopen
    # manpage says, "If filename is NULL, then the returned handle is for the
    # main program". This way we can let the linker do the work to figure out
    # which libc our process is actually using.
    process_namespace = ctypes.CDLL(None)
    try:
        gnu_get_libc_version = process_namespace.gnu_get_libc_version
    except AttributeError:
        # Symbol doesn't exist -> therefore, we are not linked to
        # glibc.
        return None

    # Call gnu_get_libc_version, which returns a string like "2.5"
    gnu_get_libc_version.restype = ctypes.c_char_p
    version_str = gnu_get_libc_version()
    # py2 / py3 compatibility:
    if not isinstance(version_str, str):
        version_str = version_str.decode("ascii")

    return version_str


# platform.libc_ver regularly returns completely nonsensical glibc
# versions. E.g. on my computer, platform says:
#
#   ~$ python2.7 -c 'import platform; print(platform.libc_ver())'
#   ('glibc', '2.7')
#   ~$ python3.5 -c 'import platform; print(platform.libc_ver())'
#   ('glibc', '2.9')
#
# But the truth is:
#
#   ~$ ldd --version
#   ldd (Debian GLIBC 2.22-11) 2.22
#
# This is unfortunate, because it means that the linehaul data on libc
# versions that was generated by pip 8.1.2 and earlier is useless and
# misleading. Solution: instead of using platform, use our code that actually
# works.
def libc_ver():
    # type: () -> Tuple[str, str]
    """Try to determine the glibc version

    Returns a tuple of strings (lib, version) which default to empty strings
    in case the lookup fails.
    """
    glibc_version = glibc_version_string()
    if glibc_version is None:
        return ("", "")
    else:
        return ("glibc", glibc_version)