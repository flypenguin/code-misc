all: prepare cbuild build_containers

prepare:
	./build.sh prepare

hbuild:
	rm -f go_server
	go get github.com/gorilla/mux
	go build -v -o go_server

cbuild:
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
