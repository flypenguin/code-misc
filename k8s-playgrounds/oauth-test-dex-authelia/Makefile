SHELL = bash

THIS_MAKEFILE := $(lastword $(MAKEFILE_LIST))
MAKEFILE_DIR := $(dir $(THIS_MAKEFILE))

KIND_CLUSTER_NAME := test-dex-authelia

KCMD = kubectl --context kind-$(KIND_CLUSTER_NAME)
HCMD = helm --kube-context kind-$(KIND_CLUSTER_NAME)

AUTHELIA_USERS_CSV = config-files/authelia-users.csv
AUTHELIA_USERS_CSV_TMPL = templates/authelia-users.csv.template
AUTHELIA_USERS_HASHES_YAML = config-files/authelia-password-hashes.yaml
AUTHELIA_USERS_K8S_SECRET = k8s-objects/k8s-authelia-users-secret.yaml

HELM_VALUES := $(wildcard helm-values-files/values-*.yaml)
KYML_VALUES := $(wildcard k8s-objects/k8s-*.yaml)
HELM_DEPLOY := $(HELM_VALUES:helm-values-files/values-%.yaml=helm-values-files/.deploy/%.txt)
KYML_DEPLOY := $(KYML_VALUES:k8s-objects/k8s-%.yaml=k8s-objects/.apply/%.txt)

SCRIPT_START = cd $(MAKEFILE_DIR) ; set -euo pipefail

CLUSTER_HIGH_PORT_HTTPS = 8443
CLUSTER_HIGH_PORT_HTTP = 8080
CLUSTER_URL = localhost.traefik.me
CLUSTER_CREATE_NAMESPACES = authelia-local authelia-ldap


helm-values-files/.deploy/%.txt: helm-values-files/values-%.yaml
	@$(SCRIPT_START) ; \
	mkdir -p helm-values-files/.deploy ; \
	rm -f "$@" "$@.tmp"; \
	name=$*; \
	chart="$$(\
	  cat helm-values-files/_deployment-infos.txt \
	  | grep -E '^CHART $* ' \
	  | cut -d " " -f 3 \
	  || true \
	)" ; \
	ns="$$(\
	  cat helm-values-files/_deployment-infos.txt \
	  | grep -E '^NS $*' \
	  | cut -d " " -f 3 \
	  || true \
	)" ; \
	[[ -z "$$chart" ]] && chart="$*" ; \
	[[ -z "$$ns" ]] && ns="$*" ; \
	(\
	  set -x ; \
	  helm upgrade -i --create-namespace -n $$ns -f $< $* $$chart > $@.tmp 2>&1 \
	) && mv $@.tmp $@ || (cat $@.tmp && false)


k8s-objects/.apply/%.txt: k8s-objects/k8s-%.yaml
	@$(SCRIPT_START) ; \
	mkdir -p k8s-objects/.apply ; \
	rm -f "$@" "$@.tmp"; \
	name=$*; \
	(\
	  set -x ; \
	  kubectl apply -f $< > $@.tmp 2>&1 \
	) && mv $@.tmp $@ || (cat $@.tmp && rm $@.tmp && false)


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
	$(KCMD) create secret \
	  generic \
	  -n authelia-local \
	  authelia-local-users-database \
	  --from-file=users_database.yml=$(AUTHELIA_USERS_HASHES_YAML) \
	  --dry-run=client \
	  -o yaml \
	> $@ \
	&& echo "Created file: $@" \
	|| (rm -f $@ ; false)


clean-users:
	@rm -fv $(AUTHELIA_USERS_K8S_SECRET)
	@rm -fv $(AUTHELIA_USERS_HASHES_YAML)
.PHONY: clean-users


clean:
	@rm -rfv helm-values-files/.deploy
	@rm -rfv k8s-objects/.apply
.PHONY: clean


deploy-helm: $(HELM_DEPLOY)
.PHONY: deploy-helm


deploy-k8s: $(KYML_DEPLOY)
.PHONY: deploy-k8s


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
	helm repo add     authelia          https://charts.authelia.com
	helm repo add     authentik         https://charts.goauthentik.io
	helm repo add     cert-manager      https://charts.jetstack.io
	helm repo add     dex               https://charts.dexidp.io
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
	  REPEAT=0 ; \
	  make -s deploy-helm || REPEAT=1 ; \
	  make -s deploy-k8s  || REPEAT=1 ; \
	  if (( REPEAT == 0 )) ; then \
	    break ; \
	  elif (( REPEAT < $(DEPLOY_TRIES) )) ; then \
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
