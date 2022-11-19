SHELL=/bin/bash

debug: 
	buildozer -v android debug

release: 
	buildozer -v android release

run-debug:
	buildozer android debug deploy run logcat

run:
	buildozer android release deploy run logcat

test:
	python src/test.py

dump:
	python src/dump.py