chkcmd() { command -v "$1" > /dev/null ; }


silent() { "$@" > /dev/null 2>&1 ; }


__run_prefix_lines() { sed -E "s/^/  /g" ; }
__run_log_echo() { __run_prefix_lines | tee -a "$1" ; }
__run_log_nope() { __run_prefix_lines | cat >> "$1" ; }
_run() {
  DEBUG="${DEBUG:-0}"
  _RUN_IGNORE_ERRORS="${_RUN_IGNORE_ERRORS:-0}"
  local RV=0
  (( DEBUG > 1 )) && return 0
  [[ -z "${_RUN_LOG_FILE:-}" ]] && local _RUN_LOG_FILE="$(mktemp -up . "cmd-$(date +%s)-XXXXX.log")" && shift
  if [[ "${_RUN_LOG_APPEND:-}" == "1" ]]; then
    if [[ -f "${_RUN_LOG_FILE}" ]]; then
      (printf "\n\n---\n## "; printf "%.0s-" {1..100}; echo) >> "${_RUN_LOG_FILE}"
    else
      printf -- '---\n' > "${_RUN_LOG_FILE}"
    fi
  else
    printf -- '---\n' > "${_RUN_LOG_FILE}"
  fi
  [[ "${_RUN_ECHO:-0}" == "1" ]] && local __ECHO_CMD="__run_log_echo" || local __ECHO_CMD="__run_log_nope"
  printf "##  COMMAND: %s\ncommand_args:\n" "$(echo "$@")" >> "${_RUN_LOG_FILE}"
  local _CMD="" ; for _CMD in "$@" ; do echo "  - \"${_CMD//\"/\\\"}\"" >> "${_RUN_LOG_FILE}" ; done
  echo -e "\ncombined_output: |" >> "${_RUN_LOG_FILE}"
  echo ">>> $@"
  "$@" 2>&1 | $__ECHO_CMD "${_RUN_LOG_FILE}" || RV=$?
  printf '\n\nreturn_value: %d\n' "$RV" >> "$_RUN_LOG_FILE"
  (( _RUN_IGNORE_ERRORS != 1)) && (( RV != 0 )) && cat "${_RUN_LOG_FILE}"
  return $RV
}


get_engine() {
  chkcmd docker && ENGINE="docker"
  chkcmd podman && ENGINE="podman"
  if [[ -z "${ENGINE:-}" ]]; then
    echo "ERROR: no suitable build app found."
    return 1
  fi
  echo "Using builder: $ENGINE"
  export ENGINE
}


DEBUG="${DEBUG:-0}"
(( DEBUG == 1 )) && set -x
set -euo pipefail
