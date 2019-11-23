#!/bin/sh -ue

fatal() { rc="$1"; shift; printf %s\\n "${0##*/} error: $*" >&2 || true; exit "$rc"; }
squote() {
    while [ $# != 0 ]; do
        printf \'%s\'${2+' '} "$(printf %s "$1" | sed -r s/\'/\'\\\\\'\'/g)"
        shift
        done
    }

# options
    as=
    dirs=
    python=python3
    signal_tb=false
    interact=pyr.interact
    run_file=false
    site=
    py_bytecode=
    py_env=-E
    py_optimize=-O
    py_unbuffered=
    py_warn=
    py_x=
    py_prepend=
handle_option() {
    case "$1" in
        a|as)
            [ $# = 2 ] || fatal 64 "missing value for option $1"
            [ -n "$2" ] || fatal 64 "expected non-empty value for option $1"
            as="$2"
            ;;
        p|path)
            [ $# = 2 ] || fatal 64 "missing value for option $1"
            x="$2"
            while [ -n "$x" ]; do
                p="${x%%:*}"
                if [ x"$p" = x"$x" ]; then
                    x=
                else
                    x="${x#*:}"
                fi
                if [ -z "$p" ]; then
                    fatal 64 "empty --path component"
                fi
                f="$(readlink -f -- "$p")" || fatal 64 "missing --path: $p"
                dirs="${dirs:+$dirs:}$f"
            done
            ;;
        py)
            [ $# = 2 ] || fatal 64 "missing value for option $1"
            [ -n "$2" ] || fatal 64 "expected non-empty value for option $1"
            python="$2"
            ;;
        2|3)
            python="python$1${2-}"
            ;;
        signal-tb)
            [ $# = 1 ] || fatal 64 "unexpected value for option $1"
            signal_tb=true
            ;;
        interact)
            [ $# = 2 ] || fatal 64 "missing value for option $1"
            [ -n "$2" ] || fatal 64 "expected non-empty value for option $1"
            interact="$2"
            ;;
        f|file)
            [ $# = 1 ] || fatal 64 "unexpected value for option $1"
            run_file=true
            ;;

        no-bytecode)
            [ $# = 1 ] || fatal 64 "unexpected value for option $1"
            py_bytecode=-B
            ;;
        e|py-env)
            [ $# = 1 ] || fatal 64 "unexpected value for option $1"
            py_env=
            ;;
        E|no-py-env)
            [ $# = 1 ] || fatal 64 "unexpected value for option $1"
            py_env=-E
            ;;
        optimize)
            case "${2-on}" in
                on)     py_optimize=-O      ;;
                off)    py_optimize=        ;;
                OO)     py_optimize=-OO     ;;
                *) fatal 64 "unknown value for option $1" ;;
            esac
            ;;
        O)
            [ $# = 1 ] || fatal 64 "unexpected value for option $1"
            py_optimize=-O
            ;;
        no-site)
            [ $# = 1 ] || fatal 64 "unexpected value for option $1"
            site=
            ;;
        s|site)
            if [ $# = 1 ]; then
                site=user,sys
            elif [ -z "$2" ]; then
                site=
            else
                site=
                set -- "$2"
                while [ $# != 0 ]; do
                    case "$1" in
                        *,*) set -- "${1%%,*}" "${1#*,}"
                    esac
                    case "$1" in
                        user) site="${site:+$site,}user" ;;
                        sys) site="${site:+$site,}sys" ;;
                        '') fatal 64 'empty --site item' ;;
                        *) fatal 64 "unknown --site item: $1" ;;
                    esac
                    shift
                done
            fi
            ;;
        u)
            [ $# = 1 ] || fatal 64 "unexpected value for option $1"
            py_unbuffered=-u
            ;;
        buffer)
            case "${2-on}" in
                off)    py_unbuffered=-u    ;;
                on)     py_unbuffered=      ;;
                *) fatal 64 "unknown value for option $1" ;;
            esac
            ;;
        W)
            [ $# = 2 ] || fatal 64 "missing value for option $1"
            [ -n "$2" ] || fatal 64 "expected non-empty value for option $1"
            py_warn="$py_warn -W$(squote "$2")"
            ;;
        X)
            [ $# = 2 ] || fatal 64 "missing value for option $1"
            [ -n "$2" ] || fatal 64 "expected non-empty value for option $1"
            py_x="$py_x -X$(squote "$2")"
            ;;
        prepend)
            [ $# = 2 ] || fatal 64 "missing value for option $1"
            py_prepend="$py_prepend $(squote "$2")"
            ;;

        *) fatal 64 "unknown option $1" ;;
    esac
}
while [ $# -gt 0 ]; do
    case "$1" in
        --) shift; break ;;
        --=*) fatal 64 'missing option name' ;;
        --*=*)
            x="${1#--}"
            v="${x#*=}"
            x="${x%%=*}"
            case "$x" in
                :?*|*[\ \`\~\!\@\#\$\%\^\&\*\\\|\;\'\"\?]*) fatal 64 'bad option name' ;;
                :)
                    shift
                    x="$v"
                    while [ -n "$x" ]; do
                        v="${x%?}"
                        set -- -"${x#"$v"}" "$@"
                        x="$v"
                        done
                    ;;
                *)
                    handle_option "$x" "$v"
                    shift
                    ;;
                esac
            ;;
        --:) shift ;;
        --:*|--*[\ \`\~\!\@\#\$\%\^\&\*\\\|\;\'\"\?]*) fatal 64 'bad option name' ;;
        --*) handle_option "${1#--}"; shift ;;
        -[\ \`\~\!\@\#\$\%\^\&\*\=\\\|\;\'\"\?]*) fatal 64 'bad option name' ;;
        -:*)
            x="${1#??}"
            shift
            while [ -n "$x" ]; do
                v="${x%?}"
                set -- -"${x#"$v"}" "$@"
                x="$v"
                done
            ;;
        -?) handle_option "${1#-}"; shift ;;
        -?*)
            v="${1#??}"
            x="${1%"$v"}"
            handle_option "${x#-}" "$v"
            shift
            ;;
        *) break ;;
        esac
    done

if [ $# = 0 ]; then
    if $run_file; then
        fatal 64 '--file with missing TARGET'
    fi
    target="$interact"
    if [ -z "$as" ]; then
        as="$0"
    fi
elif [ x"$1" = x- ]; then
    if $run_file; then
        fatal 64 '--file with "-" TARGET'
    fi
    shift
    target="$interact"
    if [ -z "$as" ]; then
        as="$0"
    fi
else
    target="$1"
    if $run_file; then
        target="$(basename "$target" .py)"
        case "$target" in
            *.*) fatal 64 "--file with invalid module filename: $1"
        esac
        target="$target.main"
        p="$(dirname -- "$1")"
        f="$(readlink -f -- "$p")" || fatal 64 "missing --path: $p"
        case "$f" in
            *:*) fatal 64 "--file TARGET path contains \":\": $f" ;;
        esac
        dirs="$f${dirs:+:$dirs}"
    fi
    shift
fi

self="$(readlink -f -- "$0")"
eval exec "$(squote "$python")" -S \
    $py_prepend $py_x $py_warn \
    $py_bytecode $py_env $py_optimize $py_unbuffered \
    -c \''
import sys
del sys.argv[0], sys.path[0]
sys.path.append(sys.argv.pop(0))
from pyr import _bootstrap
_bootstrap()
'\' "$(squote "${self%/*/*}/py3" $signal_tb "$dirs" "$site" "$target" "${as:-[pyr $target]}" "$@")"
