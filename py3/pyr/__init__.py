# code must be compatible across all supported Python versions:
#   2.7, 3.4, 3.5, 3.6
# (other Python versions may work)

# code must be able to be included in shell script within single quotes

import importlib
import os
import signal
import sys
import traceback
import types


def interact(opts, args, locals=None):
    if locals is None:
        locals = {}
    locals.setdefault("opts", opts)
    locals.setdefault("args", args)
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
    console = code.InteractiveConsole(locals)
    if sys.version_info.major == 2:
        # v2 requires banner, this is more useful than a blank line:
        x = ["Python " + sys.version.split(None, 1)[0]]
    else:
        x = [""]
    if "exitmsg" in inspect.getargspec(console.interact).args:
        x.append("")
    return console.interact(*x)

class HangupSignal(SystemExit):
    pass

class TerminateSignal(SystemExit):
    pass

def _get_target(target):
    target, _, rest = target.partition(".")
    try:
        target = importlib.import_module(target)
    except ImportError as e:
        raise TargetLookupError(target)
        sys.stderr.write("ImportError: {}\n".format(e))
        sys.exit(70)
    for x in rest.split(".") if rest else ():
        try:
            target = getattr(target, x)
        except AttributeError as e:
            if isinstance(target, types.ModuleType):
                try:
                    target = importlib.import_module("." + x, package=target.__name__)
                except ImportError as ee:
                    sys.stderr.write("ImportError: {}\n".format(ee))
                    sys.exit(70)
                else:
                    continue
            sys.stderr.write("AttributeError: {}\n".format(e))
            sys.exit(70)
    if isinstance(target, types.ModuleType):
        try:
            target = getattr(target, "main")
        except AttributeError as e:
            sys.stderr.write("AttributeError: {}\n".format(e))
            sys.exit(70)
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

_exit_signals = {}
def exit_signal(signum, frame):
    """raise last registered exception class (or SystemExit)"""
    raise _exit_signals.get(signum, SystemExit)(signum + 128)

def register_exit_signal(signum, exception=None):
    """raise (exception or SystemExit)(signum + 128) on given signal

    Exception must be None or derived from SystemExit.
    """
    if exception is None:
        exception = SystemExit
    assert issubclass(exception, SystemExit), exception
    _exit_signals[signum] = exception
    signal.signal(signum, exit_signal)

def _print_exception(e):
    sys.stderr.write("{} error...\n".format(sys.argv[0]))
    traceback.print_exception(type(e), e, sys.exc_info()[2].tb_next)

def _bootstrap(argv):
    # PY2: lacks BrokenPipeError, handled in except IOError below, but this avoids NameError
    try:
        BrokenPipeError
    except NameError:
        class BrokenPipeError(Exception):
            pass

    signal_tb = (argv.pop(0) == "true")
    try:
        try:
            register_exit_signal(signal.SIGHUP, HangupSignal)
            register_exit_signal(signal.SIGTERM, TerminateSignal)
            dirs = argv.pop(0)[1:]
            dirs = [] if not dirs else dirs.split(":")
            for x in dirs:
                if x not in sys.path:
                    sys.path.append(x)
            target = _get_target(argv.pop(0))
            args = argv[1:]
            opts = list(pop_opts(args))
            sys.exit(target(opts, args))
        except KeyboardInterrupt as e:
            if signal_tb:
                _print_exception(e)
            exit = 128 + signal.SIGINT
        except BrokenPipeError as e:
            if signal_tb:
                _print_exception(e)
            exit = 128 + signal.SIGPIPE
        except IOError as e:
            # PY2: lacks BrokenPipeError
            import errno
            if e.errno == errno.EPIPE:
                if signal_tb:
                    _print_exception(e)
                exit = 128 + signal.SIGPIPE
            else:
                _print_exception(e)
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
            _print_exception(e)
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
