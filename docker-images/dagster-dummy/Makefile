SHELL := bash
DEBUG ?= 0

PYTHON_VERSION ?= 3.12
# dagster does not support ARM64 ... :((
BUILD_ARCHITECTURES ?= amd64
BUILD_ARCH ?= this is not set in env
DAGSTER_VERSION ?= this is not set in env

ARCH_SUFFIX_SEPARATOR ?= -

IMAGE_REGISTRY ?= docker.io
IMAGE_REPOSITORY ?= flypenguin
IMAGE_NAME ?= k8s-dagster-dummy
IMAGE_BASE ?= $(IMAGE_REGISTRY)/$(IMAGE_REPOSITORY)/$(IMAGE_NAME)
ARCH_SUFFIX = $(ARCH_SUFFIX_SEPARATOR)$(BUILD_ARCH)

TAG = py$(PYTHON_VERSION)-dg$(DAGSTER_VERSION)
IMAGE = $(IMAGE_BASE):$(TAG)
BUILD_DIR = build.tmp/$(TAG)

ARCH_TAG = $(TAG)$(ARCH_SUFFIX)
ARCH_IMAGE = $(IMAGE)$(ARCH_SUFFIX)
ARCH_BUILD_DIR = $(BUILD_DIR)$(ARCH_SUFFIX)


default: build
.PHONY: default


clean:
	rm -rf build.*
.PHONY: build


_helper:
	@\
printf '\
_run() { \
  DEBUG="$(DEBUG)" ; DEBUG="${DEBUG:-0}" ; \
  (( DEBUG > 1 )) && return 0 ; \
  local LOG="$$1" ; shift ; local RV=0 ; \
  [[ "$${LOG_APPEND:-}" == "1" ]] || rm -f "$$LOG" ; \
  echo -e "COMMAND: $$@\n\n" >> "$$LOG" ; \
  echo ">>> $$@" ; \
  "$$@" >> "$$LOG" 2>&1 || RV=$? ; \
  if [[ "$$RV" != "0" ]] ; then cat "$$LOG" ; return 1 ; fi ; \
  [[ "$${LOG_APPEND:-}" != "1" ]] || echo -e "\n\n" >> "$$LOG" ; \
} ; \
chkcmd() { command -v "$$1" > /dev/null ; } ; \
silent() { "$$@" > /dev/null 2>&1 ; } ; \
export \
  PYTHON_VERSION="$(PYTHON_VERSION)" \
  DAGSTER_VERSION="$(DAGSTER_VERSION)"  \
  BUILD_ARCH="$(BUILD_ARCH)" \
; \
'
.PHONY: _helper


build:
	@\
set -euo pipefail ; \
eval $$(make _helper) ; \
chkcmd docker && BUILDER=docker ; \
chkcmd podman && BUILDER=podman ; \
if [[ -z "$${BUILDER:-}" ]]; then \
  echo "ERROR: no suitable build app found." ; \
  false ; \
fi ; \
echo "Using builder: $$BUILDER" ; \
cat dagster-versions.txt \
| sort -V \
| while read DAGSTER_VERSION ; do \
  for BUILD_ARCH in $(BUILD_ARCHITECTURES) ; do \
    export \
      PYTHON_VERSION="$(PYTHON_VERSION)" \
      DAGSTER_VERSION="$${DAGSTER_VERSION}" \
      BUILD_ARCH="$${BUILD_ARCH}" ; \
    make _build_$${BUILDER}_single ; \
  done ; \
  make _create_manifest_$${BUILDER} ; \
  make _push_manifest_$${BUILDER} ; \
done
.PHONY: build


_create_uv_lock:
	@\
set -euo pipefail ; \
eval $$(make _helper) ; \
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


_build_podman_single:
	@\
[[ "$(DEBUG)" != "1" ]] || set -x ; \
[[ -n "$(BUILD_ARCH)" ]] ; \
set -euo pipefail ; \
eval $$(make _helper) ; \
make _create_uv_lock ; \
rm -rf "$(ARCH_BUILD_DIR)}" ; mkdir -p "$(ARCH_BUILD_DIR)" ; \
cp -ar "configfiles/$(ARCH_TAG)/"* _templates/src _templates/Dockerfile "$(ARCH_BUILD_DIR)/" ; \
cd "$(ARCH_BUILD_DIR)" ; \
_run "podman-$(BUILD_ARCH)-build.log" \
  podman build \
    -f Dockerfile \
    --arch=$(BUILD_ARCH) \
    --build-arg PYTHON_BASE=$(PYTHON_VERSION) \
    -t "$(ARCH_IMAGE)" ; \
echo "$(ARCH_IMAGE)" > IMAGE_NAME
.PHONY: _build_podman_single


_create_manifest_podman:
	@\
eval $$(make _helper) ; \
rm -rf "$(BUILD_DIR)" ; mkdir -p "$(BUILD_DIR)" ; cd "$(BUILD_DIR)" ; \
for ARCH_DIR in "../$(TAG)-"* ; do \
  cat "$${ARCH_DIR}/IMAGE_NAME" >> BUILT_IMAGES ; \
done ; \
BUILT_IMAGES="$(cat BUILT_IMAGES | tr "\n" " " | xargs | sed -E 's/ +/ /g')" ; \
for USE_TAG in "$(TAG)" "latest" ; do \
  MANIFEST="$(IMAGE_BASE):$${USE_TAG}" ; \
  podman manifest exists "$${MANIFEST}" \
    && podman manifest remove "$${MANIFEST}" \
    || true ; \
  _run "podman-manifest-$${USE_TAG}-create.log" \
    podman manifest \
      create "$(IMAGE_BASE):$${USE_TAG}" $${BUILT_IMAGES} ; \
done
.PHONY: _create_manifest


_push_manifest_podman:
	@\
eval $$(make _helper) ; \
for USE_TAG in "$(TAG)" "latest" ; do \
  _run "podman-manifest-$${USE_TAG}-push.log" \
    podman manifest \
      push --all "$(IMAGE_BASE):$${USE_TAG}" ; \
done
.PHONY: _push_manifest
