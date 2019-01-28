% [TARGET [OPT..] [ARG..]]

Import TARGET and run sys.exit(TARGET(opts, args)), where opts is a list of (name, value) tuples and args is a list.  If TARGET specifies a module, TARGET.main will be used instead.

If TARGET is "-" or missing, run Python interactively.  Locals include opts and args variables, which may be non-empty if TARGET is "-".

Options:
-aP --as=PROG           sys.argv[0] (default: [pyr TARGET])
-pX --path=X            append colon-separated dirs to sys.path
    --py=PY             absolute/relative/$PATH Python (default: python3)
-2Y                     --py=python2[Y] (eg. -2)
-3Y                     --py=python3[Y] (eg. -3.6)
    --signal-tb         print tracebacks for (some) signal exits
# FUTURE: signal-tb value to list signals that print traceback?
    --interact=T        use T for console (default: pyr.interact)
-f  --file              --path=(TARGET's dirname), TARGET=basename.main

Python options:
    --no-bytecode       Python -B
-e  --py-env            no Python -E
-E  --no-py-env         Python -E (default)
-O  --optimize[=on]     Python -O (default)
    --optimize=off      no Python -O
    --optimize=OO       Python -OO
    --no-site           Python -S (default)
-s  --site[=user,sys]   append user/system site dirs after --path
-u  --buffer=off        Python -u
    --buffer[=on]       no Python -u (default)
-WS --warn=S            Python -WS
-XS                     Python -XS
    --prepend=RAW       prepend RAW to interpreter args