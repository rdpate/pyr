all: cmd/pyr-standalone

cmd/pyr-standalone: cmd/pyr py3/pyr/__init__.py util/gen-standalone
	util/gen-standalone >$@
	chmod +x $@
