# README

## TL;DR

```shell
# prepare "everything"
make prepare

# deploy the authentication test apps
make deploy
```

## Testing authentication

DEPLOYMENT CURRENTLY BROKEN.

```text
$ make deploy
secret/authelia-users-database configured
history.go:56: 2025-09-01 19:05:35.413819 +0200 CEST m=+0.093587084 [debug] getting history for release authelia
Release "authelia" does not exist. Installing it now.
install.go:225: 2025-09-01 19:05:35.417927 +0200 CEST m=+0.097695043 [debug] Original chart version: ""
install.go:242: 2025-09-01 19:05:35.726455 +0200 CEST m=+0.406220418 [debug] CHART PATH: /Users/tm/.cache/helm/repository/authelia-0.10.42.tgz

Error: values don't meet the specifications of the schema(s) in the following chart(s):
authelia:
anchor in "https://charts.authelia.com/definitions.json#definitions/io.k8s.apimachinery.pkg.apis.meta.v1.LabelSelector" not found in schema "https://charts.authelia.com/definitions.json"
helm.go:92: 2025-09-01 19:05:35.920308 +0200 CEST m=+0.600072584 [debug] values don't meet the specifications of the schema(s) in the following chart(s):
authelia:
anchor in "https://charts.authelia.com/definitions.json#definitions/io.k8s.apimachinery.pkg.apis.meta.v1.LabelSelector" not found in schema "https://charts.authelia.com/definitions.json"
make: *** [Makefile:72: deploy-authelia] Error 1
```
