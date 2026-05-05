# Dagster asset factories

**Problem:** We have the _same_ code handling _different_ input data, realizing different assets.

**Example:** We regularly import CSV files into database tables. Each table is an `asset`, but the handling code
is fully parameterized and differs only in the input file and table names.

**Solution:** A bunch of "parameterized" assets, or "Asset Factories" in Dagster-speak.

## Sources

- (Component Intro)[https://docs.dagster.io/dagster-basics-tutorial/custom-components] -
  exactly our problem description
- (Asset Factories)[https://docs.dagster.io/guides/build/assets/creating-asset-factories] -
  tutorial realizing an asset factory; source for this

## Walkthrough & explanations

### Create the component

```bash
# create dagster project
uvx create-dagster@latest project dagster-quickstart

# scaffold a component - that component will be our parameterized asset (and maybe more)
# "OurParamAsset" = the component name, creates components/our_param_asset.py
dg scaffold component OurParamAsset
```

Now, enhance with the required stuff. I added plenty of in-code-comments to line out what and how
and where, and probably I forgot the most important things.

Key pointers:

- `components/our_param_asset.py`:
    - `class CSVTable`: the whole thing
    - member variable(s) `import_configs` of class `OurParamAsset` (the component)

Now is also a good point to see if we have errors, or if Dagster recognizes everything:

```bash
dg check defs
dg list components
```

So our status now is:

- We have a component (`OurParamAsset`), which will create one asset for each entry in its `.import_configs`
  member

... the **only question now left is**: How do we _fill_ this member variable?

### Make the component ... "component"

**Answer:** We write a "defs" YAML, and dagster does the rest for us. Woho! We can also use `dg` to help us here:

```bash
dg scaffold defs dagster_asset_scaffold.components.our_param_asset.OurParamAsset our_assets

# explanation
dg \                                      # dg cli
  scaffold \                              # create a scaffold
  dagster_asset[...].OurParamAsset \      # python classpath to our component
  our_assets                              # package to create within dagster_asset_scaffold/defs

# creates this file:
#   ./src/dagster_asset_scaffold/defs/our_assets/defs.yaml
```
