# Handoff
_Updated by the last agent session. Keep under 40 lines._

## Current state
- Branch `staging`. SEO work for the US, Europe, the Gulf and Australia is committed, pushed and live on `resilai.org` (deployed 2026-11-20).
- Production frontend = commit `cd264ef` plus the SEO commit only, built in a throwaway worktree and deployed by hand with `firebase deploy --only hosting:marketing`. The other staging changes since 16 Nov are not in production.
- Frontend: `tsc -b` clean, 559 vitest tests pass, `npm run build:production` works.

## What changed last session (2026-11-20)
- New regional pages `/us`, `/europe`, `/gulf`, `/australia` (`frontend/src/pages/RegionLanding.tsx`). Short aliases `/eu`, `/uk`, `/gcc`, `/middle-east`, `/au` redirect to them.
- One data file drives titles, descriptions, regional copy, hreflang and the sitemap: `frontend/src/seo/publicRoutes.json`. Edit copy there, nowhere else.
- `frontend/scripts/prerender-seo.mjs` runs after `build` and `build:production`. It writes a static `<route>.html` for 22 public routes (own title, canonical, hreflang, JSON-LD, plain-text body) and `sitemap.xml`. Reason: AI crawlers do not run JavaScript and were reading the home page's tags on every URL.
- `firebase.json`: `cleanUrls: true` on the `marketing` target only, so `/europe` serves `europe.html`. Checked locally with `firebase serve --only hosting:marketing`.
- `RouteSEO` sets tags on public pages that had none (About, Results, AI, Contact, Security, Pilot, Docs).
- `SEOHead` takes `alternates` (hreflang). Home schema no longer says the price is 0.
- `llms.txt` and `llms-full.txt` have a regional section. `robots.txt` names the AI search crawlers and no longer lists `llms.txt` as a sitemap.
- OpenSEO plugin installed for Claude Code (user scope). Not signed in yet.

## Marketing and fundraising (2026-11-27)
- Drafts are in the untracked folders `docs/marketing/` (start at `00-stock-take.md`) and `docs/investor/`. Never `git add` them; they are not in `.gitignore`, so avoid `git add .`.
- Nothing has been sent, posted or submitted. Founder blanks are marked `[OWNER]`.
- Tracked public files contradict the pricing page and make unsupported claims: `BUSINESS_MODEL.md`, `EXECUTIVE_OVERVIEW.md`, `frontend/public/pricing.md` (insurer names), `llms.txt` (connector list). Not fixed.

## Next steps
0. Run Microsoft 365 against a real tenant before any demo or outreach.
1. The GitHub pipeline cannot deploy: step "Governance CLI validation" has failed on every staging push since 2026-11-08. Fix it before relying on CI.
2. Submit `https://resilai.org/sitemap.xml` in Google Search Console and Bing Webmaster Tools.
3. Sign in to OpenSEO (`/mcp` → OpenSEO), then run `/openseo:seo-audit` and `/openseo:ai-visibility-audit` for real ranking data.
4. `public/sitemap.xml` is generated. Refresh it with `node scripts/prerender-seo.mjs dist-production --public` after editing the JSON, and bump `lastmod` there.

## Open questions / gotchas
- Regional copy only claims what `app/services/governance/compliance_engine.py` lists. If a framework is added or removed there, update `publicRoutes.json`.
- Pages with their own `<SEOHead>` (Landing, Pricing, guides) duplicate their title and description in `publicRoutes.json` for the static file. Keep both in step.
- Google Maps "local SEO" does not apply: there is no storefront or Google Business Profile.
- `npm run lint` fails before it starts: installed ESLint is 4.19.1 but the config is the v9 flat format. Not touched.
- Files that were already uncommitted before this session (agent instruction files, `graphify-out/`, untracked local folders) were left alone.
- Staging and demo builds are not prerendered and have no `cleanUrls`.
