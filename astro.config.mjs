import { defineConfig } from "astro/config";

import cloudflare from "@astrojs/cloudflare";
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://www.mauckertgallery.com",
  build: { format: "directory" },
  image: { service: { entrypoint: "astro/assets/services/sharp" } },
  integrations: [sitemap()],
  adapter: cloudflare()
});