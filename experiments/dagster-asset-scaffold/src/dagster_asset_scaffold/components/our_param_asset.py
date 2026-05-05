import random

import dagster as dg

# SCENARIO:
#
# As described, we want to read several CSV files into several tables.
# key facts:
#   - the code is the same
#   - the only thing differing is "input file" and "target_table".


# =================================================================================================


# added manually from tutorial - this is our "configuration" structure.
# key facts:
#   - each dg.Model will be a Pydantic model
#   - this will become our YAML structure for configuration
# HERE we won't configure the input file. the plan is to have an operation that triggers
# the asset with a configuration parameter representing the input file.
class CSVTable(dg.Model):
    table_name: str


# =================================================================================================


# Note: the component is NOT yet the asset, the component CREATES the asset. a component is
#       a parameterized ... "factory" (hello, java) which can create a bunch of stuff.
class OurParamAsset(dg.Component, dg.Model, dg.Resolvable):
    """
    COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    # added fields here will define params when instantiated in Python, and yaml schema via Resolvable
    # IMPORTANT: the component has a LIST parameter, but EACH ITEM of the list can become "something".
    # so if we want to create multiple assets, we don't need multiple components, we need ONE
    # component which "knows" about each asset info.
    import_configs: list[CSVTable]

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # THIS IS THE MAGIC METHOD.
        # "build_defs()" is responsible for actually creating the dagster resources, so this "is"
        # the factory in a sense.
        # (hello, java ... really, too familiar).

        created_assets = []

        for import_config in self.import_configs:
            # here we create the asset by defining an inline function.
            # probably there are other ways to do it as well, but hey.

            @dg.asset(name=import_config.table_name)
            def _table_asset(
                context,
                # a_resource: DummyResource,
            ):
                """
                Note two things:
                - yes, we can add "context", even if build_defs() already has a "context" parameter
                - two, we can also add a context here, like everywhere; nice.
                """
                result = random.randint(0, 10000)
                context.log("asset running :) ; result={}".format(result))
                return result

            created_assets.append(_table_asset)

        return dg.Definitions(
            assets=created_assets,
        )
