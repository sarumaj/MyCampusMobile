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
	python -m unittest discover -s src/backend/tests -t src -v -p test.py

dump:
	python src/dump.py