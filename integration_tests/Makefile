egg-info:
	cd .. && python setup.py egg_info

myservice:
	docker build -t myservice -f Dockerfile-myservice ..

test-setup: myservice thread-exception wsgi-patch egg-info

test:
	pytest suite

thread-exception:
	docker build -t thread-exception -f Dockerfile-thread-exception ..

wsgi-patch:
	docker build -t wsgi-patch -f Dockerfile-wsgi-patch ..

.PHONY: egg-info test-setup test myservice thread-exception
