SHELL := bash
DEBUG ?= 0
PYTHON_VERSION ?= 3.12
BUILD_ARCHITECTURES ?= amd64 arm64
BUILD_ARCH ?= ::BUILD_ARCH not set in env::
DAGSTER_VERSION ?= ::DAGSTER_VERSION not set in env::

ARCH_SUFFIX_SEPARATOR ?= -

IMAGE_REGISTRY ?= docker.io
IMAGE_REPOSITORY ?= flypenguin
IMAGE_NAME ?= k8s-dagster-dummy
IMAGE_BASE ?= $(IMAGE_REGISTRY)/$(IMAGE_REPOSITORY)/$(IMAGE_NAME)
ARCH_SUFFIX = $(ARCH_SUFFIX_SEPARATOR)$(BUILD_ARCH)

TAG = py$(PYTHON_VERSION)-dg$(DAGSTER_VERSION)
IMAGE = $(IMAGE_BASE):$(TAG)
IMAGE_LATEST = $(IMAGE_BASE):latest
BUILD_DIR = build.tmp/$(TAG)

ARCH_TAG = $(TAG)$(ARCH_SUFFIX)
ARCH_IMAGE = $(IMAGE)$(ARCH_SUFFIX)
ARCH_IMAGE_LATEST = $(IMAGE_LATEST)$(ARCH_SUFFIX)
ARCH_BUILD_DIR = $(BUILD_DIR)$(ARCH_SUFFIX)

export BUILD_ARCHITECTURES
export BUILD_ARCH
export DAGSTER_VERSION
export PYTHON_VERSION
export DEBUG


default: build
.PHONY: default


clean:
	rm -rf build.*
.PHONY: build


superclean: clean
	rm -rf configfiles
.PHONY: superclean


build:
	@\
DEBUG=$(DEBUG) ; source helper.sh ; \
get_engine ; \
cat dagster-versions.txt \
| sort -V \
| while read DAGSTER_VERSION ; do \
  for BUILD_ARCH in $(BUILD_ARCHITECTURES) ; do \
    export PYTHON_VERSION BUILD_ARCH DAGSTER_VERSION ; \
    make _build_$${ENGINE}_single ; \
  done ; \
  make _create_manifest_$${ENGINE} ; \
done
.PHONY: build


push:
	@\
DEBUG=$(DEBUG) ; source helper.sh ; \
get_engine ; \
cat dagster-versions.txt \
| sort -V \
| while read DAGSTER_VERSION ; do \
    export BUILD_ARCHITECTURES PYTHON_VERSION BUILD_ARCH DAGSTER_VERSION ; \
    make _push_manifest_$${ENGINE} ; \
done
.PHONY: push


all: build push
.PHONY: all


_create_uv_lock:
	@\
DEBUG=$(DEBUG) ; source helper.sh ; _RUN_LOG_FILE="build-$(ARCH_TAG).log" ; _RUN_LOG_APPEND=1 ; \
export DAGSTER_VERSION="$(DAGSTER_VERSION)" ; \
export PYTHON_VERSION="$(PYTHON_VERSION)" ; \
export BUILD_ARCH="$(BUILD_ARCH)" ; \
DIR="configfiles/$(ARCH_TAG)" ; \
if [[ ! -d "$${DIR}" ]] ; then \
  echo "Generating config files for Python $(PYTHON_VERSION), Dagster $(DAGSTER_VERSION), arch $(BUILD_ARCH) ..." ; \
  mkdir -p "$${DIR}" ; \
  envsubst < _templates/pyproject.toml.template > "$${DIR}/pyproject.toml" ; \
  ( cd "$${DIR}" ; uv lock -p $(PYTHON_VERSION) ) ; \
else \
  echo "Config files for Python $(PYTHON_VERSION), Dagster $(DAGSTER_VERSION), arch $${BUILD_ARCH} exist." ; \
fi
.PHONY: _create_uv_lock


_build_podman_single: _create_uv_lock
	@\
