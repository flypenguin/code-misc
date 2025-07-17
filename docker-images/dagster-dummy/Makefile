SHELL := bash
DEBUG ?= 0

PYTHON_VERSION ?= 3.12
BUILD_ARCHITECTURES ?= arm64 amd64

ARCH_SUFFIX_SEPARATOR ?= -

IMAGE_REGISTRY ?= docker.io
IMAGE_REPOSITORY ?= flypenguin
IMAGE_NAME ?= k8s-dagster-dummy



build:
	@\
set -euo pipefail ; \
chkcmd() { command -v "$$1" > /dev/null ; } ; \
chkcmd podman && BUILDER=podman ; \
chkcmd docker && BUILDER=docker ; \
if [[ -z "$${BUILDER:-}" ]]; then \
  echo "ERROR: no suitable build app found." ; \
  false ; \
fi ; \
echo "Using builder: $$BUILDER" ; \
cat dagster-versions.txt | sort -V | while read version ; do \
  export DAGSTER_VERSION=$$version ; \
  make _build_$$BUILDER ; \
done ;
.PHONY: build


clean:
	rm -rf build.*
.PHONY: build


_create_uv_lock:
	@\
set -euo pipefail ; \
[[ "$(DEBUG)" != "1" ]] || set  ; \
export DAGSTER_VERSION="$(DAGSTER_VERSION)" ; \
export PYTHON_VERSION="$(PYTHON_VERSION)" ; \
for BUILD_ARCH in $(BUILD_ARCHITECTURES) ; do \
  KEY="py$(PYTHON_VERSION)-dg$(DAGSTER_VERSION)$(ARCH_SUFFIX_SEPARATOR)$${BUILD_ARCH}" ; \
  DIR="configfiles/$${KEY}" ; \
  if [[ ! -d "$$DIR" ]] ; then \
    echo "Generating config files for Python $(PYTHON_VERSION), Dagster $(DAGSTER_VERSION), arch $${BUILD_ARCH} ..." ; \
    mkdir -p "$${DIR}" ; \
    envsubst < _templates/pyproject.toml.template > "$${DIR}/pyproject.toml" ; \
    ( cd "$${DIR}" ; uv lock -p $(PYTHON_VERSION) ) ; \
  else \
    echo "Config files for Python $(PYTHON_VERSION), Dagster $(DAGSTER_VERSION), arch $${BUILD_ARCH} exist." ; \
  fi ; \
done
.PHONY: _create_uv_lock


_build_podman: _create_uv_lock
	@\
_run() { \
  (( $(DEBUG) > 1 )) && return 0 ; \
  local LOG="$$1" ; shift ; local RV=0 ; \
  [[ "$${LOG_APPEND:-}" == "1" ]] || rm -f "$$LOG" ; \
  echo -e "COMMAND: $$@\n\n" >> "$$LOG" ; \
  echo ">>> $$@" ; \
  "$$@" >> "$$LOG" 2>&1 || RV=$? ; \
  if [[ "$$RV" != "0" ]] ; then cat "$$LOG" ; return 1 ; fi ; \
  [[ "$${LOG_APPEND:-}" != "1" ]] || echo -e "\n\n" >> "$$LOG" ; \
} ; \
silent() { "$$@" > /dev/null 2>&1 ; } ; \
[[ "$(DEBUG)" != "1" ]] || set -x ; \
set -euo pipefail ; \
TAG="py$(PYTHON_VERSION)-dg$(DAGSTER_VERSION)" ; \
IMAGE_BASE="$(IMAGE_REGISTRY)/$(IMAGE_REPOSITORY)/$(IMAGE_NAME)" ; \
IMAGE="$${IMAGE_BASE}:$${TAG}" ; \
LATEST="$${IMAGE_BASE}:latest" ; \
BUILT_IMAGES="" ; \
BUILD_BASE="build.tmp/$${TAG}" ; \
for BUILD_ARCH in $(BUILD_ARCHITECTURES) ; do \
  silent pushd . ; \
  ARCH_SUFFIX="$(ARCH_SUFFIX_SEPARATOR)$${BUILD_ARCH}" ; \
  BUILD_DIR="$${BUILD_BASE}$${ARCH_SUFFIX}" ; \
  ARCH_TAG="$${TAG}$${ARCH_SUFFIX}" ; \
  ARCH_IMAGE="$${IMAGE}$${ARCH_SUFFIX}" ; \
  if [[ ! -d "$$BUILD_DIR" ]]; then \
    mkdir -p "$$BUILD_DIR" ; \
    cp -ar "configfiles/$${ARCH_TAG}/"* _templates/src _templates/Dockerfile "$$BUILD_DIR/" ; \
  fi ; \
  cd "$$BUILD_DIR" ; \
  rm -f *.log ; \
  LOGFILE= ; \
  _run "podman-$${BUILD_ARCH}-build.log" \
    podman build \
      -f Dockerfile \
      --arch=$${BUILD_ARCH} \
      --build-arg PYTHON_BASE=$(PYTHON_VERSION) \
      -t "$${ARCH_IMAGE}" ; \
  _run "podman-$${BUILD_ARCH}-push.log" \
    podman push \
      "$${ARCH_IMAGE}" ; \
  BUILT_IMAGES="$${BUILT_IMAGES} $${ARCH_IMAGE}" ; \
  echo "$$ARCH_IMAGE" > IMAGE.log ; \
  silent popd ; \
done ; \
mkdir -p "$$BUILD_BASE" ; cd "$$BUILD_BASE" ; \
echo "$$BUILT_IMAGES" | xargs | sed -E 's/ +/\n/g' > BUILT_IMAGES ; \
for USE_TAG in "$${TAG}" "latest" ; do \
  _run "podman-manifest-$${USE_TAG}-create.log" \
    podman manifest \
      create -a "$${IMAGE_BASE}:$${USE_TAG}" $${BUILT_IMAGES} ; \
  _run "podman-manifest-$${USE_TAG}-push.log" \
    podman manifest \
      push --all "$${IMAGE_BASE}:$${USE_TAG}" ; \
done ;
.PHONY: _build_podman
