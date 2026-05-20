# Deploy `mauckertgallery.com` to Cloudflare Pages

This is a one-page guide that walks you from a local site to a live one. No downtime — the Wix site keeps serving until the DNS change in Step 3.

---

## Step 1 — Push the code to GitHub

You need a free **github.com** account.

1. Go to **https://github.com/new**
2. Repository name: `mauckert-gallery` (or whatever)
3. **Private** is fine. Leave everything else default. Click **Create repository**.
4. Copy the repo URL GitHub shows you, e.g. `https://github.com/YOURNAME/mauckert-gallery.git`
5. In a terminal, from inside this `website/` folder:

   ```bash
   git remote add origin <THE-URL-YOU-COPIED>
   git push -u origin main
   ```

   The first push uploads ~280 MB of images — it'll take a few minutes.

---

## Step 2 — Connect Cloudflare Pages

You need a free **dash.cloudflare.com** account.

1. **Sign up / log in** at https://dash.cloudflare.com
2. Left sidebar → **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**
3. Authorise GitHub access, pick your repo
4. **Build settings:**

   | Setting | Value |
   |---|---|
   | Project name | `mauckertgallery` (becomes `mauckertgallery.pages.dev`) |
   | Production branch | `main` |
   | Framework preset | **Astro** |
   | Build command | `npm run build` |
   | Build output directory | `dist` |
   | Root directory | (leave empty) |

5. **Save and Deploy.** First build takes ~2–3 minutes. When it's green, open `mauckertgallery.pages.dev` and check the site.

From now on, every `git push` triggers a redeploy automatically. To preview before going live, push to a different branch — Cloudflare gives you a preview URL.

---

## Step 3 — Point the domain at Cloudflare

This is the only step that touches Wix. Don't cancel Wix yet — you're only editing DNS.

### On the Cloudflare Pages project:
1. Inside the Pages project → **Custom domains** → **Set up a custom domain**
2. Enter `mauckertgallery.com` → Continue
3. Cloudflare shows DNS records (a CNAME or A records). **Copy them.**
4. Repeat for `www.mauckertgallery.com`.

### On Wix:
1. Go to **www.wix.com** → log in
2. **Settings** → **Domains** → click `mauckertgallery.com`
3. **Advanced** or **DNS Records** → **Edit DNS**
4. Delete the existing records that point to Wix for `@` (root) and `www`
5. Add the records Cloudflare gave you. Typically:

   | Type | Name | Value | TTL |
   |---|---|---|---|
   | CNAME | `@` | `mauckertgallery.pages.dev` | Auto |
   | CNAME | `www` | `mauckertgallery.pages.dev` | Auto |

   If Wix refuses a CNAME on the root (`@`), use the A records that Cloudflare lists instead. Same effect.

6. Save. Cloudflare verifies within a few minutes; full DNS propagation worldwide can take up to 24 hours.

---

## Step 4 — Verify, then stop paying Wix

1. After 1–24 hours, open `mauckertgallery.com` in your browser, in a private window, and on your phone with mobile data. You should see the new site.
2. Once you've verified everywhere:
   - Wix → **Subscriptions** → cancel the **Premium plan** (website hosting)
   - **Keep** the **domain registration** active — that's what holds the `.com`. Renewal is ~€15/year.
3. (Optional, later) Transfer the domain to **Cloudflare Registrar** for at-cost pricing (~€9/year, no markup). Cloudflare has a one-click transfer wizard. Not urgent.

---

## How to update the site after launch

Anything you change in `data/*.json` or `src/**` — commit and push, Cloudflare rebuilds automatically:

```bash
git add .
git commit -m "update vita / add exhibition / new prices"
git push
```

Within ~2 minutes the live site reflects the change.

---

## Optional extras you can add later

- **Email at @mauckertgallery.com** — Cloudflare Email Routing (free) forwards `info@mauckertgallery.com` to your `web.de` inbox. Takes 5 minutes to set up. Then update the `mailto:` strings in the site.
- **Analytics** — Cloudflare Web Analytics is free and privacy-friendly (no cookies). Enable on the Pages project.
- **Custom 404 page** — drop `src/pages/404.astro` to override the default.

---

## If something goes wrong

- **The Cloudflare build fails** — read the build log; usually a typo in a JSON file. Run `npm run build` locally first to verify.
- **Wix shows a domain error** — make sure you removed the old Wix-pointing records before adding the Cloudflare ones.
- **DNS propagation feels slow** — check status at https://dnschecker.org/#A/mauckertgallery.com. Some regions update last.
- **Need to roll back to Wix temporarily** — put the original Wix DNS records back. Old site reappears within minutes to hours.
