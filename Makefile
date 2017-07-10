all: pyr-standalone

pyr-standalone: pyr py3/pyr/__init__.py util/gen-standalone
	util/gen-standalone >$@
	chmod +x $@
