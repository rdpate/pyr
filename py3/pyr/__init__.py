# code must be compatible across all supported Python versions:
#   2.7, 3.4, 3.5, 3.6
# (other Python versions may work)

import errno
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

class SignalExit(SystemExit):
    pass
class HangupSignal(SignalExit):
    pass
class TerminateSignal(SignalExit):
    pass

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


def _print_exception():
    sys.stderr.write("{} error...\n".format(sys.argv[0]))
    ty, val, tb = sys.exc_info()
    tb = tb.tb_next
    traceback.print_exception(ty, val, tb)

def _append_site(types):
    import site
    def add_site_dir(dir):
        if os.path.isdir(dir):
            site.addsitedir(dir)
    import_user_customize = False
    user_done = sys_done = False
    for dir_type in types:
        if dir_type == "user":
            if user_done:
                continue
            d = site.getusersitepackages()
            if d:
                add_site_dir(d)
                import_user_customize = True
        elif dir_type == "sys":
            if sys_done:
                continue
            tail = "/lib/python{}.{}/site-packages".format(*sys.version_info[:2])
            add_site_dir(sys.prefix + tail)
            if sys.exec_prefix != sys.prefix:
                add_site_dir(sys.exec_prefix + tail)
            try:
                import sitecustomize
            except ImportError as e:
                if e.name != "sitecustomize":
                    raise
        else:
            sys.stderr.write("pyr error: unknown --site item: {!r}".format(dir_type))
            sys.exit(70)
    if import_user_customize:
        try:
            import usercustomize
        except ImportError as e:
            if e.name != "usercustomize":
                raise

def _bootstrap_setup():
    register_exit_signal(signal.SIGHUP, HangupSignal)
    register_exit_signal(signal.SIGTERM, TerminateSignal)

    dirs = sys.argv.pop(0)[1:]
    dirs = [] if not dirs else dirs.split(":")
    for x in dirs:
        if x not in sys.path:
            sys.path.append(x)
    site_dirs = sys.argv.pop(0)
    site_dirs = site_dirs.split(",") if site_dirs else []
    _append_site(site_dirs)

    target = _get_target(sys.argv.pop(0))
    args = sys.argv[1:]
    opts = list(pop_opts(args))
    return target, opts, args

def _get_target(target):
    target, _, rest = target.partition(".")
    try:
        target = importlib.import_module(target)
    except ImportError as e:
        sys.stderr.write("pyr ImportError: {}\n".format(e))
        sys.exit(70)
    for x in rest.split(".") if rest else ():
        try:
            target = getattr(target, x)
        except AttributeError as e:
            if isinstance(target, types.ModuleType):
                try:
                    target = importlib.import_module("." + x, package=target.__name__)
                except ImportError as ee:
                    sys.stderr.write("pyr ImportError: {}\n".format(ee))
                    sys.exit(70)
                else:
                    continue
            sys.stderr.write("pyr AttributeError: {}\n".format(e))
            sys.exit(70)
    if isinstance(target, types.ModuleType):
        try:
            target = getattr(target, "main")
        except AttributeError as e:
            sys.stderr.write("pyr AttributeError: {}\n".format(e))
            sys.exit(70)
    return target


def _bootstrap():
    signal_tb = (sys.argv.pop(0) == "true")
    exit = None
    try:
        target, opts, args = _bootstrap_setup()
        exit = target(opts, args)
        if not exit:
            if sys.stdout is not None:
                sys.stdout.flush()
            if sys.stderr is not None:
                sys.stderr.flush()
        sys.exit(exit)
    except KeyboardInterrupt:
        if signal_tb:
            _print_exception()
        exit = 128 + signal.SIGINT
    except IOError as e:
        # PY2: lacks BrokenPipeError, but this works in 3.x too
        if e.errno == errno.EPIPE:
            if signal_tb:
                _print_exception()
            exit = 128 + signal.SIGPIPE
        else:
            _print_exception()
            exit = 1
    except SystemExit as e:
        exit = e.code
        message = getattr(e, "message", None)
        if message:
            sys.stderr.write("{} error: {}\n".format(sys.argv[0], message))
        elif not isinstance(exit, (int, type(None))):
            sys.stderr.write("{} error: {}\n".format(sys.argv[0], exit))
            exit = 1
    except BaseException:
        _print_exception()
        exit = 1
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
                        sys.exit(exit)
