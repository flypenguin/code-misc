#!/bin/bash

# DESCRIPTION

# the OUTPUT of this script is intended to be redirected (> ...) into the
# "authorized_iam_keys" file of ec2-user.
# this is being done in root's crontab.
# the .ssh/autorized_iam_keys file is configured in /etc/ssh/sshd_config.


# "SETTINGS"

# In order to change the authorized group modify this parameter
AUTHORIZED_GROUP_NAME='bastionAccess'


# INTERNAL PARAMETERS

AUTHORIZED_KEYS_FILE='/home/ec2-user/.ssh/authorized_keys'


# START

cat "$AUTHORIZED_KEYS_FILE"

aws iam list-users --query 'Users[].[UserName]' --output text | while read User; do
  BASTION_ACCESS_GROUP="$(aws iam list-groups-for-user --user-name "$User" --query 'Groups[?GroupName == `'$AUTHORIZED_GROUP_NAME'`]')"
  [[ "$BASTION_ACCESS_GROUP" == "[]" ]] && continue
  aws iam list-ssh-public-keys \
          --user-name "$User" \
          --query "SSHPublicKeys[?Status == 'Active'].[SSHPublicKeyId]" \
          --output text \
          | while read KeyId; do
      aws iam get-ssh-public-key \
              --user-name "$User" \
              --ssh-public-key-id "$KeyId" \
              --encoding SSH \
              --query "[SSHPublicKey.SSHPublicKeyBody, SSHPublicKey.UserName]" \
              --output text \
              | sed -s 's/\t/ /g'
  done
done
