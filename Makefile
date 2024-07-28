.PHONY: test
test:
	python -m pytest

build:
	python3 -m pip install --upgrade build
	python3 -m build

clean: clean_src
	-rm -r build dist __pycache__

clean_src:
	-rm -r src/__pycache__