[[ -n "$(BUILD_ARCH)" ]] ; \
DEBUG=$(DEBUG) ; source helper.sh ; _RUN_LOG_FILE="build-$(ARCH_TAG).log" ; _RUN_LOG_APPEND=1 ; \
rm -rf "$(ARCH_BUILD_DIR)}" ; mkdir -p "$(ARCH_BUILD_DIR)" ; \
cp -ar "configfiles/$(ARCH_TAG)/"* _templates/src _templates/Dockerfile "$(ARCH_BUILD_DIR)/" ; \
cd "$(ARCH_BUILD_DIR)" ; \
_RUN_IGNORE_ERRORS=1 podman image exists "$(ARCH_IMAGE)" && _run podman rmi "$(ARCH_IMAGE)" ; \
_run podman build \
    -f Dockerfile \
    --arch=$(BUILD_ARCH) \
    --build-arg PYTHON_BASE=$(PYTHON_VERSION) \
    --no-cache \
    -t "$(ARCH_IMAGE)" ; \
_RUN_ECHO_ONCE=1 \
  _run podman image inspect "$(ARCH_IMAGE)" --format '{{.Digest}}' ; \
echo "$(ARCH_IMAGE)" > IMAGE_NAME
.PHONY: _build_podman_single


_create_manifest_podman:
	@\
DEBUG=$(DEBUG) ; source helper.sh ; _RUN_LOG_FILE="build-$(TAG).log" ; _RUN_LOG_APPEND=1 ; \
rm -rf "$(BUILD_DIR)" ; mkdir -p "$(BUILD_DIR)" ; cd "$(BUILD_DIR)" ; \
[[ "$(DEBUG)" != "1" ]] || set -x ; \
rm -f BUILT_IMAGES ; \
for ARCH_DIR in "../$(TAG)-"* ; do \
  cat "$${ARCH_DIR}/IMAGE_NAME" >> BUILT_IMAGES ; \
done ; \
BUILT_IMAGES="$$(cat BUILT_IMAGES | tr "\n" " " | xargs | sed -E 's/ +/ /g')" ; \
for USE_TAG in "$(TAG)" "latest" ; do \
  MANIFEST="$(IMAGE_BASE):$${USE_TAG}" ; \
  _RUN_IGNORE_ERRORS=1 _run podman manifest exists "$${MANIFEST}" && _run podman manifest rm "$${MANIFEST}" || true ; \
  _RUN_IGNORE_ERRORS=1 _run podman image    exists "$${MANIFEST}" && _run podman rmi         "$${MANIFEST}" || true ; \
  _run podman manifest create "$(IMAGE_BASE):$${USE_TAG}" $${BUILT_IMAGES} ; \
done
.PHONY: _create_manifest


_push_manifest_podman:
	@\
DEBUG=$(DEBUG) ; source helper.sh ; _RUN_LOG_FILE="build-$(TAG).log" ; _RUN_LOG_APPEND=1 ; \
BUILT_IMAGES="$$(cat "$(BUILD_DIR)/BUILT_IMAGES" | tr "\n" " " | xargs | sed -E 's/ +/ /g')" ; \
_run podman manifest push --all "$(IMAGE)" ; \
_run podman manifest push --all "$(IMAGE_LATEST)" ; \
for USE_TAG in $(TAG) "latest" ; do \
  for BUILD_ARCH in $(BUILD_ARCHITECTURES) ; do \
    ARCH_SUFFIX="$(ARCH_SUFFIX_SEPARATOR)$${BUILD_ARCH}" ; \
    SOURCE_IMAGE="$(IMAGE)$${ARCH_SUFFIX}" ; \
    PUSH_IMAGE="$(IMAGE_BASE):$${USE_TAG}$${ARCH_SUFFIX}" ; \
    _run podman image push "$$SOURCE_IMAGE" "$$PUSH_IMAGE" ; \
  done ; \
done
.PHONY: _push_manifest
