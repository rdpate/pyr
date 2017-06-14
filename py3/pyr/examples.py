import string
import sys

from . import optics


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


def head(opts, args):
    opt_map = {
        "n": "lines",
        "lines": optics.nonneg_int,
        }
    def shortcut_int(name, value):
        return optics.nonneg_int(name, name + (value or ""))
    for x in "123456789":
        opt_map[x] = ("lines", shortcut_int)
    lines = optics.parse_opts(opts, opt_map).get("lines", 10)

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
