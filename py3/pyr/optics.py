"""common look and feel for error messages"""
# code must be compatible across all supported Python versions

import signal
import sys

if sys.version_info[0] == 2:
    class pathlib(object):
        @staticmethod
        def PurePath(v):
            return v
        Path = PurePath
else:
    import pathlib

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


# TODO: change function signature to use inspect module and only pass prev value parameter if function takes 3 args

def any_string(name, value, _):
    return value or ""
def nonempty_string(name, value, _):
    if not value:
        raise missing_value(name)
    return value

def store_true(name, value, _):
    if value is not None:
        raise unexpected_value(name)
    return True
def store_false(name, value, _):
    if value is not None:
        raise unexpected_value(name)
    return False

def integer(name, value, _):
    if not value:
        raise missing_value(name)
    if value.startswith("-"):
        rest = value[1:]
    else:
        rest = value
    if not all(c in "0123456789" for c in rest):
        raise Exit("usage", "expected integer for option " + name)
    return int(value)
def nonneg_int(name, value, _):
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

def existing_path(name, value, _):
    if not value:
        raise missing_value(name)
    if not os.path.exists(value):
        raise Exit("noinput", "no such path: " + value)
    return pathlib.Path(value)
def existing_filename(name, value, _):
    if not value:
        raise missing_value(name)
    if not os.path.exists(value):
        raise Exit("noinput", "no such path: " + value)
    if not os.path.isfile(value):
        raise Exit("noinput", "not a file: " + value)
    return pathlib.Path(value)
def existing_dir(name, value, _):
    if not value:
        raise missing_value(name)
    if not os.path.exists(value):
        raise Exit("noinput", "no such path: " + value)
    if not os.path.isdir(value):
        raise Exit("noinput", "not a directory: " + value)
    return pathlib.Path(value)

def pure_path(name, value, _):
    if not value:
        raise missing_value(name)
    return pathlib.PurePath(value)
def path(name, value, _):
    if not value:
        raise missing_value(name)
    return pathlib.Path(value)


def parse_opts(opts, opt_map, out=None):
    """parse_opts with functions from opt_map

    If out is None, it becomes a new dict.

    For each (name, raw) in opts, depending on opt_map.get(name) as X:
    * function: out[name] = function(name, raw, out.get(name))
    * tuple of (other, function): out[other] = function(name, raw, out.get(other))
    * str: out[X] = opt_map[X](name, raw, out.get(X))
    * None: raise unknown_option(name)

    That functions can use the previous (or None) value but not access other options' values is intentional.
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
        out[target] = f(name, value, out.get(target))
    return out
