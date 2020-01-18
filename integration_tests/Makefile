egg-info:
	cd .. && python setup.py egg_info

myservice:
	docker build -t myservice -f Dockerfile-myservice ..

test-setup: myservice thread-exception egg-info

test:
	nosetests suite

thread-exception:
	docker build -t thread-exception -f Dockerfile-thread-exception ..

.PHONY: egg-info test-setup test myservice thread-exception
