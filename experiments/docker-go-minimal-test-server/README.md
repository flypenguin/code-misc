# Minimal go server for docker testing

A minimal test server returning the first argument of the command line back if you curl `/`. This is useful for quick deployment testing with orchestration tools (answer the questions "does deployment work?" etc.)

Please use the `Makefile` to get your stuff done.


# Quickstart

```bash
$ make
[...]
$ make run


# open-new-terminal

$ curl localhost:8080
[a cool color]

$ _
```


## go_server notes

The server has the following endpoints:

```
/                   -> <a color string>
/health             -> "OK"
/allocate/{NUM}     -> NUM is a number. NUM megabytes will be allocated, {ID} is returned
/deallocate/{ID}    -> deallocates the memory block with ID {ID}
/allocations        -> prints a list of all allocations
```


## Code notes

The code was initially copied from here: `https://golang.org/doc/articles/wiki/`.


## General notes

The image is available on the docker hub as `flypenguin/test_server` and `flypenguin/test_server:A_LOT_OF_COLORS`. The tags can be found in the `colors` file or [on docker hub](https://hub.docker.com/r/flypenguin/test_server/).


## Mac notes

* I did not try compiling on Mac with the new version. We compile *inside* docker now, and for this you need to mount a Workdir into the container. As said, not tried yet.
