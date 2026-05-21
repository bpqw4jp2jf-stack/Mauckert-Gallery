import { defineConfig } from "astro/config";

import cloudflare from "@astrojs/cloudflare";

export default defineConfig({
  site: "https://www.mauckertgallery.com",
  build: { format: "directory" },
  image: { service: { entrypoint: "astro/assets/services/sharp" } },
  adapter: cloudflare()
});