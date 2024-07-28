.PHONY: test
test:
	python -m pytest

build:
	python3 -m pip install --upgrade build
	python3 -m build

push_test:
	python3 -m pip install --upgrade twine
	python3 -m twine upload --repository testpypi dist/*

push:
	python3 -m pip install --upgrade twine
	python3 -m twine upload dist/*


clean: clean_src
	-rm -r build dist __pycache__

clean_src:
	-rm -r src/__pycache__
