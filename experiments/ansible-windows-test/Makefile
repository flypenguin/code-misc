SHELL=/bin/bash

# ###########################################################################
#
# secrets management
#

# relative to repository root
GPG_DIR=gpg_keys

open:
	find . -iname "*.gpg" | while read GPG_FILE ; do \
	    UNSAFE_FILE=$${GPG_FILE%.gpg} ; \
	    gpg -d "$$GPG_FILE" > "$$UNSAFE_FILE"; \
	    chmod 600 "$$UNSAFE_FILE" ; \
	    touch -r "$$GPG_FILE" "$$UNSAFE_FILE" ; \
	done
.PHONY: open
.SILENT: open

clean-gpg:
	find . -iname "*.gpg" | while read GPG_FILE ; do \
	    DELETE_ME=$${GPG_FILE%.gpg} ; \
	    rm -rfv "$$DELETE_ME";  \
	done
	for EXT in key sec ; do \
	    find . -iname "*.$$EXT" | while read DELETE_ME ; do \
	        rm -rfv "$$DELETE_ME";  \
	    done ; \
	done
.PHONY: clean-gpg
.SILENT: clean-gpg

close: clean-gpg
.PHONY: close

# https://security.stackexchange.com/a/86751
_reencrypt:
	REPO_ROOT=$$(realpath --relative-to=. $$(git rev-parse --show-toplevel)) ; \
	RECIPIENTS="" ; \
	for RECIPIENT in "$$REPO_ROOT/$(GPG_DIR)/"* ; do \
	    RECIPIENTS="$$RECIPIENTS -f $$RECIPIENT" ; \
	done ; \
	find . -iname "*.gpg" | while read GPG_FILE ; do \
	    UNSAFE_FILE=$${GPG_FILE%.gpg} ; \
	    if [ "$(FORCE_REENCRYPT)" = "yes" -o "$$UNSAFE_FILE" -nt "$$GPG_FILE" ] ; then \
	        echo "** UPDATING $$GPG_FILE" ; \
	        gpg --yes -e $$RECIPIENTS "$$UNSAFE_FILE" ; \
	    else \
	        echo "-  skipping $$GPG_FILE" ; \
	    fi ; \
	done
.PHONY: _reencrypt
.SILENT: _reencrypt

reencrypt-force: FORCE_REENCRYPT=yes
reencrypt-force: _reencrypt
.PHONY: reencrypt-force
.SILENT: reencrypt-force

reencrypt: FORCE_REENCRYPT=no
reencrypt: _reencrypt
.PHONY: reencrypt
.SILENT: reencrypt
