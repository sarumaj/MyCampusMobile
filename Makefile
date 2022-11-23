SHELL=/bin/bash

.PHONY: debug
debug:
	buildozer -v android debug
	$(shell ./release.sh)

.PHONY: release
release:
	buildozer -v android release

publish: release
	$(shell ./publish.sh)

adb-run-debug: debug
	buildozer android debug deploy run logcat

adb-run: release
	buildozer android release deploy run logcat

run: c.profile
	python main.py

.PHONY: test
test:
	python test.py

.PHONY: dump
dump:
	python dump.py