# TallyCheck marketing site

Static HTML + SCSS. No framework.

```bash
npx nx build website                          # dist/apps/website
npx nx build website --configuration=development   # readable CSS + source maps
npx nx serve website                          # http://localhost:4300
```

## Why it lives here

Solely so it consumes the same design tokens as the product. `styles/main.scss`
does `@use 'theme/src/styles'`, resolved via sass `--load-path=libs`, so a brand
change is one edit in `libs/theme` instead of two edits in two repos that drift.

## Why it is not an Angular app

A marketing page has no application state and needs to be indexable. An Angular
SPA would cost a JS bundle and client-side rendering for content that is a single
static document. The trade-off: it cannot use `@omni/ui` components, which are
Angular. It gets the tokens, which is the part that matters for brand
consistency.

## Provenance — read before trusting this content

This was **rebuilt in the monorepo, not migrated**. The original
`Tallycheck-company-website` repo in the `tallycheckltd` org was not available
locally, so the structure and copy here were reconstructed. **Diff this against
that repo before it replaces anything**, in particular for:

- content that existed there and is missing here
- analytics, verification tags, or form endpoints wired into the original
- whatever `www.tallycheck.co.ke` currently points at

## Content decisions that need sign-off

The old copy said "Coming Soon" and described a university student-attendance
product. That is no longer accurate, so it was changed. Specifically:

- **"Coming Soon" removed.** There is a working product and live pilots. But the
  Play Store open-testing track is *paused*, so the site does **not** claim
  general availability or link a download. It says pilots are running and asks
  for a demo. If the track is resumed, add the store link.
- **Broadened past universities** to workplaces, education and children's
  ministries, matching what the backend actually supports.
- **No customer names.** Diakonia and Impala Club are deliberately absent —
  naming clients publicly needs their written consent, and one is a pilot rather
  than a reference customer.
- **No metrics, logos, testimonials or certifications**, because none can be
  substantiated yet. The security section describes mechanisms that exist in the
  code (device binding, schema-per-tenant isolation, audit logging) and nothing
  more.
- **No compliance claims.** The earlier draft mentioned the Kenya Data
  Protection Act; that is a claim to make once registration and a DPA are
  actually in place, not before.

## Deployment — not wired up

Root `vercel.json` builds the intranet demo, and a Vercel project takes one build
command. Publishing this site needs a **second** Vercel project pointed at the
same repo with:

```
build command:     npx nx build website
output directory:  dist/apps/website
```

That was left undone on purpose rather than editing `vercel.json` and silently
breaking the existing demo deployment.

## Known gap

`nx affected` will not mark this project affected when `libs/theme` changes: the
dependency is a SCSS `@use`, and Nx's graph only follows TypeScript imports. The
same is already true of `apps/intranet`. Rebuild the site deliberately after a
token change.
