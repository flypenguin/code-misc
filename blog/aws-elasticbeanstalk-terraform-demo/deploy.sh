#!/usr/bin/env bash

if [ "$3" == "" ] ; then
  cat <<EOF

USAGE: $(basename $0) <app-name> <version> <env-name>

Deploys version with name <version> for application <app-name> into application
environment with the name <env-name>.

All of those must already exist.

EOF
  exit -1
fi

aws elasticbeanstalk update-environment \
  --application-name $1 \
  --version-label $2 \
  --environment-name $3

echo "Done."
