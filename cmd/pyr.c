#include <errno.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static char const *prog_name = "<unknown>";
void fatal(int rc, char const *fmt, ...) {
    fprintf(stderr, "%s error: ", prog_name);
    va_list args;
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);
    fputc('\n', stderr);
    exit(rc);
    }

typedef int (*handle_option_func)(char const *name, char const *value, void *data);
static int parse_options_(char **args, char ***rest, handle_option_func handle_option, void *data) {
    // modifies argument for long options with values, though does reverse the modification afterwards
    // returns 0 or the first non-zero return from handle_option
    // if rest is non-null, *rest is the first unprocessed argument, which will either be the first non-option argument or the argument for which handle_option returned non-zero
    int rc = 0;
    for (; args[0]; ++args) {
        if (!strcmp(args[0], "--")) {
            args += 1;
            break;
            }
        else if (args[0][0] == '-' && args[0][1] != '\0') {
            if (args[0][1] == '-') {
                // long option
                char *eq = strchr(args[0], '=');
                if (!eq) {
                    // long option without value
                    if ((rc = handle_option(args[0] + 2, NULL, data))) {
                        break;
                        }
                    }
                else {
                    // long option with value
                    *eq = '\0';
                    if ((rc = handle_option(args[0] + 2, eq + 1, data))) {
                        *eq = '=';
                        break;
                        }
                    *eq = '=';
                    }
                }
            else if (args[0][2] == '\0') {
                // short option without value
                if ((rc = handle_option(args[0] + 1, NULL, data))) {
                    break;
                    }
                }
            else {
                // short option with value
                char name[2] = {args[0][1]};
                if ((rc = handle_option(name, args[0] + 2, data))) {
                    break;
                    }
                }
            }
        else break;
    }
    if (rest) {
        *rest = args;
        }
    return rc;
    }
int parse_options(int *pargc, char ***pargv, handle_option_func handle_option, void *data) {
    char **rest;
    int rc = parse_options_(*pargv, &rest, handle_option, data);
    *pargc -= rest - *pargv;
    *pargv = rest;
    return rc;
    }
int main_parse_options(int *pargc, char ***pargv, handle_option_func handle_option, void *data) {
    prog_name = **pargv;
    char const *x = strrchr(prog_name, '/');
    if (x) prog_name = x + 1;
    --*pargc;
    ++*pargv;
    return parse_options(pargc, pargv, handle_option, data);
    }

static struct {
    // Pyr options
        char const *as;
        char *path;
        char const *py;
        bool signal_tb;
        char const *interact;
        bool run_file;
    // Python options
        bool no_bytecode;
        bool py_env;
        int optimize;
        char const *site;
        bool unbuffered;
    } opts = {};
static struct {
    char const **start, **end, **end_alloc;
    } new_args;
static void push_arg(char const *arg) {
    // keep one "hidden" arg entry, before start, for program name
    if (!new_args.start) {
        char const **x = malloc(sizeof(char**) * 16);
        x[0] = NULL;
        new_args.start = new_args.end = x + 1;
        new_args.end_alloc = x + 16;
        }
    else if (new_args.end == new_args.end_alloc) {
        int len = new_args.end - new_args.start;
        char const **x = realloc(new_args.start - 1, sizeof(char**) * (len + 1) * 2);
        new_args.start = x + 1;
        new_args.end = new_args.start + len;
        new_args.end_alloc = x + (len + 1) * 2;
        }
    *new_args.end = arg;
    new_args.end ++;
    }
static int handle_option(char const *name, char const *value, void *data) {
    #define OPT(NAME) else if (strcmp(name, NAME) == 0)
    #define OPT2(NAME_A, NAME_B) else if (strcmp(name, NAME_A) == 0 || strcmp(name, NAME_B) == 0)
    if (0) ;
    OPT2("as", "a") {
        if (!value) fatal(64, "missing value for option %s", name);
        opts.as = value;
        }
    OPT2("path", "p") {
        if (!value) fatal(64, "missing value for option %s", name);
        int n;
        if (opts.path) {
            n = strlen(opts.path) + 1;
            opts.path[n] = ':';
            }
        else n = 0;
        opts.path = realloc(opts.path, n + strlen(value) + 1);
        strcpy(opts.path + n, value);
        }
    OPT("py") {
        if (!value) fatal(64, "missing value for option %s", name);
        opts.py = value;
        }
    OPT2("2", "3") {
        int n = 7; // strlen("pythonX")
        if (value) n += strlen(value);
        char *py = malloc(n + 1);
        // mem is never freed
        py[n] = '\0';
        strcpy(py, "python");
        py[6] = name[0];
        if (value) strcpy(py + 7, value);
        opts.py = py;
        }
    OPT("signal-tb") {
        if (value) fatal(64, "unexpected value for option %s", name);
        opts.signal_tb = true;
        }
    OPT("interact") {
        if (!value) fatal(64, "missing value for option %s", name);
        opts.interact = value;
        }
    OPT2("file", "f") {
        if (value) fatal(64, "unexpected value for option %s", name);
        opts.run_file = true;
        }
    OPT("no-bytecode") {
        if (value) fatal(64, "unexpected value for option %s", name);
        opts.no_bytecode = true;
        }
    OPT2("py-env", "e") {
        if (value) fatal(64, "unexpected value for option %s", name);
        opts.py_env = true;
        }
    OPT2("no-py-env", "E") {
        if (value) fatal(64, "unexpected value for option %s", name);
        opts.py_env = false;
        }
    OPT("O") {
        if (value) fatal(64, "unexpected value for option %s", name);
        opts.optimize = 1;
        }
    OPT("optimize") {
        if (!value || strcmp(value, "on") == 0) opts.optimize = 1;
        else if (strcmp(value, "off") == 0) opts.optimize = 0;
        else if (strcmp(value, "OO") == 0) opts.optimize = 2;
        else fatal(64, "unknown value for option %s", name);
        }
    OPT("no-site") {
        if (value) fatal(64, "unexpected value for option %s", name);
        opts.site = NULL;
        }
    OPT2("site", "s") {
        if (!value) opts.site = "user,sys";
        else opts.site = value;
        }
    OPT("u") {
        if (value) fatal(64, "unexpected value for option %s", name);
        opts.unbuffered = true;
        }
    OPT("buffer") {
        if (!value || strcmp(value, "on") == 0) opts.unbuffered = false;
        else if (strcmp(value, "off") == 0) opts.unbuffered = true;
        else fatal(64, "unknown value for option %s", name);
        }
    OPT2("warn", "W") {
        if (!value) fatal(64, "missing value for option %s", name);
        char *s = malloc(2 + strlen(value) + 1);
        s[0] = '-';
        s[1] = 'W';
        strcpy(s + 2, value);
        push_arg(s);
        }
    OPT("X") {
        if (!value) fatal(64, "missing value for option %s", name);
        char *s = malloc(2 + strlen(value) + 1);
        s[0] = '-';
        s[1] = 'X';
        strcpy(s + 2, value);
        push_arg(s);
        }
    OPT("prepend") {
        if (!value) fatal(64, "missing value for option %s", name);
        push_arg(value);
        }
    else fatal(64, "unknown option %s", name);
    return 0;
    #undef OPT
    #undef OPT2
    }

