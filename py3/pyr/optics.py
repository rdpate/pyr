"""common look and feel for error messages"""
# code must be compatible across all supported Python versions

import inspect
import os
import signal
import sys

try:
    import pathlib
except ImportError:
    class pathlib(object):
        @staticmethod
        def PurePath(v):
            return v
        Path = PurePath

_other_prefix = os.path.basename(sys.argv[0])
_error_prefix = _other_prefix + " error:"
_other_prefix += ":"
def _clean(x):
    return str(x).replace("\n", " ")
def _print(prefix, message):
    if not message:
        raise ValueError("empty message")
    parts = [prefix]
    parts.extend(_clean(x) for x in message)
    parts[-1] += "\n"
    sys.stderr.write(" ".join(parts))
def print_error(*message):
    """print message with a command error prefix to stderr"""
    _print(_error_prefix, message)
def print_warning(*message):
    """print message with a command prefix to stderr"""
    _print(_other_prefix, message)

exit_codes = {
    "other":         1,
    # freebsd: man sysexits
    "usage":        64,
    "dataerr":      65,
    "noinput":      66,
    "nouser":       67,
    "nohost":       68,
    "unavailable":  69,
    "software":     70,
    "oserr":        71,
    "osfile":       72,
    "cantcreat":    73,
    "cantcreate":   73,
    "ioerr":        74,
    "tempfail":     75,
    "protocol":     76,
    "noperm":       77,
    "config":       78,
    }
def _add_signals():
    for name, value in signal.__dict__.items():
        if name.startswith("SIG") and not name.startswith("SIG_"):
            exit_codes[name.lower()] = 128 + int(value)
_add_signals()

class Exit(SystemExit):
    """SystemExit with a specific code and a string message"""
    def __init__(self, code, message=None):
        """code is an integer or exit_codes key"""
        if not isinstance(code, int):
            code = exit_codes[code]
        SystemExit.__init__(self, code)
        self.message = message

def internal_error(message="internal error"):
    return Exit("software", message)

def unknown_option(name):
    return Exit("usage", "unknown option " + name)
def missing_value(name):
    return Exit("usage", "missing value for option " + name)
def unexpected_value(name):
    return Exit("usage", "unexpected value for option " + name)

def unknown_args():
    return Exit("usage", "unknown arguments")
def missing_arg(name):
    return Exit("usage", "missing expected argument " + name)
def missing_args(*names):
    return Exit("usage", "missing expected arguments " + " ".join(names))
def unknown_extra_args(count):
    message = "{} unknown extra argument{}".format(count, "s" if count != 1 else "")
    return Exit("usage", message)


def any_string(name, value):
    return value or ""
def nonempty_string(name, value):
    if not value:
        raise missing_value(name)
    return value

def store_true(name, value):
    if value is not None:
        raise unexpected_value(name)
    return True
def store_false(name, value):
    if value is not None:
        raise unexpected_value(name)
    return False

def integer(name, value):
    """allow any base 10 integer"""
    if not value:
        raise missing_value(name)
    if value.startswith("-"):
        rest = value[1:]
    else:
        rest = value
    if not all(c in "0123456789" for c in rest):
        raise Exit("usage", "expected integer for option " + name)
    return int(value)
def nonneg_int(name, value):
    """allow zero and positive base 10 integers"""
    if not value:
        raise missing_value(name)
    if not all(c in "0123456789" for c in value):
        raise Exit("usage", "expected non-negative integer for option " + name)
    return int(value)
def pos_int(name, value):
    """allow positive base 10 integers"""
    if not value:
        raise missing_value(name)
    if not all(c in "0123456789" for c in value):
        raise Exit("usage", "expected positive integer for option " + name)
    value = int(value)
    if value == 0:
        raise Exit("usage", "expected positive integer for option " + name)
    return value

def raw_list(name, value, prev):
    """create list of raw values"""
    if prev is None:
        prev = []
    prev.append(value)
    return prev
def list_of(function):
    """create list of function(name, value, None)"""
    def f(name, value, prev):
        if prev is None:
            prev = []
        prev.append(function(name, value, None))
        return prev
    return f

def default(default, function):
    """use default for missing value, otherwise call function

    Implements "--N[=V]" and "-N[V]".  Note difference from "--N=[V]".
    """
    if _needs_prev(function):
        def f(name, value, prev):
            if value is None:
                return default
            return function(name, value, prev)
    else:
        def f(name, value):
            if value is None:
                return default
            return function(name, value)
    return f

def _set_attr(target):
    def decorate(f):
        setattr(target, f.__name__, f)
        return f
    return decorate
def _path_attrs(f):
    @_set_attr(f)
    def absolute(name, value):
        value = f(name, value)
        return value.absolute()
    @_set_attr(f)
    def resolve(name, value):
        value = f(name, value)
        return value.resolve()
    @_set_attr(f)
    def exists(name, value):
        p = f(name, value)
        if not p.exists():
            raise Exit("noinput", "no such path: " + value)
        return value
    return f
@_path_attrs
def path(name, value):
    if not value:
        raise missing_value(name)
    return pathlib.Path(value)
@_path_attrs
def filename(name, value):
    p = path(name, value)
    if p.exists() and not p.is_file():
        raise Exit("noinput", "not a file: " + value)
    return p
@_path_attrs
def directory(name, value):
    p = path(name, value)
    if p.exists() and not p.is_dir():
        raise Exit("noinput", "not a directory: " + value)
    return p
@_path_attrs
def command(name, value):
    """filename.exists if "/" in value, else search os.environ["PATH"]

    Does NOT check if file is executable.
    """
    if not value:
        raise missing_value(name)
    if "/" in value:
        return filename.exists(name, value)
    x = os.environ.get("PATH")
    if x is None:
        raise Exit("noinput", "cannot lookup command without PATH: " + value)
    for x in x.split(":"):
        x = pathlib.Path(x, value)
        if x.exists():
            return x
    raise Exit("noinput", "no such command: " + value)

def pure_path(name, value):
    if not value:
        raise missing_value(name)
    return pathlib.PurePath(value)

def _needs_prev(f):
    return len(inspect.getargspec(f).args) != 2

class OptionAttrs:
    """use attributes instead of items with parse_opts"""
    def __getitem__(self, key):
        return getattr(self, key.replace("-", "_"), None)
    def __setitem__(self, key, value):
        setattr(self, key.replace("-", "_"), value)

def parse_opts(opts, opt_map, out=None):
    """parse options through functions from opt_map

    If out is None, it becomes a new dict.

    For each (name, raw) in opts, depending on opt_map.get(name) as X:
    * function: out[name] = X(name, raw, out[name])
    * tuple of (other, func): out[other] = func(name, raw, out[other])
    * str: out[X] = opt_map[X](name, raw, out[X])
    * None: raise unknown_option(name)

    For every call above:
    * if len(inspect.getargspec(func).args) == 2, then the third parameter will be elided
    * else if out[...] raises KeyError, then None will be used instead

    That functions can use the previous value but not access other options' values is intentional.
    """
    if out is None:
        out = {}
    for name, value in opts:
        f = opt_map.get(name)
        if f is None:
            raise unknown_option(name)
        if isinstance(f, tuple):
            target = f[0]
            f = f[1]
        elif isinstance(f, str):
            target = f
            f = opt_map[f]
        else:
            target = name
        assert callable(f), f
        if _needs_prev(f):
            try:
                prev = out[target]
            except KeyError:
                prev = None
            out[target] = f(name, value, prev)
        else:
            out[target] = f(name, value)
    return out
