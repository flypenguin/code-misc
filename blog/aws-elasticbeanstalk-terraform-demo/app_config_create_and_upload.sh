#!/usr/bin/env bash

#
# Creates a ZIP file with the following content:
#
#    vX.zip -> -|
#               |-Dockerrun.aws.json
#               |-.ebextensions       (optional)
#                  |- ...
#


if [ "$2" == "" ]; then
  cat <<EOF

USAGE:    $(basename $0) <version-name> <docker-image>
EXAMPLE:  $(basename $0) v6 jenkins
          $(basename $0) 1.2.3 my.host.com:5000/myrepo/mycontainer:v1.2.3

Will create the Dockerrun.aws.json file from the file dockerrun.json.template,
replace %%IMAGE%% in that file with the image given, upload it to the S3
bucket given in the variable \$EBS_BUCKET (if not set it will ask you to enter
it), and create a terraform file which creates the app version under the name
you have specified.

If present, a "ebextensions" directory is copied to .ebextensions and also
packaged into the ZIP file for environment configuration.

If you don't have a test image, you can use 'flypenguin/test:latest'. It only
has one tag ('latest') though.

EOF
  exit -1
fi

if [ "$EBS_BUCKET" == "" ] ; then
  echo ""
  echo "Enter S3 bucket to store config in. You can also set the EBS_BUCKET "
  echo "env variable to skip this question."
  echo "DO NOT USE THE 's3://' PREFIX, just the raw bucket name!"
  echo -n "S3 bucket: "
  read EBS_BUCKET
  echo ""
fi


#set -x

VERSION=$(basename $1)
VERSION_CLEAN=$(echo $VERSION | sed 's/[^a-zA-Z0-9_-]/_/g')


cat app_config_json.template \
  | sed -r -e "s&%%IMAGE%%&$2&g" \
  > Dockerrun.aws.json
zip $VERSION_CLEAN Dockerrun.aws.json


# take care of .ebextensions
if [[ -d "ebextensions" ]] ; then
  echo "Found ebextensions/. Adding to ZIP as .ebextensions ..."
  cp -r ebextensions .ebextensions
  zip -r $VERSION_CLEAN .ebextensions
  rm -rf .ebextensions
fi


# upload the shit
aws s3 cp "${VERSION_CLEAN}.zip" "s3://$EBS_BUCKET/${VERSION_CLEAN}.zip"
rm -f "${VERSION_CLEAN}.zip"
rm -f Dockerrun.aws.json


# create the terraform config
cat app_config_terraform.template \
  | sed -r -e "s/%%VERSION%%/$VERSION/g" \
           -e "s/%%VERSION_CLEAN%%/$VERSION_CLEAN/g" \
           -e "s/%%EBS_BUCKET%%/$EBS_BUCKET/g" \
           -e "s&%%IMAGE%%&$2&g" \
           -e "s!%%KEY%%!${VERSION_CLEAN}.zip!g" \
  > app_version_${VERSION}.tf

# done.
