# ###########################################################################
#
# AWS
#


C_BOLD="\e[1m"
C_BRED="\e[91m"
C_BGRE="\e[92m"
C_BYEL="\e[93m"
C_BWHI="\e[97m"
C_REST="\e[0m"
H_GREN="${C_BGRE}${C_BOLD}"
H_YELO="${C_BYEL}${C_BOLD}"
H_REDD="${C_BRED}${C_BOLD}"
DINFO="${C_BWHI}${C_BOLD}INFO:${C_REST}"
DERRR="${C_BRED}${C_BOLD}ERROR:${C_REST}"
DWARN="${C_BYEL}${C_BOLD}WARNING:${C_REST}"


# this function assumes the following env variables are present:
#   - AWS_TOKEN_VALIDITY
# parameters
#   $1 - the AWS profile for which to check
# it returns:
#   0 - still valid (loaded _OR_ active tokens)
#   1 - token almost expired
#   2 - token expired
#   3 - no token found
_aws_load_token() {
  local TOKEN_FILE="$HOME/.aws/token.$1.sh"

  if [ "$AWS_MFA_BASE" != "$1" ] ; then
    if [ ! -f "$TOKEN_FILE" ] ; then
      # "no existing token found"
      echo "$DINFO ${H_YELO}No existing token${C_REST} found."
      return 3
    else
      . "$TOKEN_FILE"
    fi
  fi
  # now we are set and can verify the token lifetime
  local TIME_NOW=$(date  +%s)
  local TIME_REMAINING=$((AWS_TOKEN_VALIDITY - TIME_NOW))
  if (( TIME_REMAINING > 3600 )) ; then
    echo "$DINFO existing ${H_GREN}token still valid${C_REST} (and loaded)"
    return 0
  elif (( TIME_REMAINING > 0 )) ; then
    # "token almost expired"
    echo "$DINFO existing ${H_YELO}token almost expired${C_REST}, creating new one"
    return 2
  else
    echo "$DINFO existing ${H_YELO}token expired${C_REST}, creating new one"
    # "token expired"
    return 1
  fi
}


# parameters:
#   $1 - the profile to get a token for
_aws_get_new_token() {
  local TOKEN_FILE="$HOME/.aws/token.$1.sh"
  local SED_MARKER
  local TMP

  echo -n ">> Enter MFA token value (ENTER to abort): "
  read MFA_TOKEN
  if [ -z "$MFA_TOKEN" ] ; then
    echo "Abort."
    return 1
  fi

  # clean env variables, but only if a session token is active
  if [ -n "$AWS_MFA_BASE" ] ; then
    echo "* Cleaning existing ENV vars (already have a session token)"
    unset AWS_SESSION_TOKEN
    unset AWS_ACCESS_KEY_ID
    unset AWS_SECRET_ACCESS_KEY
  fi

  export AWS_PROFILE="$1"

  echo -n "* Getting MFA ARN ... "
  MFA_ARN=$(aws --profile $AWS_PROFILE iam list-mfa-devices | jq -r '.MFADevices[0].SerialNumber')
  if [ "$?" != "0" ] ; then
    echo "$DERRR something failed getting the session token. You should close this shell."
    return 2
  fi
  echo $MFA_ARN

  echo -n "* Getting session token ... "
  SESSION_TOKEN_JSON=$(aws --profile $AWS_PROFILE sts get-session-token --serial-number $MFA_ARN --token-code $MFA_TOKEN --duration-seconds $TOKEN_DURATION)
  if [ "$?" != "0" ] ; then
    echo "$DERRR something failed getting the session token. You should close this shell."
    return 3
  else
    export AWS_TOKEN_VALIDITY=$(( $(date +%s) + TOKEN_DURATION ))
    export AWS_MFA_BASE=$AWS_PROFILE
    echo "${C_BGRE}${C_BOLD}done${C_REST}."
  fi

  echo -n "* Setting env variables ... "
  export AWS_ACCESS_KEY_ID=$(echo $SESSION_TOKEN_JSON | jq -r '.Credentials.AccessKeyId')
  export AWS_SECRET_ACCESS_KEY=$(echo $SESSION_TOKEN_JSON | jq -r '.Credentials.SecretAccessKey')
  export AWS_SESSION_TOKEN=$(echo $SESSION_TOKEN_JSON | jq -r '.Credentials.SessionToken')
  echo "done."

  echo -n "* Writing ${C_BWHI}${C_BOLD}$TOKEN_FILE${C_REST} ... "
  cat > "$TOKEN_FILE" <<EOF
# SOURCE this file, do not execute it.
export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
export AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN
# helper variables
export AWS_TOKEN_VALIDITY=$AWS_TOKEN_VALIDITY
export AWS_MFA_BASE=$AWS_PROFILE
EOF
  chmod 600 "$TOKEN_FILE"
  echo "done."

  export AWS_PROFILE="$1_mfasession"
  echo -n "* Creating AWS MFA ${C_BWHI}${C_BOLD}profile '${AWS_PROFILE}'${C_REST} ... "
  # delete old version of profile from credentials file
  SED_MARKER="##- MFA $AWS_PROFILE"
  sed -Ei "/$SED_MARKER/,/$SED_MARKER/d" "$HOME/.aws/credentials"
  # append new credentials
  TMP="$HOME/.aws/credentials"
  echo "$SED_MARKER start"                                  >> "$TMP"
  echo "[$AWS_PROFILE]"                                     >> "$TMP"
  echo "aws_access_key_id = $AWS_ACCESS_KEY_ID"             >> "$TMP"
  echo "aws_secret_access_key = $AWS_SECRET_ACCESS_KEY"     >> "$TMP"
  echo "aws_session_token = $AWS_SESSION_TOKEN"             >> "$TMP"
  echo "$SED_MARKER end"                                    >> "$TMP"
  echo "done."

  echo "* done."
  local VALIDITY_STR=$(date --date=@$AWS_TOKEN_VALIDITY +%H:%M:%S)
  echo "${DINFO} ${H_GREN}token valid until ${VALIDITY_STR}${C_REST}"
}


# gat = Get Aws sessionToken
gat() {
  local TOKEN_DURATION=28800 # 8h
  local FORCE_TOKEN="no"
  local USE_PROFILE

  if [ "$2" = "-f" ] ; then
    FORCE_TOKEN="yes"
    USE_PROFILE="$1"
  elif [ "$1" = "-f" ] ; then
    FORCE_TOKEN="yes"
    USE_PROFILE="${2:-${AWS_MFA_BASE:-default}}"
  else
    USE_PROFILE="${1:-${AWS_MFA_BASE:-default}}"
  fi
  echo "$DINFO using ${H_GREN}profile '${USE_PROFILE}'${C_REST}"
  TOKEN_FILE="$HOME/.aws/token.$USE_PROFILE.sh"
  # check if we already have a session token active
  if [ "$FORCE_TOKEN" = "yes" ] ; then
    echo "$DINFO ${H_REDD}Force-creating${C_REST} new token ..."
    _aws_get_new_token $USE_PROFILE
  else
    _aws_load_token $USE_PROFILE || _aws_get_new_token $USE_PROFILE
  fi
}

# rat = Re-use Aws sessionToken
# same as "gat" now
rat() {
  gat "$@"
}
