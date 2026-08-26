# Hosting guide — getting tldr-api onto a real, public URL

Everything up to this point (tests, Docker build, CI, even a simulated deploy) has been
verified to work *locally*. This file is the last mile: the actual clicks and commands to
get `../build_from_scratch/` running on the internet, for free, with your own GitHub
account and your own free Render account. Nobody can do this step for you — it needs your
own accounts — but it takes about fifteen minutes and every step below is exactly what to
do.

Background reading if you want the "why" before the "how": `../knowledge/09_deploying_to_render_or_cloud_run.md`
(concepts) and `../build_from_scratch/render.yaml` (the actual config this guide uses).

## 1. Push `build_from_scratch/` to GitHub

You have two reasonable options:

**Option A — its own repo (simplest).** Create a new, empty GitHub repo (e.g.
`tldr-api`), then push the *contents* of `build_from_scratch/` to it as the repo root:

```powershell
cd build_from_scratch
git init
git add .
git commit -m "tldr-api: tested, containerized, ready to deploy"
git branch -M main
git remote add origin https://github.com/<you>/tldr-api.git
git push -u origin main
```

**Option B — a subfolder of a bigger monorepo.** If you'd rather push this whole
`18-cicd-cloud-deployment` folder (or your whole `learning` repo) as one repo, that's fine
too — Render supports deploying from a subdirectory. When you create the Blueprint (step 3)
you'll set the service's **Root Directory** to `build_from_scratch` so Render only looks at
that folder for the Dockerfile and `render.yaml`. Either option works; Option A is slightly
simpler for a first deploy because there's no root-directory setting to get right.

Either way: double-check `.gitignore` is doing its job before you push —

```powershell
git status
```

should never show `.env` as a file about to be committed (only `.env.example` should be
tracked). If you're not sure, see `../labs/05_secrets_and_gitignore/` for a hands-on drill
on exactly this.

## 2. Create a free Render account