char const *py3_dir(char const *self) {
    if (self[0] != '/') {
        self = realpath(self, NULL); // memory is never freed
        if (!self) fatal(71, "realpath failed: %s", strerror(errno));
        }
    int slash = 0;
    for (int n = strlen(self) - 1; n > 0; n--) {
        if (self[n] == '/') {
            slash ++;
            if (slash == 2) {
                char *s = malloc(n + 3 + 1); // memory is never freed
                strncpy(s, self, n);
                strcpy(s + n, "/py3");
                return s;
                }
            }
        }
    fatal(70, "unexpected executable location");
    return 0; // unreachable
    }

int main(int argc, char **argv) {
    char *self = argv[0];
    opts.optimize = 1;
    int rc = main_parse_options(&argc, &argv, &handle_option, NULL);
    if (rc) return rc;
    if (!opts.py) opts.py = "python3";
    if (!opts.interact) opts.interact = "pyr.interact";

    if (opts.run_file) {
        if (argc == 0) fatal(64, "--file requires TARGET argument");
        char *slash = strrchr(argv[0], '/');
        char *dirname, *basename;
        if (!slash) {
            dirname = realpath(".", NULL);
            if (!dirname) fatal(71, "realpath failed: %s", strerror(errno));
            basename = argv[0];
            }
        else if (slash == argv[0]) {
            // argv[0] is "/filename"
            dirname = "/";
            basename = slash + 1;
            }
        else {
            dirname = argv[0];
            if (dirname[0] != '/') {
                dirname = realpath(dirname, NULL);
                if (!dirname) fatal(71, "realpath failed: %s", strerror(errno));
                }
            *slash = '\0';
            basename = slash + 1;
            }
        if (strchr(dirname, ':')) fatal(64, "--file TARGET dirname contains colon: %s", dirname);
        { // prepend TARGET dirname to opts.path
            int n = opts.path ? 1 + strlen(opts.path) : 0;
            char *path = malloc(strlen(dirname) + n + 1);
            strcpy(path, dirname);
            if (opts.path) {
                strcat(path, ":");
                strcat(path, opts.path);
                }
            free(opts.path);
            opts.path = path;
            }
        { // set TARGET to basename + .main
            char *dot = strchr(basename, '.');
            if (!dot) fatal(64, "--file with unexpected TARGET (missing extension)");
            if (strchr(dot + 1, '.')) {
                fatal(64, "--file with unexpected TARGET (multiple extensions)");
                }
            *dot = '\0';
            argv[0] = malloc(strlen(basename) + 5 + 1);
            strcpy(argv[0], basename);
            strcat(argv[0], ".main");
            }
        }

    push_arg("-S");
    if (opts.no_bytecode) push_arg("-B");
    if (!opts.py_env) push_arg("-E");
    if (opts.optimize == 1) push_arg("-O");
    else if (opts.optimize == 2) push_arg("-OO");
    if (opts.unbuffered) push_arg("-u");
    push_arg("-c");
    push_arg("import sys\n"
        "del sys.argv[0], sys.path[0]\n"
        "sys.path.append(sys.argv.pop(0))\n"
        "from pyr import _bootstrap\n"
        "_bootstrap()\n"
        );
    push_arg(py3_dir(self));
    push_arg(opts.signal_tb ? "true" : "false");
    push_arg(opts.path ? opts.path : "");
    push_arg(opts.site ? opts.site : "");
    if (argc == 0 || strcmp(argv[0], "-") == 0) {
        push_arg(opts.interact);
        }
    else push_arg(argv[0]);
    if (opts.as) push_arg(opts.as);
    else if (argc == 0 || strcmp(argv[0], "-") == 0) push_arg(self);
    else {
        char *s = malloc(6 + strlen(argv[0]) + 1);
        strcpy(s, "[pyr ");
        strcat(s, argv[0]);
        strcat(s, "]");
        push_arg(s);
        }
    if (argc > 1) for (char **rest = argv + 1; rest != argv + argc; ++rest) {
        push_arg(*rest);
        }
    push_arg(NULL);
    new_args.start[-1] = opts.py;
    execvp(opts.py, (char **)new_args.start - 1);
    fatal(71, "execvp failed: %s", strerror(errno));
    }
