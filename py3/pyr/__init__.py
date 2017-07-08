import os
import sys

def interact(opts, args, locals=None):
    if locals is None:
        locals = {}
    locals["opts"] = opts
    locals["args"] = args
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

