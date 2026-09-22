# Documentation site

This directory contains the zero-build GitHub Pages site for Codex Jev Preflight.

The interface defaults to English and includes a built-in switch to Chinese. The
language preference is stored locally in the browser.

## Preview locally

From the repository root:

```bash
python3 -m http.server 8000 --directory docs
```

Open `http://127.0.0.1:8000/`.

## Deployment

The `docs/` directory is deployed by `.github/workflows/pages.yml`.

The site is static and does not call the live Jev API. The interactive assessment
preview runs entirely in the browser and is labeled as a local demo.
