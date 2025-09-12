SHELL = bash

THIS_MAKEFILE := $(lastword $(MAKEFILE_LIST))
MAKEFILE_DIR := $(dir $(THIS_MAKEFILE))

KIND_CLUSTER_NAME := test-oauth
KCMD = kubectl --context kind-$(KIND_CLUSTER_NAME)
HCMD = helm --kube-context kind-$(KIND_CLUSTER_NAME)

AUTHELIA_USERS_CSV = config-files/authelia-users.csv
AUTHELIA_USERS_CSV_TMPL = templates/authelia-users.csv.template
AUTHELIA_USERS_HASHES_YAML = config-files/authelia-password-hashes.yaml
AUTHELIA_USERS_K8S_SECRET = k8s-objects/k8s-authelia-users-secret.yaml

HELM_VALUES := $(wildcard helm-values-files/values-*.yaml)
KYML_VALUES := $(wildcard k8s-objects/k8s-*.yaml)
HELM_DEPLOY := $(HELM_VALUES:helm-values-files/values-%.yaml=helm-values-files/deploy-%.txt)
KYML_DEPLOY := $(KYML_VALUES:k8s-objects/k8s-%.yaml=k8s-objects/apply-%.txt)

SCRIPT_START = cd $(MAKEFILE_DIR) ; set -euo pipefail

CLUSTER_HIGH_PORT_HTTPS = 8443
CLUSTER_HIGH_PORT_HTTP = 8080
CLUSTER_URL = localhost.traefik.me


helm-values-files/deploy-%.txt: helm-values-files/values-%.yaml
	@$(SCRIPT_START) ; \
	rm -f "$@" "$@.tmp"; \
	name=$*; \
	chart="$$(\
	  cat helm-values-files/_deployment-infos.txt \
	  | grep -E '^CHART $*' \
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
	) && mv $@.tmp $@ || cat $@.tmp

k8s-objects/apply-%.txt: k8s-objects/k8s-%.yaml
	@$(SCRIPT_START) ; \
	rm -f "$@" "$@.tmp"; \
	name=$*; \
	(\
	  set -x ; \
	  kubectl apply -f $< > $@.tmp 2>&1 \
	) && mv $@.tmp $@ || (cat $@.tmp && rm $@.tmp)


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
	  -n authelia \
	  authelia-users-database \
	  --from-file=users_database.yml=$(AUTHELIA_USERS_HASHES_YAML) \
	  --dry-run=client \
	  -o yaml \
	> $@ \
	&& echo "Created file: $@" \
	|| rm -f $@


clean:
	@rm -fv helm-values-files/deploy-*.txt
	@rm -fv k8s-objects/apply-*.txt
	@rm -fv $(AUTHELIA_USERS_K8S_SECRET)
	@rm -fv $(AUTHELIA_USERS_HASHES_YAML)
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


prepare-cluster:
	@if ! kind get clusters | grep -q $(KIND_CLUSTER_NAME) ; then \
	  echo " * Creating cluster '$(KIND_CLUSTER_NAME)' using 'kind' ..." ; \
	  set -x ; \
	  kind create cluster -n test-oauth ; \
	fi
.PHONY: prepare-cluster


prepare-helm:
	helm repo add     oauth2-proxy      https://oauth2-proxy.github.io/manifests/
	helm repo add     dex               https://charts.dexidp.io
	helm repo add     authelia          https://charts.authelia.com
	helm repo add     cert-manager      https://charts.jetstack.io
	helm repo add     traefik           https://traefik.github.io/charts
	helm repo update
.PHONY: prepare-helm


prepare: prepare-cluster prepare-users prepare-helm
.PHONY: prepare


deploy-namespaces:
	@$(SCRIPT_START) ; \
	for ns in authelia ; do \
	  if ! $(KCMD) get ns "$$ns" > /dev/null 2>&1 ; then \
	    $(KCMD) create ns "$$ns" ; \
	  fi ; \
	done
.PHONY: deploy-namespaces


deploy: deploy-namespaces
deploy: $(AUTHELIA_USERS_K8S_SECRET)
deploy: deploy-helm
deploy: deploy-k8s
.PHONY: deploy
