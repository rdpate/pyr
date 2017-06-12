import string
import sys


def show(opts, args):
    """example from readme.md"""
    print(sys.argv)
    print(opts)
    print(args)


def showargs(opts, args):
    for name, value in opts:
        s = "option " + name
        if value is not None:
            s += ": " + value
        print(s)
    for n, x in enumerate(args, start=1):
        print("{:3d} {}".format(n, x))


SAFE_CHARS = set(string.ascii_letters + string.digits + "-_=+:,./")
def reconstruct(opts, args):
    def q(s):
        if all(c in SAFE_CHARS for c in s):
            return s
        # TODO: what about non-printables, including controls?
        return "'" + s.replace("'", "'\\''") + "'"
    argv = [sys.argv[0]]
    for n, v in opts:
        if len(n) == 1 and v is not None:
            argv.append("-" + n + v)
        elif v is None:
            argv.append("--" + n)
        else:
            argv.append("--{}={}".format(n, v))
    if args and args[0].startswith("-") and args[0] != "-":
        argv.append("--")
    argv.extend(args)
    argv = " ".join(map(q, argv))
    print(argv)


# TODO: cleanup and reorganize all following
# maybe move into pyr.optics module (common "look"/optics for error messages)

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
    #
    "sighup":      129,
    "sigint":      130,
    "sigpipe":     141,
    "sigterm":     143,
    }

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
class ExpectedUsage(Exit):
    """Print a different error message showing args as expected arguments"""
    def __init__(self, args):
        Exit.__init__(self, "usage", args)

def any_string(name, value, prev):
    """require_string that allows empty strings"""
    return value or ""
def require_string(name, value, prev):
    if not value:
        raise missing_value(name)
    return value

def no_value(name, value, prev):
    if value is not None:
        raise unexpected_value(name)
    return True
def no_value_false(name, value, prev):
    if value is not None:
        raise unexpected_value(name)
    return False

def require_int(name, value, prev):
    if not value:
        raise missing_value(name)
    if value.startswith("-"):
        rest = value[1:]
    else:
        rest = value
    if not all(c in "0123456789" for c in rest):
        raise Exit("usage", "expected integer for option " + name)
    return int(value)
def require_nonneg_int(name, value, prev):
    if not value:
        raise missing_value(name)
    if not all(c in "0123456789" for c in value):
        raise Exit("usage", "expected (non-negative) integer for option " + name)
    return int(value)

def parse_opts(opts, opt_map, start=None):
    out = {} if start is None else start
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
            assert not isinstance(f, str), f
        else:
            target = name
        out[target] = f(name, value, out.get(target))
    return out

def head(opts, args):
    opt_map = {
        "n": "lines",
        "lines": require_nonneg_int,
        }
    def shortcut_int(name, value, prev):
        return require_nonneg_int(name, name + (value or ""), prev)
    for x in "123456789":
        opt_map[x] = ("lines", shortcut_int)
    lines = parse_opts(opts, opt_map).get("lines", 10)

    if not args:
        args = ["-"]
    for filename in args:
        if filename == "-":
            f = sys.stdin
        else:
            f = open(filename)
        if len(args) > 1:
            print("==> {} <==".format(filename))
        for n, line in enumerate(f, start=1):
            sys.stdout.write(line)
            if n == lines:
                break
