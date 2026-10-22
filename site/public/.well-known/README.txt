Drop your scanner's domain-verification file here (or at the site root).

Many scanners ask you to either:
  1. Add a DNS TXT record to your domain, or
  2. Serve a specific file at a known path (often /.well-known/<name> or /<token>.html).

For option 2, place the file the scanner gives you in this folder (or in
site/public/) and redeploy. It will then be reachable at:
  https://<your-domain>/.well-known/<filename>
