import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";

export default defineConfig({
  site: "https://masont.dev",
  outDir: "./docs",
  integrations: [mdx()]
});
