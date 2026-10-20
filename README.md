# pdf-label-onboarding

Fixed URL, always the newest label:
https://andreashippypro.github.io/pdf-label-onboarding/labels/latest.pdf

Each run also keeps its own copy: .../labels/SPY-2026-<run number>.pdf

## One-time setup
1. Upload the contents of this folder to the repo root (keep the `.github`, `docs` and `fonts` folders).
   On github.com: Add file > Upload files. Drag the folders in. Hidden `.github` may not drag from Finder,
   so create `.github/workflows/label.yml` with Add file > Create new file and paste it in.
2. Settings > Pages > Source: Deploy from a branch > `main` / `/docs` > Save.
3. Settings > Actions > General > Workflow permissions > Read and write permissions > Save.

## Update the label (manual form)
Actions tab > Generate label > Run workflow > fill name, team, ... > Run.
After about a minute `latest.pdf` shows the new data. The URL does not change.

## Update from another system (automatic)
POST to https://api.github.com/repos/AndreaShippyPro/pdf-label-onboarding/dispatches
with a token that has Contents read/write on this repo:

    {"event_type":"new-label","client_payload":{"name":"Test User","contents":"Product","province":"MI"}}

Privacy: repo and PDFs are public. Use only data you are fine with everyone seeing.
