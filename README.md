# Mason Thomas site (Astro)

## Commands

- `npm install`
- `npm run dev`
- `npm run build`
- `npm run preview`

## Content editing

- Posts live in `src/content/posts/*.md` and render at `/<slug>/`.
- About page markdown lives in `src/pages/about/index.md`.
- About supports a right-side image column via frontmatter:

```yaml
images:
  - src: /images/about-1.jpg
    alt: At a campsite in Marin
  - /images/about-2.jpg
```

Put static files in `public/`.
