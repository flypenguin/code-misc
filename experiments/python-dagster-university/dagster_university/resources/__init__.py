from dagster_duckdb import DuckDBResource

# EnvVar is similar to the os.getenv method that you’ve been using, but there is a key difference:
# EnvVar fetches the environmental variable’s value every time a run starts
# os.getenv fetches the environment variable when the code location is loaded
# https://tinyurl.com/2xgexbgn
from dagster import EnvVar

database_resource = DuckDBResource(
    database=EnvVar("DUCKDB_DATABASE")  # replaced with environment variable
)
