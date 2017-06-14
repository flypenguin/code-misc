#!/usr/bin/env bash 

if [ "$1" == "source" ] ; then

    docker run --rm -ti \
        -v $(pwd):/go/src/app \
        -w /go/src/app \
        golang:alpine \
        go build -v -o go_server

elif [ "$1" == "containers" ] ; then

    cp Dockerfile.template Dockerfile
    docker build -t flypenguin/test_server:latest .
    cat colors | while read color ; do
        cat Dockerfile.template | sed "s/default/$color/g" > Dockerfile
        docker build -t flypenguin/test_server:$color .
    done

elif [ "$1" == "push" ] ; then

    docker push flypenguin/test_server:latest
    cat colors | while read color ; do
        docker push flypenguin/test_server:$color
    done

elif [ "$1" == "clean" ] ; then

    docker rmi flypenguin/test_server:latest
    cat colors | while read color ; do
        docker rmi flypenguin/test_server:$color
    done

fi