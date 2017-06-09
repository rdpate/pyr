all: pyr-standalone

pyr-standalone: pyr py3/pyr/_bootstrap.py
	sed 's/^bootstrap=.*/bootstrap=__main__/; /^#bootstrap/q' pyr >$@
	cat py3/pyr/_bootstrap.py >>$@
	printf "' " >>$@
	tail -n1 pyr >>$@
	chmod +x $@

clean:
	rm -f pyr-standalone
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name '*.py[co]' -delete
