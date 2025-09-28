SHELL = bash

THIS_MAKEFILE := $(lastword $(MAKEFILE_LIST))
MAKEFILE_DIR := $(dir $(THIS_MAKEFILE))

KIND_CLUSTER_NAME := test-dex-authelia

KCMD = kubectl --context kind-$(KIND_CLUSTER_NAME)
HCMD = helm --kube-context kind-$(KIND_CLUSTER_NAME)

AUTHELIA_USERS_CSV = config-files/authelia-users.csv
AUTHELIA_USERS_CSV_TMPL = templates/authelia-users.csv.template
AUTHELIA_USERS_HASHES_YAML = config-files/authelia-password-hashes.yaml
AUTHELIA_USERS_K8S_SECRET = helm-charts/managed-objects/templates/authelia-local-users-database.yaml

CLUSTER_HIGH_PORT_HTTPS = 8443
CLUSTER_HIGH_PORT_HTTP = 8080
CLUSTER_URL = localhost.traefik.me
CLUSTER_CREATE_NAMESPACES = authelia-local authelia-ldap

LOCAL_CHART_VALUES_FILES := $(wildcard helm-values-files/local-*.yaml)
EXTERNAL_CHART_VALUES_FILES := $(wildcard helm-values-files/values-*.yaml)
ALL_VALUES := $(wildcard helm-values-files/*.yaml)
HELM_DEPLOY := $(ALL_VALUES:helm-values-files/%.yaml=helm-values-files/.deploy/%.txt)

SCRIPT_START = cd $(MAKEFILE_DIR) ; set -euo pipefail

# FUCK ME.
# Note that "$(1)" is the ONLY THING that is not "double-escaped", because this is
# the parameter which is filled in. _that_ should be returned _replaced_, and all
# the other stuff should _not_ be evaluated just now.
# why?
# because the "eval()" call below should see the dollar signs, and THEN evaluate
# them.
define LOCAL_DEPENDENCIES=
file_only = $$(notdir $(1))
file_stem = $$(basename $$(file_only))
inner_stem = $$(subst local-,,$$(basename $$(file_stem)))
helm-values-files/.deploy/$$(file_stem).txt: \
  helm-values-files/$$(file_only) \
  helm-charts/$$(inner_stem)/values.yaml \
  helm-charts/$$(inner_stem)/.helmignore \
  $$(wildcard helm-charts/$$(inner_stem)/templates/*.yaml)
  $$(wildcard helm-charts/$$(inner_stem)/templates/*.yml)
endef

# dynamically add the dependencies to the target below.
$(foreach file,$(LOCAL_CHART_VALUES_FILES),$(eval $(call LOCAL_DEPENDENCIES, $(file))) )


#
# Some notes:
#   - for LOCAL deployments there is no namespace. the namespace should be
#     part of the managed objects.
#   - ... that's it.
#
helm-values-files/.deploy/%.txt: helm-values-files/%.yaml
	@$(SCRIPT_START) ; \
	TARGET="$@" ; FILENAME="$${TARGET##*/}" ; DIRNAME="$${TARGET%/*}" ; \
	STEM="$${FILENAME%.*}" ; INNER_STEM="$${STEM#*-}" ; INNER_STEM="$${INNER_STEM%%.*}" ; \
	VALUES_FILE="helm-values-files/$$STEM.yaml" ; \
	VALUES_FILE_NAME="$${VALUES_FILE##*/}" ; \
	mkdir -p "$$DIRNAME" ;  rm -f "$$FILENAME" "$$FILENAME.tmp" ; \
	if [[ "$$FILENAME" == "local-"* ]]; then \
	  if ! echo "$$VALUES_FILE_NAME" | grep -Eq '^local-[^.]+\.[^.]+\.yaml' ; then \
	    echo -e "\nERROR:    Values file does not match pattern: 'local-CHART.SUFFIX.yaml'. Aborting." ; \
	    echo -e "FILENAME: $$VALUES_FILE_NAME\n" ; \
	    false ; \
	  fi ; \
	  VALUE_SUFFIX="$${STEM#*.}" ; \
	  DEFAULT_NAMESPACE="$${VALUE_SUFFIX}" ; \
	  CHART="./helm-charts/$${INNER_STEM}" ; \
	  DEPLOYMENT_NAME="$${VALUE_SUFFIX}" ; \
	else \
	  DEFAULT_NAMESPACE="$$INNER_STEM" ; \
	  CHART="$$(cat $$VALUES_FILE | grep -E '##:CHART')" ; CHART="$${CHART##* }" ; \
	  DEPLOYMENT_NAME="$${INNER_STEM}" ; \
	fi ; \
	if [[ -z "$$CHART" ]] ; then \
	  echo "ERROR: No chart found. Aborting." ; false ; \
	fi ; \
	NS="$$(cat $$VALUES_FILE | grep -E '##:NAMESPACE' || true)" ; NS="$${NS##* }" ; \
	[[ -z "$$NS" ]] && NS="$${DEFAULT_NAMESPACE}" ; \
	[[ "$$NS" == "-" ]] && NS="" ; \
	[[ -n "$$NS" ]] && NS="-n $$NS" ; \
	(\
	  set -x ; \
	  helm upgrade -i --create-namespace $$NS -f "$$VALUES_FILE" $$DEPLOYMENT_NAME $$CHART > "$$TARGET.tmp" 2>&1 \
	) && mv "$$TARGET.tmp" "$$TARGET" || (cat $$TARGET.tmp ; rm "$$TARGET.tmp" ; touch .deploy_error)



$(AUTHELIA_USERS_CSV):
	@$(SCRIPT_START) ; \
	if [[ -f "$@" ]]; then touch "$@" ; \
	else cp -v "$(AUTHELIA_USERS_CSV_TMPL)" "$(AUTHELIA_USERS_CSV)" ; \
	fi ; \


$(AUTHELIA_USERS_HASHES_YAML): $(AUTHELIA_USERS_CSV)
	@$(SCRIPT_START) ; \
	echo "# this file is re-generated using 'make prepare-users'. do not edit." \
	  > $@ ; \
	./create-users.py "$(AUTHELIA_USERS_CSV)" >> "$@" ; \
	echo "Created file: $@"


$(AUTHELIA_USERS_K8S_SECRET): $(AUTHELIA_USERS_HASHES_YAML)
	@$(SCRIPT_START) ; \
	if
	sed -Ei '/users_database.yml/d' $@ ; \
	$(KCMD) create secret \
	  generic \
	  -n authelia-local \
	  authelia-local-users-database \
	  --from-file=users_database.yml=$(AUTHELIA_USERS_HASHES_YAML) \
	  --dry-run=client \
	  -o yaml \
	| grep users_database.yml \
	>> $@ \
	&& echo "Updated file: $@" \
	|| false


clean-users:
	@rm -fv $(AUTHELIA_USERS_K8S_SECRET)
	@rm -fv $(AUTHELIA_USERS_HASHES_YAML)
.PHONY: clean-users


clean:
	@rm -rfv helm-values-files/.deploy
.PHONY: clean


deploy-helm: $(HELM_DEPLOY)
.PHONY: deploy-helm


reverse-proxy:
	caddy run --watch
loadbalancer: reverse-proxy


lb: reverse-proxy
caddy: reverse-proxy
.PHONY: reverse-proxy loadbalancer lb caddy


ingress-test:
	@for TUPLE in \
	  http,foo.,:$(CLUSTER_HIGH_PORT_HTTP),/ \
	  http,xxx.,:$(CLUSTER_HIGH_PORT_HTTP),/ingress-test-foo \
	  http,foo.,,/ \
	  http,xxx.,,/ingress-test-foo \
	  https,foo.,:$(CLUSTER_HIGH_PORT_HTTPS),/ \
	  https,xxx.,:$(CLUSTER_HIGH_PORT_HTTPS),/ingress-test-foo \
	  https,foo.,,/ \
	  https,xxx.,,/ingress-test-foo ; \
	do \
	  IFS=, read PROTO HOST PORT CPTH <<< $$TUPLE ; \
	  CURL_ME="$$PROTO://$${HOST}$(CLUSTER_URL)$${PORT}$${CPTH}" ; \
	  ANSWER="$$(set -x ; curl --insecure -s "$${CURL_ME}")" ; \
	  [[ "$$ANSWER" == "ingress-test-foo" ]] && echo "   ... ok" || echo "   ... NOPE." ; \
	done
.PHONY: ingress-test


_select_engine:
	@cd "$(MAKEFILE_DIR)" ; \
	set -euo pipefail ; \
	[[ -f .cluster_type ]] && source .cluster_type ; \
	if [[ -z "$${CLUSTER_TYPE:-}" ]] ; then \
	  CLUSTER_TYPE=$$(echo -e "podman\ndocker\n" | fzf --height=~100%) ; \
	  echo "CLUSTER_TYPE=$$CLUSTER_TYPE" > .cluster_type ; \
	fi
.PHONY: _select_engine


delete-cluster: _select_engine clean clean-users
	@cd "$(MAKEFILE_DIR)" ; \
	set -euo pipefail ; source .cluster_type ; \
	if [[ "$$CLUSTER_TYPE" == "podman" ]] ; then \
	  export KIND_EXPERIMENTAL_PROVIDER=podman ; \
	fi ; \
	if kind get clusters | grep -q $(KIND_CLUSTER_NAME) ; then \
	  echo " * Deleting kind cluster '$(KIND_CLUSTER_NAME)' ..." ; \
	  set -x ; \
	  kind delete cluster -n $(KIND_CLUSTER_NAME) ; \
	else \
	  echo "Nothing to delete ... ?" ; \
	fi
.PHONY: delete-cluster


create-cluster: _select_engine
	@cd "$(MAKEFILE_DIR)" ; \
	set -euo pipefail ; source .cluster_type ; \
	if [[ "$$CLUSTER_TYPE" == "podman" ]] ; then \
	  export KIND_EXPERIMENTAL_PROVIDER=podman ; \
	fi ; \
	if ! kind get clusters | grep -q $(KIND_CLUSTER_NAME) ; then \
	  echo " * Creating kind cluster '$(KIND_CLUSTER_NAME)' ..." ; \
	  make clean ; \
	  make clean-users ; \
	  kind create cluster --config ./config-files/kind-cluster.yaml -n $(KIND_CLUSTER_NAME) ; \
	fi
.PHONY: create-cluster


kubeconfig: _select_engine
	@cd "$(MAKEFILE_DIR)" ; \
	set -euo pipefail ; source .cluster_type ; \
	if [[ "$$CLUSTER_TYPE" == "podman" ]] ; then \
	  export KIND_EXPERIMENTAL_PROVIDER=podman ; \
	fi ; \
	kind get kubeconfig --name $(KIND_CLUSTER_NAME)
.PHONY: kubeconfig


prepare-helm:
	helm repo add     apache-superset   https://apache.github.io/superset
	helm repo add     authelia          https://charts.authelia.com
	helm repo add     authentik         https://charts.goauthentik.io
	helm repo add     cert-manager      https://charts.jetstack.io
	helm repo add     dex               https://charts.dexidp.io
	helm repo add     emberstack        https://emberstack.github.io/helm-charts
	helm repo add     external-secrets  https://charts.external-secrets.io
	helm repo add     oauth2-proxy      https://oauth2-proxy.github.io/manifests/
	helm repo add     traefik           https://traefik.github.io/charts
	helm repo add     zitadel           https://charts.zitadel.com
	helm repo update
.PHONY: prepare-helm


prepare-users: $(AUTHELIA_USERS_HASHES_YAML)
.PHONY: prepare-users


prepare: create-cluster prepare-users prepare-helm
.PHONY: prepare


deploy-namespaces:
	@$(SCRIPT_START) ; \
	for ns in $(CLUSTER_CREATE_NAMESPACES) ; do \
	  if ! $(KCMD) get ns "$$ns" > /dev/null 2>&1 ; then \
	    $(KCMD) create ns "$$ns" ; \
	  fi ; \
	done
.PHONY: deploy-namespaces


DEPLOY_SLEEP ?= 15
DEPLOY_TRIES ?= 3

deploy: deploy-namespaces
	@cd "$(MAKEFILE_DIR)" ; \
	for i in {1..$(DEPLOY_TRIES)} ; do \
	  find . -iname ".deploy_error" -delete ; \
	  make -s deploy-helm ; \
	  [[ ! -f .deploy_error ]] && break ; \
	  if (( REPEAT < $(DEPLOY_TRIES) )) ; then \
	    echo -e "\n\nDeployment run $$i (of max $(DEPLOY_TRIES)) completed with errors, trying again in $(DEPLOY_SLEEP) seconds ..." ; \
	    sleep $(DEPLOY_SLEEP) ; \
	    echo -e "\nRetry.\n" ; \
	  else \
	    echo -e "\nMax retries reached, aborting. Deployment has errors.\n" ; \
	  fi ; \
	done ;
deploy: $(AUTHELIA_USERS_K8S_SECRET)
.PHONY: deploy


reset: delete-cluster prepare deploy
.PHONY: reset


redeploy: clean deploy
.PHONY: redeploy
