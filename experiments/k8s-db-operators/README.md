# README

## Init (TL;DR)

```bash
# creates namespace & debug pod with cluster admin permissions
make itfr

# must be first, installs the operators
make helmsman

# must be second, installs the clusters using kubectl
make kube
```

Then:
    * deploy a shell pod on the cluster
        * `kubectl apply -f manual_debug_pod.yaml`
        * shell into it, and do `apt-get update && apt-get install postgresql-client dnsutils`
        * (one time actions)
    * connect to the databases from the shell
        * cnpg
            * read the database password from the secret `cnpg0-app`, field `password`
            * connect usinng: `psql -h cnpg0-rw -U cnpg-user cnpg`
        * crunchy
            * TBD


## Notes

## Prepare debug pod

... to install `kubectl` and `postgresql-client` (among other required things):

```bash
apt-get update && apt-get install -y dnsutils postgresql-client apt-transport-https ca-certificates curl gpg vim jq wget
wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq && chmod +x /usr/bin/yq
mkdir /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /' > /etc/apt/sources.list.d/kubernetes.list
apt-get update
apt-get install -y kubectl
```

## CNPG

* You cannot configure multiple databases on a cluster declaratively

```bash
# connect to database, user defined in manifest
CNPG0_APP_SECRET="cnpg0-app"
export PGPASSWORD=$(kubectl get secret -o json $CNPG0_APP_SECRET | jq -r ".data.password" | base64 -d)
psql -h cnpg0-rw   -U cnpg-user   cnpg
```

## CrunchyData

* You _must_ configure backups. This is kinda nice :)

```bash
# connect to database, cluster name = user name
CRUNCHY_SECRET="crunchy0-pguser-crunchy0"
export PGPASSWORD=$(kubectl get secret -o json $CRUNCHY_SECRET | jq -r ".data.password" | base64 -d)
psql -h crunchy0-ha   -U crunchy0   crunchy0
```

## Links

* [CloudNativePG](https://cloudnative-pg.io/)
    * [Documentation](https://cloudnative-pg.io/docs/)
    * [CloudNativePG v1.22 API reference v1.22 (CRDs)](https://cloudnative-pg.io/documentation/1.22/cloudnative-pg.v1/)
* [Crunchy data](https://www.crunchydata.com/)
    * [Documentation](https://access.crunchydata.com/documentation/postgres-operator/latest)
    * [PostgresCluster v5.5 API reference (CRDs)](https://access.crunchydata.com/documentation/postgres-operator/latest/references/crd/5.5.x/postgrescluster)
* [Percona K8S operators](https://www.percona.com/software/percona-kubernetes-operators)
    * [v2.0 Documentation](https://docs.percona.com/percona-operator-for-postgresql/2.0/index.html)
    * [PerconaPGCluster v2.0 API reference (CRDs)](https://docs.percona.com/percona-operator-for-postgresql/2.0/operator.html)
* [Zalando Postgres operator](https://github.com/zalando/postgres-operator)
    * [Documentation](https://postgres-operator.readthedocs.io/en/latest/)
    * [Cluster Manifest API reference (CRDs - _maybe_)](https://postgres-operator.readthedocs.io/en/latest/reference/cluster_manifest/) (yes, this is shit)
* PG other
    * [PGBarman](https://pgbarman.org/)
