all: pyr-standalone

clean:
	find */ -type d -name __pycache__ -delete
	find . -type f -name '*.py[oc]' -delete
	rm -f pyr-standalone


pyr-standalone: pyr py3/pyr/__init__.py util/gen-standalone
	util/gen-standalone >$@
	chmod +x $@
