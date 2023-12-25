DEBUG := 0
SHELL := /bin/bash

helmsman_params := ""

secret_src_files := $(wildcard secret__*.yaml)
secret_deploy_files := $(patsubst %.yaml,%.secret_deploy,$(secret_src_files))
secret_uninstall_files := $(patsubst %.yaml,%.secret_uninstall,$(secret_src_files))

# wildcard results are sorted! (https://is.gd/sufwSy)
# ITFR = "i take full responsibility"
itfr_src_files := $(wildcard itfr__*.yaml)
itfr_deploy_files := $(patsubst %.yaml,%.itfr_deploy,$(itfr_src_files))
itfr_diff_files := $(patsubst %.yaml,%.itfr_diff,$(itfr_src_files))

# wildcard results are sorted! (https://is.gd/sufwSy)
kube_src_files := $(wildcard kube__*.yaml)
kube_deploy_files := $(patsubst %.yaml,%.kube_deploy,$(kube_src_files))
kube_diff_files := $(patsubst %.yaml,%.kube_diff,$(kube_src_files))

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
	@yq > /dev/null 2>&1 || (echo "Command 'yq' missing, please install" ; false)
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
		| yq -M ".metadata.name = \"$$k8s_sa_name\" | .metadata.namespace = \"$$k8s_ns\"" \
		| $$tee_cmd \
		| kubectl apply \
			--namespace $$k8s_ns \
			-f - \
			2>&1 \
		| tee $$log_file


# this will BREAK BADLY as soon as any yaml file has a space in its name ...
# just to be sure you know / remember.
# MAKEFILE VARIABLES: src_file (*.yaml)   => "$<"
# MAKEFILE VARIABLES: target_file (*.log) => "$@"
%.kube_diff: %.yaml
	@yq > /dev/null 2>&1 || (echo "Command 'yq' missing, please install" ; false)
	@src_file="$<" ; \
	tmp=$${src_file#*__} ; \
	k8s_ns=$${tmp%%__*} ; \
	k8s_sa_name=$${tmp#*__} ; \
	k8s_sa_name=$${k8s_sa_name%.yaml} ; \
	k8s_sa_name=$${k8s_sa_name%.*} ; \
	DIFF=$$( \
		cat "$$src_file" \
		| yq -M ".metadata.name = \"$$k8s_sa_name\" | .metadata.namespace = \"$$k8s_ns\"" \
		| kubectl diff -f - \
	) ; \
	if [ "$$?" = "0" ]; then \
		echo "# Up to date: '$$src_file'" ; \
	else \
		echo -e "# CHANGED: '$$src_file'" ; \
		echo "$$DIFF" ; \
	fi

# ITFR = "I take full responsibility" ...
%.itfr_deploy: %.yaml
	src_file="$<" ; \
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
	echo "Deploying: $$src_file ..." ; \
	cat $$src_file \
		| $$tee_cmd \
		| kubectl apply -f -  2>&1 \
		| tee $$log_file


# ITFR = "I take full responsibility" ...
%.itfr_diff: %.yaml
	@src_file="$<" ; \
	DIFF=$$(kubectl diff -f "$$src_file" 2>&1) ; \
	if [ "$$?" = "0" ]; then \
		echo "# Up to date: '$$src_file'" ; \
	else \
		echo -e "# CHANGED: '$$src_file'" ; \
		echo "$$DIFF" ; \
	fi



default:
	echo "helmsman targets:     make  plan|diff|helmsman|helmsman-migrate|plan-migrate|debug"
	echo "kubectl targets:      make  kube"
	echo "secrets targets:      make  secrets|secrets-uninstall"
.PHONY: default
.SILENT: default

clean:
	rm -f *.log *.result
.PHONY: clean


helmsman-deploy:
	@[ -f helmsman.yaml ] \
	&& helmsman   -apply -subst-ssm-values -f helmsman.yaml $(helmsman_params) \
	|| echo "No helmsman.yaml found, skipping helmsman deployment"
.PHONY: helmsman-deploy


helmsman-debug:
	helmsman -dry-run -subst-ssm-values -f helmsman.yaml -show-diff -debug $(helmsman_params)
.PHONY: helmsman-debug


helmsman-diff:
	helmsman          -subst-ssm-values -f helmsman.yaml -show-diff $(helmsman_params)
.PHONY: helmsman-diff


helmsman-plan:
	helmsman          -subst-ssm-values -f helmsman.yaml $(helmsman_params)
.PHONY: helmsman-plan


helmsman-deploy-migrate: helmsman_params := --migrate-context
helmsman-deploy-migrate: helmsman-deploy
.PHONY: helmsman-deploy-migrate


helmsman-plan-migrate: helmsman_params := --migrate-context
helmsman-plan-migrate: plan
.PHONY: helmsman-plan-migrate


secrets-deploy: $(secret_deploy_files)
.PHONY: secrets-deploy


secrets-uninstall: $(secret_uninstall_files)
.PHONY: secrets-uninstall


kube-deploy: clean
kube-deploy: $(kube_deploy_files)
.PHONY: kube-deploy


kube-diff: $(kube_diff_files)
.PHONY: kube-diff


kube-debug: DEBUG=1
kube-debug: kube-deploy
.PHONY: kube-debug


itfr-deploy: clean
itfr-deploy: $(itfr_deploy_files)
.PHONY: itfr-deploy


itfr-diff: $(itfr_diff_files)
.PHONY: itfr-diff


itfr-debug: DEBUG=1
itfr-debug: itfr-deploy
.PHONY: itfr-debug


# aliases


kdeploy: kube-deploy
.PHONY: kdeploy

itfr: itfr-deploy
.PHONY: itfr

kdebug: DEBUG=1
kdebug: kube-deploy
.PHONY: kdebug

kdiff: kube-diff
.PHONY: kdiff

secrets: secrets-deploy
.PHONY: secrets

helmsman: helmsman-plan
.PHONY: helmsman

hdeploy: helmsman-deploy
.PHONY: hdeploy

hdebug: helmsman-debug
.PHONY: hdebug

hdiff: helmsman-diff
.PHONY: hdiff

hmig: helmsman-deploy-migrate
.PHONY: hmig

pmig: helmsman-plan-migrate
.PHONY: plan-migrate
