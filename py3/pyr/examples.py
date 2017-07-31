import string
import sys

from . import optics


_examples = []
def _example(f):
    _examples.append((f.__name__, f))
    return f

@_example
def main(opts, args):
    """ %

    List examples.

    Options:
        --sort          sort examples
    -s  --short         show help synopsis only
    """
    opt_map = {
        "sort": optics.store_true,
        "short": optics.store_true,
        "s": "short",
        }
    opts = optics.parse_opts(opts, opt_map)
    if args:
        raise optics.unknown_args()
    examples = _examples
    if opts.get("sort"):
        examples = sorted(examples)
    for name, f in examples:
        doc = f.__doc__
        if not doc:
            print(name)
        else:
            doc = doc.strip().splitlines()
            first = doc[0]
            assert first.startswith("%"), repr(first)
            if first.startswith("% "):
                first = first[2:]
                print(name + " " + first)
            else:
                assert first == "%", repr(first)
                print(name)
            if not opts.get("short") and len(doc) > 1:
                assert doc[1] == "", (name, doc[1])
                del doc[0:2]
                print("\n".join(doc))

@_example
def show(opts, args):
    """% [OPT..] [ARG..]

    (example from readme.md)
    """
    print(sys.argv)
    print(opts)
    print(args)


@_example
def showargs(opts, args):
    """% [OPT..] [ARG..]

    Show options and arguments.
    """
    for name, value in opts:
        s = "option " + name
        if value is not None:
            s += ": " + value
        print(s)
    for n, x in enumerate(args, start=1):
        print("{:3d} {}".format(n, x))


SQUOTE_SAFE_CHARS = set(string.ascii_letters + string.digits + "-_=+:,./")
def squote(s):
    if not s:
        return "''"
    if all(c in SQUOTE_SAFE_CHARS for c in s):
        return s
    return "'" + s.replace("'", "'\\''") + "'"
@_example
def reconstruct(opts, args):
    """% [OPT..] [ARG..]

    Reconstruct command line.
    """
    argv = [sys.argv[0]]
    for n, v in opts:
        if len(n) == 1:
            argv.append("-" + n)
            if v:
                argv[-1] += v
        elif v is None:
            argv.append("--" + n)
        else:
            argv.append("--{}={}".format(n, v))
    if args and args[0].startswith("-") and args[0] != "-":
        argv.append("--")
    argv.extend(args)
    argv = " ".join(map(squote, argv))
    print(argv)


@_example
def head(opts, args):
    """% [FILE..]

    Options:
    -nL --lines=L       show first L lines (default 10)
    -##                 --lines=## (where ## >= 0)
    """
    opt_map = {
        "n": "lines",
        "lines": optics.nonneg_int,
        }
    def shortcut_int(name, value):
        return optics.nonneg_int(name, name + (value or ""))
    for x in "0123456789":
        opt_map[x] = ("lines", shortcut_int)
    lines = optics.parse_opts(opts, opt_map).get("lines", 10)

    if not args:
        args = ["-"]
    for filename in args:
        close = False
        try:
            if filename == "-":
                f = sys.stdin
            else:
                f = open(filename)
                close = True
            if len(args) > 1:
                print("==> {} <==".format(filename))
            if lines == 0:
                continue
            for n, line in enumerate(f, start=1):
                sys.stdout.write(line)
                if n == lines:
                    break
        finally:
            if close:
                f.close()
