all: pyr-standalone

pyr-standalone: pyr py3/pyr/_bootstrap.py util/standalone
	util/standalone >$@
	chmod +x $@
