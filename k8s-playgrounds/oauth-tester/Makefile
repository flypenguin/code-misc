SHELL = bash

THIS_MAKEFILE := $(lastword $(MAKEFILE_LIST))
MAKEFILE_DIR := $(dir $(THIS_MAKEFILE))

KIND_CLUSTER_NAME := test-oauth
KCMD = kubectl --context kind-$(KIND_CLUSTER_NAME)
HCMD = helm --kube-context kind-$(KIND_CLUSTER_NAME)

USERS_FILE = authelia-users-to-create.csv
USERS_FILE_TMPL = $(USERS_FILE).template
USERS_SECRET_YAML = k8s-objects/authelia-users-database.yaml

SCRIPT_START = cd $(MAKEFILE_DIR) ; set -eup pipefail


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
	helm repo update
.PHONY: prepare-helm


prepare-users:
	@$(SCRIPT_START) ; \
	if [[ ! -f "$(USERS_FILE)" ]]; then \
	  cat "$(USERS_FILE_TMPL)" >> "$(USERS_FILE)" ; \
	fi ; \
	echo "# this file is re-generated using 'make prepare-users'. do not edit." \
	  > $(USERS_SECRET_YAML) ; \
	./create-users.py "$(USERS_FILE)" >> "$(USERS_SECRET_YAML)"
.PHONY: prepare-users


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


deploy-authelia-users:
	@$(SCRIPT_START) ; \
	$(KCMD) create secret \
	  generic \
	  -n authelia \
	  authelia-users-database \
	  --from-file=users_database.yml=$(USERS_SECRET_YAML) \
	  --dry-run=client \
	  -o yaml \
	| kubectl apply -f -
.PHONY: deploy-authelia-users


deploy-authelia:
	@$(SCRIPT_START) ; \
	cd helm-values-files ; \
	$(HCMD) upgrade -i \
	  -n authelia \
	  -f values-authelia.yaml \
	  authelia \
	  authelia/authelia \
	  --debug
.PHONY: deploy-authelia


deploy: deploy-namespaces
deploy: deploy-authelia-users
deploy: deploy-authelia
.PHONY: deploy
