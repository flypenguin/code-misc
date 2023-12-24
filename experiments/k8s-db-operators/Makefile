DEBUG := 0
SHELL := /bin/bash

helmsman_params := ""

secret_src_files := $(wildcard secret__*.yaml)
secret_deploy_files := $(patsubst %.yaml,%.secret_deploy,$(secret_src_files))
secret_uninstall_files := $(patsubst %.yaml,%.secret_uninstall,$(secret_src_files))

kube_src_files := $(wildcard kube__*.yaml)
kube_deploy_files := $(patsubst %.yaml,%.kube_deploy,$(kube_src_files))

# this will BREAK BADLY as soon as any yaml file has a space in its name ...
# just to be sure you know / remember.
%.secret_deploy: %.yaml
	@src_file="$<" ; \
	tmp=$${src_file#*__} ; \
	k8s_ns=$${tmp%%__*} ; \
	k8s_secret_name=$${tmp#*__} ; \
	k8s_secret_name=$${k8s_secret_name%.yaml} ; \
	helm_name="$${k8s_secret_name}-secret" ; \
	helm_name="$${helm_name/-secret-secret/-secret}" ; \
	helm_name="$${helm_name/-secrets-secret/-secrets}" ; \
	set -x ; \
	helm ssm upgrade -i \
			-f $$src_file \
			--set name=$$k8s_secret_name \
			--set namespace=$$k8s_ns \
			--namespace $$k8s_ns \
			"$${helm_name}" \
			dahelmcharts/secret


# this will BREAK BADLY as soon as any yaml file has a space in its name ...
# just to be sure you know / remember.
%.secret_uninstall: %.yaml
	@src_file="$<" ; \
	tmp=$${src_file#*__} ; \
	k8s_ns=$${tmp%%__*} ; \
	k8s_secret_name=$${tmp#*__} ; \
	k8s_secret_name=$${k8s_secret_name%.yaml} ; \
	helm_name="$${k8s_secret_name}-secret" ; \
	helm_name="$${helm_name/-secret-secret/-secret}" ; \
	helm_name="$${helm_name/-secrets-secret/-secrets}" ; \
	set -x ; \
	helm uninstall -n $$k8s_ns "$${helm_name}"


# this will BREAK BADLY as soon as any yaml file has a space in its name ...
# just to be sure you know / remember.
# MAKEFILE VARIABLES: src_file (*.yaml)   => "$<"
# MAKEFILE VARIABLES: target_file (*.log) => "$@"
%.kube_deploy: %.yaml
	@src_file="$<" ; \
	if [ "$(DEBUG)" = "1" ] ; then \
		log_file="$@.log" ; \
		result_file="$$src_file.result" ; \
		tee_cmd="tee $$result_file" ; \
		rm -f "$$log_file" "$$result_file"; \
		echo "$$src_file -> $$log_file/.yaml" ; \
	else \
		log_file=/dev/null ; \
		tee_cmd=cat ; \
	fi ; \
	tmp=$${src_file#*__} ; \
	k8s_ns=$${tmp%%__*} ; \
	k8s_sa_name=$${tmp#*__} ; \
	k8s_sa_name=$${k8s_sa_name%.yaml} ; \
	k8s_sa_name=$${k8s_sa_name%.*} ; \
	echo "Deploying: $$src_file ..." ; \
	cat $$src_file \
		| sed \
			-e "s/%%NAME%%/$$k8s_sa_name/g" \
			-e "s/%%NAMESPACE%%/$$k8s_ns/g" \
		| $$tee_cmd \
		| kubectl apply \
			--namespace $$k8s_ns \
			-f - \
			2>&1 \
		| tee $$log_file


default:
	echo "helmsman targets:     make  plan|diff|helmsman|helmsman-migrate|plan-migrate|debug"
	echo "kubectl targets:      make  kube"
	echo "secrets targets:      make  secrets|uninstall-secrets"
.PHONY: default
.SILENT: default

clean:
	rm -f *.log *.result
.PHONY: clean


debug:
	helmsman -dry-run -subst-ssm-values -f helmsman.yaml -show-diff -debug $(helmsman_params)
.PHONY: debug


diff:
	helmsman          -subst-ssm-values -f helmsman.yaml -show-diff $(helmsman_params)
.PHONY: diff


plan:
	helmsman          -subst-ssm-values -f helmsman.yaml $(helmsman_params)
.PHONY: plan


deploy-secrets: $(secret_deploy_files)
.PHONY: deploy-secrets


deploy-kube: clean
deploy-kube: $(kube_deploy_files)
.PHONY: deploy-kube


deploy-helmsman:
	@[ -f helmsman.yaml ] \
	&& helmsman   -apply -subst-ssm-values -f helmsman.yaml $(helmsman_params) \
	|| echo "No helmsman.yaml found, skipping helmsman deployment"
.PHONY: deploy-helmsman


uninstall-secrets: $(secret_uninstall_files)
.PHONY: uninstall-secrets


debug: DEBUG=1
debug: do


# aliases


secrets: deploy-secrets
.PHONY: secrets


kube: deploy-kube
.PHONY: kube


helmsman: deploy-helmsman
.PHONY: helmsman


install: all
.PHONY: all


helmsman-migrate: helmsman_params := --migrate-context
helmsman-migrate: helmsman
.PHONY: helmsman-migrate


plan-migrate: helmsman_params := --migrate-context
plan-migrate: plan
.PHONY: plan-migrate
