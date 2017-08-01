all: prepare build_source_container build_containers

prepare:
	./build.sh prepare

host:
	rm -f go_server
	go build -v -o go_server

build_source_container:
	rm -f go_server
	./build.sh source

build_containers:
	./build.sh containers

push:
	./build.sh push

clean:
	./build.sh clean
	rm -f go_server
	rm -f Dockerfile

run:
	docker run -ti -p 80:8080 flypenguin/test_server
