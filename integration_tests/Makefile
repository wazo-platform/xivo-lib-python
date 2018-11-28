.PHONY: egg-info test-setup test myservice thread-exception

egg-info:
	cd .. && python setup.py egg_info

myservice:
	docker build -t myservice -f Dockerfile-myservice ..

test-setup: myservice thread-exception egg-info
	docker pull progrium/consul
	docker pull rabbitmq
	docker pull wazopbx/wait
	docker pull python:3.5-slim-stretch

test:
	nosetests suite

thread-exception:
	docker build -t thread-exception -f Dockerfile-thread-exception ..
