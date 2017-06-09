Pyr
===

    pyr [MODULE:FUNC [OPT..] [ARG..]]

Pyr ("pure") is an experimental Python front-end to replace "pythonXY script".  Put code into modules!  Pyr replaces "pythonXY -m", which prepends the current working directory to sys.path and only allows further sys.path additions through $PYTHONPATH.

Pyr parses options consistently and uniformly, replacing optparse and argparse, but options must, as always, be given meaning by the code using them.

## Quick Example

    $ mkdir bin py3
    $ cat >bin/show <<END
    #!/bin/sh -ue
    exec ".../pyr" -a"$0" -3.6 --path="$(dirname "$0")/../py3" example:main "$@"
    END
    $ cat >py3/example.py <<END
    import sys
    def main(opts, args):
        print(sys.argv)
        print(opts)
        print(args)
    END
    $ chmod +x bin/show
    $ ./bin/show -a -b1 --cc --dd= --ee=2 foo 'bar baz'
    ['./bin/show', '-a', '-b1', '--c', '--d=', '--e=2', 'foo', 'bar baz']
    [('a', None), ('b', '1'), ('cc', None), ('dd', ''), ('ee', '2')]
    ['foo', 'bar baz']

## Options

All options follow identical syntax in two flavors: short and long.  Short options start with a single hyphen and are named with a single character followed by the value, if any.  Long options start with double hyphens, separate the name and value with equals ("="), and allow distinguishing an empty value from no value.  Any short option may be specified as a long option with a single-character name (eg. --a, --b=X).

Options must come before all arguments.

## Arguments

Arguments follow all options.  The first argument either starts without a hyphen or is one of two special arguments: "-", which is retained, or "--", which is discarded.

## Interactive

Run without args or with "-" for an interactive interpreter.  Pyr's options to control Python options and sys.path are still usable.  Without args, the site module is imported, to be nearly identical to Python's native console.  (With "-", the default -S is used.)

TODO: use PYTHONSTARTUP, or check which versions of code module already do so

### Project Console

Create an executable in your project:

    #!/bin/sh -ue
    # replace -p with one or more directories to append to sys.path
    # eg. the project's Python module directory (relative path from $0)
    exec .../pyr -a"$0" -S -p"$(basename "$0")/py3" "$@"

Now you either get a console or supply MODULE:FUNC, either way project-specific directories are applied to sys.path, and project-specific Pyr options should also be specified here.  Also see how bin/reconstruct and bin/showargs call functions in pyr.examples.

## Standalone Pyr

Make pyr-standalone to copy into any project.
