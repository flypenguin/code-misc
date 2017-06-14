#!/usr/bin/env bash 

if [ "$1" == "build" ] ; then

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

fi