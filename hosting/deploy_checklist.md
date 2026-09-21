# Deploy checklist

A concrete, tickable list — work through it in order the first time you deploy, and re-run the
post-deploy half after every subsequent push. See `HOSTING_GUIDE.md` for the full walkthrough
behind each item.

## Before you push

- [ ] `pytest -q` passes locally, run from the repo root (15 tests, 0 failures).
- [ ] `.env` is NOT tracked by git — confirm with `git ls-files | Select-String "\.env$"`
      (PowerShell) returns nothing. Only `.env.example` should ever be committed.
- [ ] `docker build -t tldr-api:local .` succeeds locally.
- [ ] `docker run` the built image and curl all four endpoints (`/`, `/health`, `/ready`,
      `POST /summarize`) — all respond correctly.
- [ ] `.dockerignore` excludes `.env`, `.git`, and `tests/` from the build context.
- [ ] `render.yaml` is committed, with `sync: false` on `GEMINI_API_KEY` (never a real value in
      the file itself).

## Wiring up the platform (one-time setup)

- [ ] Code pushed to a GitHub repo (see `HOSTING_GUIDE.md` section 1 for the two layout options).
- [ ] Free Render account created, connected to GitHub.
- [ ] Service deployed via **New → Blueprint**, pointed at the repo (and the correct **Root
      Directory** if using the monorepo option).
- [ ] `GEMINI_API_KEY` set in Render's dashboard **Environment** tab (or left blank — the app
      defaults to `TLDR_MODEL=offline`, which needs no key).
- [ ] Render's **Deploy Hook** URL copied.
- [ ] That URL saved as the GitHub repository secret `RENDER_DEPLOY_HOOK` (Settings → Secrets
      and variables → Actions → New repository secret) — named exactly that, since
      `deploy.yml` reads it by that name.

## After every push to `main`

- [ ] `ci.yml` ran and went green (Actions tab) — lint + test + Docker build + smoke test all
      passed.
- [ ] `deploy.yml` ran after it and completed — `test-gate` passed, image built and pushed to
      GHCR tagged with the commit SHA, and the Render deploy hook was hit (check the last job's
      log — it prints a clear "skipping" message if the secret isn't set, so confirm it didn't).
- [ ] Live URL's `/health` returns `200` (may need ~30-60s if the free tier had spun down —
      that's a normal cold start, not a failure).
- [ ] Live URL's `/ready` returns `200`.
- [ ] Live URL's `/version` — the `git_sha` field matches the commit you just pushed. This is
      the single most important check: it's the difference between "the pipeline said it
      deployed" and "the live service is actually running what I think it's running."
- [ ] `POST /summarize` on the live URL returns a real summary for a test payload.
- [ ] README (the one in your deployed repo, or this project's root `README.md`) updated with
      the live URL, so it's easy to find later and easy to put in your portfolio/resume.
