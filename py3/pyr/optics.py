"""common look and feel for error messages"""
# code must be compatible across all supported Python versions

import inspect
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

error_prefix = sys.argv[0] + " error: "
def print_error(message, *rest):
    message = error_prefix + str(message)
    if rest:
        message += " " + " ".join(str(x) for x in rest)
    message += "\n"
    sys.stderr.write(message)

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
    if not value:
        raise missing_value(name)
    if not all(c in "0123456789" for c in value):
        raise Exit("usage", "expected (non-negative) integer for option " + name)
    return int(value)

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

def existing_path(name, value):
    if not value:
        raise missing_value(name)
    if not os.path.exists(value):
        raise Exit("noinput", "no such path: " + value)
    return pathlib.Path(value)
def existing_filename(name, value):
    if not value:
        raise missing_value(name)
    if not os.path.exists(value):
        raise Exit("noinput", "no such path: " + value)
    if not os.path.isfile(value):
        raise Exit("noinput", "not a file: " + value)
    return pathlib.Path(value)
def existing_dir(name, value):
    if not value:
        raise missing_value(name)
    if not os.path.exists(value):
        raise Exit("noinput", "no such path: " + value)
    if not os.path.isdir(value):
        raise Exit("noinput", "not a directory: " + value)
    return pathlib.Path(value)

def pure_path(name, value):
    if not value:
        raise missing_value(name)
    return pathlib.PurePath(value)
def path(name, value):
    if not value:
        raise missing_value(name)
    return pathlib.Path(value)


def parse_opts(opts, opt_map, out=None):
    """parse options through functions from opt_map

    If out is None, it becomes a new dict.

    For each (name, raw) in opts, depending on opt_map.get(name) as X:
    * function: out[name] = X(name, raw, out.get(name))
    * tuple of (other, func): out[other] = func(name, raw, out.get(other))
    * str: out[X] = opt_map[X](name, raw, out.get(X))
    * None: raise unknown_option(name)

    For every call above, if len(inspect.getargspec(func).args) == 2, then func will be called with 2 parameters instead of 3.

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
        if len(inspect.getargspec(f).args) == 2:
            out[target] = f(name, value)
        else:
            out[target] = f(name, value, out.get(target))
    return out
