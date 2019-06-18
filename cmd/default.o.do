set -Cue
exec >&2
fatal() { rc="$1"; shift; printf %s\\n "${0##*/} error: $*" >&2 || true; exit "$rc"; }

src="${1%.o}.c"
redo-ifchange "$src"
[ -e "$src" ] || fatal 66 "missing source $1"
dep="$(dirname "$1")/.$(basename "$1").dep"
target="$1"
output="$3"
set -- -std=c11 -D_DEFAULT_SOURCE -D_BSD_SOURCE -Wall -Werror -O3
if [ -e "$target.args" ]; then
    redo-ifchange "$target.args"
    reldir="$(dirname "$target.args")"
    while read -r line; do
        case "$line" in
            '#'*|'') continue ;;
            [-/]*) ;;
            *) line="$reldir/$line" ;;
            esac
        set -- "$@" "$line"
        done <"$target.args"
    fi
cc -c -MD -MF"$dep" -o"$output" "$@" "$src"
sed -r 's/^[^:]+: *//; s/ \\$//; s/^ +| +$//g; s/ +/\n/g' "$dep" \
| xargs redo-ifchange
rm "$dep"
