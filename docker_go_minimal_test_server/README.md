# Minimal go server for docker testing

There is a build script which will build - by default - two docker containers. If you run them and `curl` port 80, they will return either `RED`or `GREEN`. 

This is useful for quick deployment testing with orchestration tools (answer the questions "does deployment work?" etc.)

# Quickstart

```bash
$ ./build.sh RED GREEN BLUE   # the parameters are optional
[...]
$ docker run --rm -ti -p 8080:80 test_server:red

[-open-new-terminal-]
$ curl localhost:8080
RED
$ _
```


## Code notes

The code was initially copied from here: `https://golang.org/doc/articles/wiki/`.


## General notes

RED and GREEN are always available on the docker hub as `flypenguin/test_server:red` and `flypenguin/test_server:green`. `flypenguin/test_server` will point to a random version just as I need it right now ;) .


## Mac notes

* By default it will compile everything for Linux. If you don't want this just set the ENV variables `$GOOS` and `$GOARCH` (could thia be ANY easier?!? :)
* You need to use docker-machine to run the things of course
