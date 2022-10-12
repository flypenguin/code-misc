# Terraform prerequisites

- set `project_prefix` in variables.tf
- check into git
- `make init`, `make plan`, `make do`
  - (or `terraform init`, `terraform plan -out tf.plan`, `terraform apply tf.plan`)
- if everything went well, `backend.tf` is now changed
- re-run `terraform init` add everything to git, commit, you're done.
