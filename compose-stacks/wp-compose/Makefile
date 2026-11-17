# Local WordPress mirror, see README.md.
# Override the compose command with e.g. "make up COMPOSE='docker compose'".
COMPOSE ?= $(shell if podman compose version >/dev/null 2>&1; then echo podman compose; \
	elif docker compose version >/dev/null 2>&1; then echo docker compose; fi)
LOCAL_URL := http://localhost:8080
# --no-deps: otherwise every run recreates the db container
WP := $(COMPOSE) run --rm --no-deps cli wp
# Backups (tar.*, zip or directory), stored in .envrc by inspect-dump; command line values win.
# WP_ARCHIVE: wp-content, read when data/wp-content/ is missing.
# DB_ARCHIVE: SQL dump, read when data/dump.sql* is missing; defaults to WP_ARCHIVE.
WP_ARCHIVE ?= $(shell test ! -f .envrc || { . ./.envrc && printf %s "$$WP_ARCHIVE"; })
DB_ARCHIVE ?= $(shell test ! -f .envrc || { . ./.envrc && printf %s "$$DB_ARCHIVE"; })
export WP_ARCHIVE DB_ARCHIVE
# recipes pass backslash-newlines to the shell verbatim, so multi-line PHP lives here
define APP_PW_PHP
add_filter("random_password", fn() => "admin");
foreach (get_users(["role" => "administrator"]) as $$u)
	WP_Application_Passwords::application_name_exists_for_user($$u->ID, "local")
		|| WP_Application_Passwords::create_new_application_password($$u->ID, ["name" => "local"]);
endef
export APP_PW_PHP

.PHONY: up down reset clean

up: data/wp-content
	@test -n "$(COMPOSE)" || { echo "neither 'podman compose' nor 'docker compose' works" >&2; exit 1; }
	@ls data/dump.sql* >/dev/null 2>&1 || test -z "$(or $(DB_ARCHIVE),$(WP_ARCHIVE))" || ./unpack-db-dump "$(or $(DB_ARCHIVE),$(WP_ARCHIVE))"
	@./inspect-dump
	. ./.envrc && $(COMPOSE) up -d
	@# the DB image refuses TCP connections until the dump import has finished
	@printf "waiting for database import "; \
	. ./.envrc; for i in $$(seq 36); do \
		$(WP) db query "SELECT 1" >/dev/null 2>&1 && { echo " done"; exit 0; }; \
		test -n "$$($(COMPOSE) ps -q db)" || { echo; echo "db container stopped, see: $(COMPOSE) logs db" >&2; exit 1; }; \
		printf .; sleep 5; \
	done; \
	echo; echo "database not ready after 3 minutes, see: $(COMPOSE) logs db" >&2; exit 1
	@. ./.envrc && $(WP) core is-installed >/dev/null 2>&1 || { \
		echo "database has no WordPress tables with prefix '$$WP_TABLE_PREFIX': run 'make clean' and 'make up' again" >&2; exit 1; }
	. ./.envrc && $(WP) search-replace "$$WP_SITE_URL" "$(LOCAL_URL)" --all-tables --report-changed-only
	@# grep: PHP warnings may land on stdout
	@. ./.envrc && $(WP) user update $$($(WP) user list --role=administrator --field=ID 2>/dev/null | grep -E '^[0-9]+$$') \
		--user_pass=admin --skip-email >/dev/null 2>&1 || { echo "could not set admin passwords" >&2; exit 1; }
	@# application password "local" = "admin": the core generator returns the random_password filter's value
	@. ./.envrc && $(WP) eval "$$APP_PW_PHP" >/dev/null 2>&1 || { echo "could not create application passwords" >&2; exit 1; }
	@echo "ready: $(LOCAL_URL)/wp-admin, admins: $$(. ./.envrc && $(WP) user list --role=administrator --field=user_login 2>/dev/null | tr '\n' ' '), password and application password: admin"

data/wp-content:
	@./unpack-wp-content "$(WP_ARCHIVE)"

down:
	. ./.envrc && $(COMPOSE) down

# keeps ./dump.sql*, the archives and .envrc, so a plain "make up" rebuilds from the stored archives
reset clean:
	@# down needs no real values, only interpolation that succeeds
	WP_DB_IMAGE=x WP_DB_NAME=x WP_DUMP_FILE=x WP_DUMP_NAME=x WP_TABLE_PREFIX=x $(COMPOSE) --profile tools down -v
	rm -rf data
