all:
	@echo "Did nothing..."

setup:
	mkdir -p root/

test_1:
	python -m unittest rest_test
test_2:
	python -m unittest fs_test
test_3:
	python -m unittest httpd_test

test: test_1 test_2 test_3
