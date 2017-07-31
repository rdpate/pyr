import os
import sys

from . import pop_opts, optics, __version__
pyr = sys.modules[__package__]

def main(opts, args):
    if sys.platform.startswith("win32"):
        # TODO: win32 script template
        return "{} error: missing script template for win32".format(sys.argv[0])

    if opts:
        return "{} error: unknown option {}".format(sys.argv[0], opts[0][0])
    if not args:
        return "{} error: missing TARGET argument".format(sys.argv[0])
    if len(args) > 1:
        return "{} error: unknown extra arguments".format(sys.argv[0])

    pyr_script = args[0]
    if os.path.exists(pyr_script):
        return "{} error: script already exists: {}".format(sys.argv[0], pyr_script)
    script_dir = os.path.dirname(pyr_script) or "."
    if not os.path.exists(script_dir):
        return "{} error: script directory missing: {}".format(sys.argv[0], script_dir)

    base = os.path.dirname(pyr.__file__)
    pyr_name = os.path.basename(base)
    pyr_path = os.path.join(base, "pyr-path")
    if "'" in pyr_path + pyr_name:
        return "{} error: path contains single-quote: {}/{}".format(sys.argv[0], pyr_path, pyr_name)
    if os.path.exists(pyr_path):
        print("skipping creation of {}".format(pyr_path))
    else:
        os.mkdir(pyr_path)
        print("created directory {}".format(pyr_path))
    pyr_path_pyr = os.path.join(pyr_path, "pyr")
    if os.path.exists(pyr_path_pyr):
        print("skipping creation of {}".format(pyr_path_pyr))
    else:
        src = "../../" + pyr_name
        os.symlink(src, pyr_path_pyr)
        print("created symlink {} to {}".format(pyr_path_pyr, src))

    help_file = os.path.join(os.path.dirname(__file__), "pyr-help.en.txt")
    if not os.path.exists(help_file):
        help_text = ""
        print("omitting help text from script (help file not found)")
    else:
        with open(help_file) as f:
            help_text = ["#.help\n"]
            for line in f:
                if line == "\n" or line.startswith("#"):
                    line = "#" + line
                else:
                    line = "# " + line
                help_text.append(line)
            help_text = "".join(help_text)
        print("including help text in script")
    with open(pyr_script, "x") as f:
        f.write("""\
#!/bin/sh -ue
#.version
# {}
{}\
pyr_path='{}'
. "$pyr_path/pyr/stub-sh"
""".format(__version__, help_text, pyr_path))
        mode = os.stat(f.fileno()).st_mode
        for shift in 0, 3, 6:
            if mode & (4 << shift):
                mode |= 1 << shift
        os.chmod(f.fileno(), mode)
    print("created script {}".format(pyr_script))

if __name__ == "__main__":
    args = sys.argv[1:]
    sys.exit(main(list(pop_opts(args)), args))
