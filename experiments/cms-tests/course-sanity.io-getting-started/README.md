# Sanity.io

- Date of creation: 2025-12-31
- Date of last substantial update: 2025-12-31

## TL;DR (summary)

- following "[Day one content operations](https://www.sanity.io/learn/course/day-one-with-sanity-studio)"
- requirements: `pnpm`, ...

### first impressions

Just from following the "Day one ..." videos:

- The data schema feature looks really nice, will apply that thinking to other CMS tests.

## Process

```shell
# Create the example project with the sanity cli
# source: https://www.sanity.io/learn/course/day-one-with-sanity-studio/hello-studio
# NOTE: WILL ASK FOR LOGIN
pnpm create sanity@latest \
    --template clean \
    --create-project "Day One Content Operations" \
    --dataset production \
    --typescript \
    --output-path project-day-one/apps/studio
```

I aborted here for now, because _my_ requirement is to have _fully_ self-hosted solution.

## Non-final verdict

- The ugly
  - Violoates my personal "fully self-hostable, no account required" requirement.
- The bad
  - Maybe ?? too TypeScript / React centric, not a WebDev / React / ... guy here.
- The good
  - The data schema feature _really_ looks useful, real pity that I need an account even for simply testing it.
