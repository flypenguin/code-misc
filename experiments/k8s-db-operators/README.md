# README

## Init (TL;DR)

```bash
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

## CNPG

* You cannot configure multiple databases on a cluster declaratively

## CrunchyData

* You _must_ configure backups. This is kinda nice :)

## Links

* [CloudNativePG](https://cloudnative-pg.io/)
    * [Documentation](https://cloudnative-pg.io/docs/)
    * [CloudNativePG v1.22 API reference v1.22 (CRDs)](https://cloudnative-pg.io/documentation/1.22/cloudnative-pg.v1/)
* [Crunchy data](https://www.crunchydata.com/)
    * [Documentation](https://access.crunchydata.com/documentation/postgres-operator/latest)
    * [PostgresCluster v5.5 API reference (CRDs)](https://access.crunchydata.com/documentation/postgres-operator/latest/references/crd/5.5.x/postgrescluster)
* PG other
    * [PGBarman](https://pgbarman.org/)
