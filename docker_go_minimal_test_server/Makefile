all: goserver containers

goserver:
	go build -o go_server

containers:
	./build.sh build

push:
	./build.sh push

