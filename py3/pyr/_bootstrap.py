# code must be compatible across all supported Python versions:
#   2.7, 3.4, 3.5, 3.6
# (other Python versions may work)

# code must be able to be included in shell script within single quotes

import importlib
import os
import signal
import sys
import traceback

def interact(opts, args):
    import code, inspect, site
    try:
        site.removeduppaths()
    except Exception:
        pass
    try:
        site.sethelper()
    except Exception:
        pass
    try:
        import atexit, readline
    except ImportError:
        pass
    else:
        import rlcompleter
        readline.parse_and_bind("tab: complete")
        history_fn = os.path.expanduser("~/.python{}_history".format(sys.version_info[0]))
        if os.path.isfile(history_fn):
            readline.read_history_file(history_fn)
        atexit.register(readline.write_history_file, history_fn)
    locals = {"opts": opts, "args": args}
    console = code.InteractiveConsole(locals)
    if sys.version_info.major == 2:
        # v2 requires banner, this is more useful than a blank line:
        x = ["Python " + sys.version.split(None, 1)[0]]
    else:
        x = [""]
    if "exitmsg" in inspect.getargspec(console.interact).args:
        x.append("")
    return console.interact(*x)

def get_target(module, attr):
    try:
        module = importlib.import_module(module)
    except ImportError as e:
        sys.stderr.write("ImportError: {}\n".format(e))
        sys.exit(64)
    target = module
    try:
        for x in attr.split("."):
            target = getattr(module, x)
    except AttributeError as e:
        sys.stderr.write("AttributeError: {}\n".format(e))
        sys.exit(64)
    return target

def pop_opts(args):
    """yield (name, value) options, then modify args in-place"""
    for n, x in enumerate(args):
        if x == "--":
            del args[:n + 1]
            break
        elif x.startswith("-") and len(x) != 1:
            if x.startswith("--"):
                name, sep, value = x[2:].partition("=")
                if not sep:
                    value = None
            else:
                name, value = x[1], x[2:] or None
            yield name, value
        else:
            del args[:n]
            break
    else:
        del args[:]

# PY2: lacks BrokenPipeError
try:
    BrokenPipeError
except NameError:
    class BrokenPipeError(Exception):
        pass

def exit_signal(signum, frame):
    raise SystemExit(signum + 128)
signal.signal(signal.SIGHUP, exit_signal)
signal.signal(signal.SIGTERM, exit_signal)

silent = sys.argv.pop(0) != "false"
for x in sys.argv.pop(0)[1:].split(":"):
    if x not in sys.path:
        sys.path.append(x)
def print_exception(e):
    sys.stderr.write("{} error:\n".format(os.path.basename(sys.argv[0])))
    traceback.print_exception(type(e), e, sys.exc_info()[2].tb_next)
try:
    try:
        target = None
        target = get_target(sys.argv.pop(0), sys.argv.pop(0))
        args = sys.argv[1:]
        opts = list(pop_opts(args))
        sys.exit(target(opts, args))
    except KeyboardInterrupt as e:
        if not silent:
            print_exception(e)
        exit = 128 + signal.SIGINT
    except BrokenPipeError as e:
        if not silent:
            print_exception(e)
        exit = 128 + signal.SIGPIPE
    except IOError as e:
        # PY2: lacks BrokenPipeError
        import errno
        if e.errno == errno.EPIPE:
            if not silent:
                print_exception(e)
            exit = 128 + signal.SIGPIPE
        else:
            print_exception(e)
            exit = 1
    except SystemExit as e:
        exit = e.code
        message = getattr(e, "message", None)
        if message:
            sys.stderr.write("{} error: {}\n".format(sys.argv[0], message))
        elif not isinstance(exit, (int, type(None))):
            sys.stderr.write("{} error: {}\n".format(sys.argv[0], exit))
            exit = 1
    except BaseException as e:
        print_exception(e)
        exit = 1
    sys.exit(exit)
finally:
    try:
        if sys.stdout is not None:
            sys.stdout.flush()
    finally:
        try:
            if sys.stdout is not None:
                sys.stdout.close()
        finally:
            if sys.stderr is not None:
                try:
                    sys.stderr.flush()
                finally:
                    sys.stderr.close()
