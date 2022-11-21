SHELL=/bin/bash

debug: bin/*.apk
	buildozer -v android debug

release: bin/*aab
	buildozer -v android release

.PHONY: adb-run-debug
adb-run-debug:
	buildozer android debug deploy run logcat

.PHONY: adb-run
adb-run:
	buildozer android release deploy run logcat

run: c.profile
	python main.py

.PHONY: test
test:
	python test.py

dump: app_data/mock/*.dump
	python dump.py