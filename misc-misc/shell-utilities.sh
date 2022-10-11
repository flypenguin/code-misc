# SOURCE this if needed, or copy-paste into a larger script

# text colors
NC="\e[0m"
BK="\e[0;30m" ; BBK="\e[1;30m" ; LBK="\e[0;90m" ; BLBK="\e[1;90m"
RD="\e[0;31m" ; BRD="\e[1;31m" ; LRD="\e[0;91m" ; BLRD="\e[1;91m"
GN="\e[0;32m" ; BGN="\e[1;32m" ; LGN="\e[0;92m" ; BLGN="\e[1;92m"
YE="\e[0;33m" ; BYE="\e[1;33m" ; LYE="\e[0;93m" ; BLYE="\e[1;93m"
BL="\e[0;34m" ; BBL="\e[1;34m" ; LBL="\e[0;94m" ; BLBL="\e[1;94m"
MA="\e[0;35m" ; BMA="\e[1;35m" ; LMA="\e[0;95m" ; BLMA="\e[1;95m"
CY="\e[0;36m" ; BCY="\e[1;36m" ; LCY="\e[0;96m" ; BLCY="\e[1;96m"
GR="\e[0;37m" ; BGR="\e[1;37m" ; LGR="\e[0;97m" ; BLGR="\e[1;97m"


eerr() {
  echo "$@" >&2
}


eout() {
  echo "$@"
}


# $@ - text lines to print on error.
#      first line is prefixed with "ERROR: ", and all others
#      with spaces.
checkerr() {
  if [ "$?" != "0" ] ; then
    eerr -e "\n\n${BRD}ERROR:${NC} $1"
    shift
    for line in "$@" ; do
      eerr "       $line"
    done
    exit 255
  fi
}



