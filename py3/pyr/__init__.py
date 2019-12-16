# code must be compatible across all supported Python versions

import errno
import importlib
import os
import signal
import sys
import traceback
import types


def pop_opts(args):
    """yield (name, value) options, then modify args in-place"""
    for n, x in enumerate(args):
        if x == "--":
            del args[:n + 1]
            break
        elif x.startswith("-") and len(x) != 1:
            if x.startswith("--"):
                name, sep, value = x[2:].partition("=")
                if not name:
                    raise Exit("usage", "missing option name")
                if not sep:
                    value = None
            else:
                name, value = x[1], x[2:] or None
            if any(x in pop_opts.bad_chars for x in name):
                raise Exit("usage", "bad option name")
            if name == ":":
                if value is not None:
                    for name in value:
                        if name == ":":
                            continue
                        if any(x in pop_opts.bad_chars for x in name):
                            raise Exit("usage", "bad option name")
                        yield name, None
            else:
                yield name, value
        else:
            del args[:n]
            break
    else:
        del args[:]
pop_opts.bad_chars = set(" `~!@#$%^&*=\\|;'\"?")

def interact(opts, args, names=None):
    if names is None:
        names = {}
    names.setdefault("opts", opts)
    names.setdefault("args", args)
    import code, inspect, site
    try:
        site.removeduppaths()
    except Exception:
        pass
    try:
        site.sethelper()
    except Exception:
        pass
    readline = None
    try:
        import readline
        history_fn = os.path.expanduser("~/.python3_history")
        if os.path.isfile(history_fn):
            readline.read_history_file(history_fn)
        import atexit
        atexit.register(readline.write_history_file, history_fn)
    except ImportError:
        pass
    if readline:
        try:
            import rlcompleter
            readline.parse_and_bind("tab: complete")
            readline.set_completer(rlcompleter.Completer(names).complete)
        except ImportError:
            pass
    console = code.InteractiveConsole(names)
    return console.interact(banner="", exitmsg="")
def execfile(path, globals=None):
    if globals is None:
        globals = {}
    globals.setdefault("__file__", path)
    globals.setdefault("__name__", "__file__")
    with open(path, "rb") as f:
        exec(compile(f.read(), path, "exec"), globals, globals)
    return globals

def set_command_name(name):
    global _error_prefix, _other_prefix
    _error_prefix = name + " error:"
    _other_prefix = name + ":"
def _print_message(prefix, message):
    if not message:
        raise ValueError("missing message")
    parts = [prefix]
    parts.extend(str(x).replace("\n", " ") for x in message)
    parts[-1] += "\n"
    sys.stderr.write(" ".join(parts))
def print_error(*message):
    """print message with a command error prefix to stderr"""
    _print_message(_error_prefix, message)
def print_warning(*message):
    """print message with a command prefix to stderr"""
    _print_message(_other_prefix, message)

def Exit(code, *message):
    """raise Exit(code, "message with", values)"""
    if message:
        _print_message(_error_prefix, message)
    if not isinstance(code, int):
        code = Exit.codes[code]
    return SystemExit(code)
Exit.codes = {
    "other":         1,
    # freebsd: man sysexits
    "usage":        64,
    "dataerr":      65,
    "noinput":      66,
    "nouser":       67,
    "nohost":       68,
    "unavailable":  69,
    "unknown":      69,
    "internal":     70,
    "to""do":       70,
    "os":           71,
    "osfile":       72,
    "cantcreat":    73,
    "cantcreate":   73,
    "io":           74,
    "tempfail":     75,
    "protocol":     76,
    "noperm":       77,
    "config":       78,
    }
def _add_signals():
    for name, value in signal.__dict__.items():
        if name.startswith("SIG") and not name.startswith("SIG_"):
            Exit.codes[name.lower()] = 128 + int(value)
_add_signals()
del _add_signals

class SignalExit(SystemExit): pass
class HangupSignal(SignalExit): pass
class TerminateSignal(SignalExit): pass
_exit_signals = {}
def exit_signal(signum, frame):
    """raise last registered exception class (or SystemExit)"""
    raise _exit_signals.get(signum, SystemExit)(signum + 128)
def register_exit_signal(signum, exception=None):
    """raise (exception or SystemExit)(signum + 128) on given signal

    Exception must be None or derived from SystemExit, and should be derived from SignalExit.
    """
    if exception is None:
        exception = SystemExit
    assert issubclass(exception, SystemExit), exception
    _exit_signals[signum] = exception
    signal.signal(signum, exit_signal)

def _print_exception():
    ty, val, tb = sys.exc_info()
    tb = tb.tb_next
    for _ in range(_print_exception.extra_skips):
        tb = tb.tb_next
    traceback.print_exception(ty, val, tb)
_print_exception.extra_skips = 0
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

    dirs = sys.argv.pop(0)
    dirs = [] if not dirs else dirs.split(":")
    for x in dirs:
        if x not in sys.path:
            sys.path.append(x)
    site_dirs = sys.argv.pop(0)
    site_dirs = site_dirs.split(",") if site_dirs else []
    _append_site(site_dirs)

    target = sys.argv.pop(0)
    if target == "__file__":
        target = _get_execfile(sys.argv.pop(0))
    else:
        target = _get_target(target)
    set_command_name(os.path.basename(sys.argv[0]))
    args = sys.argv[1:]
    opts = list(pop_opts(args))
    return target, opts, args
def _get_execfile(path):
    _print_exception.extra_skips += 1
    def target(opts, args):
        _print_exception.extra_skips += 1
        main = execfile(path).get("main")
        _print_exception.extra_skips -= 1
        if main:
            return main(opts, args)
    return target
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
        raise SystemExit(exit)

    except KeyboardInterrupt:
        if signal_tb:
            _print_exception()
        exit = 128 + signal.SIGINT
    except SystemExit as e:
        exit = e.code
        if not isinstance(exit, (int, type(None))):
            print_error(exit)
            exit = Exit.codes["unknown"]

    except BrokenPipeError as e:
        if signal_tb:
            _print_exception()
        exit = 128 + signal.SIGPIPE
    except IOError as e:
        _print_exception()
        exit = Exit.codes["io"]
    except OSError as e:
        _print_exception()
        exit = Exit.codes["os"]
    except BaseException:
        _print_exception()
        exit = Exit.codes["internal"]

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