Go to [render.com](https://render.com) and sign up (the free tier needs no credit card).
Signing in with your GitHub account is the easiest path — it lets Render list your repos
directly in step 3.

## 3. Deploy via the Blueprint (`render.yaml`)

`render.yaml` already exists in `build_from_scratch/` and fully describes the service — you
don't hand-configure anything in Render's UI:

1. In the Render dashboard, click **New** → **Blueprint**.
2. Connect your GitHub account if you haven't, then pick the repo you pushed in step 1.
3. If you used Option B (monorepo), set **Root Directory** to `build_from_scratch` when
   prompted; if you used Option A, leave it as the repo root.
4. Render reads `render.yaml`, shows you the one service it's about to create
   (`tldr-api`, a Docker-runtime web service on the free plan, health-checked on `/ready`),
   and asks you to confirm.
5. Click **Apply** / **Create**. Render builds your Dockerfile and deploys it. First build
   takes a few minutes.

You did not have to write any deploy configuration by hand — that's the entire point of
committing `render.yaml`: it's Infrastructure-as-Code, so the deploy is reproducible and
reviewable like any other file in the repo.

## 4. Set the real secret (optional: `GEMINI_API_KEY`)

`render.yaml` has this line:

```yaml
- key: GEMINI_API_KEY
  sync: false
```

`sync: false` is what tells Render "don't put this in the file — ask the human." Because of
it, Render will prompt you to fill in `GEMINI_API_KEY` in the dashboard when you apply the
Blueprint, or you can set it any time after under your service → **Environment** tab → **Add
Environment Variable**. This key is NEVER written into `render.yaml` or any committed file —
that's the whole reason `sync: false` exists. Leaving it blank is completely fine: the app
defaults `TLDR_MODEL=offline`, which needs no key at all. Only set a real key (free from
[ai.google.dev](https://ai.google.dev)) and flip `TLDR_MODEL=gemini` in the Environment tab
if you want the real LLM path.

## 5. Wire up auto-deploy from GitHub Actions (`RENDER_DEPLOY_HOOK`)

`deploy.yml` already has a step that POSTs to a Render "deploy hook" URL after CI passes on
`main` — but it needs that URL as a GitHub secret to do anything (it skips harmlessly if the
secret is missing):

1. In Render, open your `tldr-api` service → **Settings** → find **Deploy Hook** and copy
   the URL shown there.
2. In your GitHub repo, go to **Settings** → **Secrets and variables** → **Actions** →
   **New repository secret**.
3. Name it exactly `RENDER_DEPLOY_HOOK`, paste the URL as the value, save.

From now on, every push to `main` that passes `ci.yml`'s tests will trigger `deploy.yml`,
which builds the image, tags it with the commit SHA, pushes it to GHCR, and then hits this
hook so Render redeploys. That's the whole CD loop, end to end, no manual clicking required
after today.

## 6. Verify the live URL

Render gives you a URL that looks like `https://tldr-api-xxxx.onrender.com`. Hit it for
real:

```powershell
curl https://tldr-api-xxxx.onrender.com/health
curl https://tldr-api-xxxx.onrender.com/ready
curl https://tldr-api-xxxx.onrender.com/version
curl -X POST https://tldr-api-xxxx.onrender.com/summarize `
  -H "Content-Type: application/json" `
  -d '{"text": "Docker packages an app with everything it needs to run so the same image behaves the same way everywhere."}'
```

Expect `/health` and `/ready` to both return 200 (after the cold start settles — see below),
`/version` to show the git SHA of the commit you just pushed, and `/summarize` to return a
real summary. If `/version`'s `git_sha` matches your latest commit, you've confirmed the
live service really is running the code you think it's running — not a stale build.

## 7. What to expect on Render's free tier

The free plan spins your service **down after about 15 minutes of no traffic**. The next
request after that wakes it back up, which takes roughly 30–60 seconds (a "cold start") —
during that window you may see `/ready` return 503 or the request simply hang briefly. This
is normal, expected free-tier behavior, not a bug in your app. If you need it always warm,
Render's paid plans remove the spin-down; for a portfolio project, free is fine — just
mention the cold start if you're demoing it live to someone.

## Alternative: Google Cloud Run

If you'd rather use GCP instead of Render, Cloud Run is the equivalent free-tier-friendly,
Docker-native host:

1. Install the `gcloud` CLI ([cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)),
   then `gcloud init` and `gcloud auth login` to connect it to a (free) Google Cloud
   project.
2. Deploy directly from source — Cloud Run will build your Dockerfile for you:

   ```powershell
   cd build_from_scratch
   gcloud run deploy tldr-api --source . --region us-central1 --allow-unauthenticated
   ```

   Or, if you'd rather deploy the exact image `deploy.yml` already builds and pushes to
   GHCR, point Cloud Run at that image directly instead of building again:

   ```powershell
   gcloud run deploy tldr-api `
     --image ghcr.io/<you>/tldr-api:latest `
     --region us-central1 --allow-unauthenticated
   ```

3. Set environment variables (`APP_ENV`, `TLDR_MODEL`, `GEMINI_API_KEY`, etc.) either with
   `--set-env-vars` on the deploy command or afterward in the Cloud Run console's
   **Variables & Secrets** tab — same principle as Render's Environment tab: never commit
   the real key.
4. Cloud Run's free tier includes a monthly allowance of requests, CPU, and memory that's
   generous enough for a portfolio project's traffic (check the current numbers on
   [cloud.google.com/run/pricing](https://cloud.google.com/run/pricing), they do change).
   Cloud Run also scales to zero when idle, so the same "cold start after inactivity" idea
   applies here too.

## If something goes wrong

- **Build fails on Render** — check the **Logs** tab on the service; Render shows the full
  `docker build` output, and almost every failure here is a typo in `render.yaml` or the
  Dockerfile, or a missing file that wasn't committed.
- **`/version` doesn't match the commit you expect** — you're probably looking at a stale
  deploy. Check the GitHub Actions run for `deploy.yml` on your latest commit; if it hasn't
  completed yet (or failed), Render is still serving the previous build.
- **`/ready` returns 503 right after a fresh deploy** — almost always just the cold start
  (see section 7). Wait ~30 seconds and try again before assuming something's broken.
- **`deploy.yml` isn't triggering a real deploy** — check that the `RENDER_DEPLOY_HOOK`
  secret is actually set (Settings → Secrets and variables → Actions on GitHub) and that
  `ci.yml` passed on that commit — `deploy.yml` only runs its own gate after a push to
  `main`, and the deploy step no-ops (on purpose) if the secret is missing.
- **A GitHub Actions run failed** — open the **Actions** tab on your repo, click the red
  run, and open the specific failing step — the log almost always names the exact command
  and line that broke, far more precisely than guessing from the outside.

See also `deploy_checklist.md` in this same folder for a tickable pre-deploy/post-deploy
checklist that walks through all of the above in order.
