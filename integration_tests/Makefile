.PHONY: egg-info test-setup test myservice thread-exception config-from-consul

egg-info:
	cd .. && python setup.py egg_info

myservice:
	docker build -t myservice -f Dockerfile-myservice ..

test-setup: myservice thread-exception egg-info
	docker pull consul
	docker pull rabbitmq
	docker pull wazopbx/wait
	docker pull python:3.7-slim-buster

test:
	nosetests suite

thread-exception:
	docker build -t thread-exception -f Dockerfile-thread-exception ..

config-from-consul:
	docker build -t config-from-consul -f Dockerfile-config-from-consul ..
