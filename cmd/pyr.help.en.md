% [TARGET [OPT..] [ARG..]]

Execute TARGET as Python source.  If TARGET defines "main", run main(opts, args), where opts is a list of (name, value) tuples and args is a list.  Unlike when directly executing with Python, "\_\_name\_\_" will be "\_\_file\_\_" instead of "\_\_main\_\_".

With option -m/--module, TARGET is a dotted attribute list for a callable which is given opts and args arguments.  If TARGET is a module instead of a callable, then TARGET.main must exist and is used instead.

If TARGET is "-" or missing, run Python interactively.  Locals include opts and args variables, which can be non-empty if TARGET is "-".

Options:
-aP --as=PROG           use PROG as sys.argv[0]
-pX --path=X            append colon-separated dirs to sys.path
    --py=PY             absolute/relative/$PATH Python (default: python3)
-3Y                     --py=python3[Y] (eg. -3.6)
    --signal-tb         print tracebacks for (some) signal exits
# FUTURE: signal-tb value to list signals that print traceback?
    --interact=T        use T for console (default: pyr.interact)
-m  --module            use TARGET callable (or TARGET.main for modules)

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
-WS --warn=S            Python -WS (--prepend=-WS)
-XS                     Python -XS (--prepend=-XS)
    --prepend=RAW       prepend RAW interpreter option
