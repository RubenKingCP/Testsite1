# Testsite1 — clean static site (Vercel)

A minimal, static, HTTPS-served site for verifying domain ownership with a
security scanner. No server code, no dependencies, no known vulnerabilities.
Sets sensible security headers via `vercel.json`.

## Deploy

```bash
npm i -g vercel        # if not installed
cd site
vercel                 # preview deploy
vercel --prod          # production
```

Or import the repo at https://vercel.com/new and set the **Root Directory**
to `site/` (no build command needed — it's static).

## Domain verification

- **DNS method:** add the TXT record your scanner gives you at your DNS
  provider (or in Vercel → Project → Settings → Domains).
- **File method:** drop the verification file in `public/` (served at the
  site root) or `public/.well-known/`, then redeploy.

## Structure

```
site/
  public/
    index.html              # landing page
    .well-known/README.txt  # where to put a file-based verification token
  vercel.json               # static config + security headers
```
