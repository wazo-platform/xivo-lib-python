.PHONY: test-setup test myservice

myservice:
	docker build -t myservice -f assets/Dockerfile_myservice ..

test-setup: myservice
	docker pull progrium/consul
	docker pull rabbitmq
	docker pull wazopbx/wait

test:
	nosetests suite
