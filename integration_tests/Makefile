.PHONY: test-setup test myservice

myservice:
	docker build -t myservice -f assets/service_discovery/Dockerfile_myservice assets/service_discovery

test-setup: myservice
	docker pull n3llyb0y/wait
	docker pull rabbitmq
	docker pull progrium/consul

test:
	nosetests suite
