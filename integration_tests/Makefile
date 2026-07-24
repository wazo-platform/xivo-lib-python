egg-info:
	cd .. && python setup.py egg_info

myservice:
	docker build -t myservice -f Dockerfile-myservice ..

test-setup: myservice thread-exception wsgi-patch dynamic-wsgi egg-info

test:
	pytest suite

thread-exception:
	docker build -t thread-exception -f Dockerfile-thread-exception ..

wsgi-patch:
	docker build -t wsgi-patch -f Dockerfile-wsgi-patch ..

dynamic-wsgi:
	docker build -t dynamic-wsgi -f Dockerfile-dynamic-wsgi ..

.PHONY: egg-info test-setup test myservice thread-exception dynamic-wsgi
