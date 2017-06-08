#!/usr/bin/env bash

export GOARCH=${GOARCH:-amd64}
export GOOS=${GOOS:-linux}

COLORS=${@:-RED GREEN}

echo "Building colors: $COLORS"
echo "Using GOOS:      $GOOS"
echo "Using GOARCH:    $GOARCH"

set -e


for color in $COLORS ; do

	color_lower=$(echo $color | tr '[[:upper:]]' '[[:lower:]]' )

	rm -rf "go_server_${color_lower}" "Dockerfile.${color_lower}" server.go

	echo ""

	echo "Compiling binary for color '${color_lower}' ..."
	cat server.go.template | sed "s/RED/$color/g" > server.go
	go build -o go_server_${color_lower}

	echo "Building docker container 'test_server_${color_lower}' ..."
	cat Dockerfile.template | sed "s/RED/${color_lower}/g" > "Dockerfile.${color_lower}" 
	docker build \
	     -t "test_server:${color_lower}" \
	     -f "Dockerfile.${color_lower}" \
	     . \
	     > docker_build.log 2>&1

	# always clean the build log if it succeeded.
	rm docker_build.log

done

echo ""

# tag the :latest image with the last used color
echo "Tagging test_server:${color_lower} as :latest ..."
docker tag "test_server:${color_lower}" test_server:latest

# keep the Dockerfiles for manual fiddling, also keep the binaries in case
# you still need them.

echo ""

# so we're ...
echo "Done."
