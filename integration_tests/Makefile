.PHONY: test-setup test myservice

myservice:
	docker build -t myservice -f assets/common/Dockerfile_myservice ..

test-setup: myservice
	docker pull progrium/consul
	docker pull rabbitmq
	docker pull waisbrot/wait

test:
	nosetests suite
