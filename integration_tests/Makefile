.PHONY: test-setup test myservice

myservice:
	docker build -t myservice -f assets/common/Dockerfile_myservice assets/common

test-setup: myservice
	docker pull n3llyb0y/wait
	docker pull rabbitmq
	docker pull progrium/consul

test:
	nosetests suite
