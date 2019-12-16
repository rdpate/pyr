Pyr
===

    pyr [TARGET [OPT..] [ARG..]]

Pyr ("pure") is an experimental Python front-end to replace "pythonXY file" and "pythonXY -mmodule".
Pyr parses options consistently and uniformly, replacing optparse and argparse.
By default, Pyr has Python ignore environment variables, optimize code, and without site packages or user/sitecustomize modules.


## Quick Example

    $ mkdir cmd py3

    $ cat >cmd/show <<'END'
    #!/bin/sh -Cue
    exec /path/to/pyr --path="$(dirname "$(readlink -f -- "$0")")/../py3" \
        -a"$0" -m example "$@"
    END

    $ cat >py3/example.py <<'END'
    import sys
    def main(opts, args):
        print(sys.argv)
        print(opts)
        print(args)
    END

    $ chmod +x cmd/show

    $ ./cmd/show -a -b1 --cc --dd= --ee=2 foo 'bar baz'
    ['./cmd/show', '-a', '-b1', '--c', '--d=', '--e=2', 'foo', 'bar baz']
    [('a', None), ('b', '1'), ('cc', None), ('dd', ''), ('ee', '2')]
    ['foo', 'bar baz']

In particular while getting started with Pyr:
Use --optimize=off to execute asserts.
Use -s to include user and system site directories until your path directories are sorted.

## Installation

Pyr runs Python rather than the other way around.
Install Pyr by cloning the repository or unpacking an archive, then symlink cmd/pyr into $PATH.

## Options & Arguments

Options must come before all arguments.
All options follow identical syntax in two flavors: short and long.
Short options start with a single hyphen and are named with a single character followed by the value, if any.
Long options start with double hyphens, separate the name and value with equals ("="), and allow distinguishing an empty value from no value.
Any short option may be specified as a long option with a single-character name (eg. --a, --b=X).

Arguments follow all options.
The first argument either starts without a hyphen or is one of two special arguments: "-" (which is retained) or "--" (which is discarded).

## Interactive Console

Pyr provides a simple interactive interpreter nearly identical to Python's native console.
To use it, run Pyr without TARGET or with "-".
The latter form allows further arguments (eg. shell globs) available as "args" variable.
(Options are also parsed, available as "opts".)
Console history is loaded from and saved to ~/.python3\_history.

Pyr's options to control Python and sys.path are still applied.
$PYTHONSTARTUP is always ignored; to get something similar, write a function which calls pyr.interact with a dict third argument:

    import pyr
    def main(opts, args):
        import datetime, sys, re
        now = datetime.datetime.now()
        return pyr.interact(opts, args, locals())

Copy doc/custom-interact (eg. to ~/cmd/pyr) and modify it with the path to Pyr and the path to the above module.

## Consistent Error Messages

Pyr.optics provides several utilities for option and argument validation with consistent error messages.
See Exit, parse\_opts, and more.

## Compared to Alternatives

Pyr is very much like a virtualenv without creating a faux Python install.
Consequently, a different tool is required to manage external dependencies.

### sys.path

Because providing a filename to Python prepends that file's parent directory to sys.path, you may want to use a location that won't have other files or directories added.
The situation is arguably worse with Python -m, as the *current working directory* is prepended to sys.path.
At either point, the file's location might as well be a path explicitly added to sys.path with a stub (located anywhere) used to call it.
Use doc/show\_path.py to see these sys.path differences:

    $ pyr -pdoc -m show_path
    # doc is appended

    $ PYTHONPATH=doc python3 -mshow_path
    # CWD and doc are BOTH prepended

    $ pyr doc/show_path.py
    # doc NOT in sys.path

    $ python3 doc/show_path.py
    # doc is prepended

Because environment is inherited, local use of $PYTHONPATH might inadvertantly affect a child process (or be affected by a parent process) only incidentally implemented in Python.
However, Python provides no other way to modify sys.path, apart from Python code manipulating sys.path which would, again, be put into a stub.

### Signal Exits

By default, Python shows tracebacks for certain signals where Unix convention is to exit non-zero without output.
Pyr instead exits without tracebacks, but option --signal-tb skips suppression.
In addition to KeyboardInterrupt/SIGINT and BrokenPipeError/SIGPIPE, pyr.HangupSignal is raised from SIGHUP and pyr.TerminateSignal from SIGTERM, both derived from SystemExit.
(Set handlers with signal.signal to get other behavior.)
Whenever exiting due to a signal exception, the exit code is 128 plus the signal number.
Also see pyr.register\_exit\_signal.

Use doc/yes.py to see differences from SIGPIPE:

    # considering other programs:
    $ yes | head -n1
    y

    # compare pyr's default behavior:
    $ pyr doc/yes.py | head -n1
    y

    # against python's default behavior:
    $ python3 doc/yes.py | head -n1
    y
    Traceback (most recent call last):
      File "doc/yes.py", line 6, in <module>
        main([], [])
      File "doc/yes.py", line 3, in <module>
        print("y")
    BrokenPipeError: [Errno 32] Broken pipe

    # signal tracebacks can be shown instead of hidden:
    $ pyr --signal-tb doc/yes.py | head -n1
    y
    Traceback (most recent call last):
      File "doc/yes.py", line 3, in main
        print("y")
    BrokenPipeError: [Errno 32] Broken pipe

Use doc/sigint and doc/sleep.py to see differences from SIGINT:

    $ doc/sigint pyr doc/sleep.py; echo $?
    130

    $ doc/sigint pyr --signal-tb doc/sleep.py; echo $?
    Traceback (most recent call last):
      File "doc/sleep.py", line 4, in main
        time.sleep(60)
    KeyboardInterrupt
    130

    $ doc/sigint python3 doc/sleep.py; echo $?
    Traceback (most recent call last):
      File "doc/sleep.py", line 7, in <module>
        main([], [])
      File "doc/sleep.py", line 4, in main
        time.sleep(60)
    KeyboardInterrupt
    1

### Lost Exceptions

Python can lose exceptions with confusing errors, but Pyr does not:

    $ pyr doc/date.py | :

    $ python3 doc/date.py | :
    Exception ignored in: <_io.TextIOWrapper name='<stdout>' mode='w' encoding='UTF-8'>
    BrokenPipeError: [Errno 32] Broken pipe
