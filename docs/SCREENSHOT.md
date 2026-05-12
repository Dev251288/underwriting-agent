# Capturing the dashboard screenshot

The README references `docs/dashboard.png` as the live dashboard hero image.
Capture it once on your machine; it does not need to be regenerated unless the
UI changes meaningfully.

## One-time setup

```bash
python main.py seed                            # creates 5 demo applications
python main.py serve                           # http://127.0.0.1:8000
```

## Capture

1. Open `http://127.0.0.1:8000` in Chrome.
2. Click into any seeded application — `C07D230C` has the richest dashboard
   (KYC + financial + property + conditions populated).
3. Use Chrome DevTools → Run command (Cmd/Ctrl+Shift+P) →
   **"Capture full size screenshot"**.
4. Save the resulting PNG as `docs/dashboard.png` (overwrite the placeholder).
5. Commit and push.

## Recommended viewport

Width 1440px before capturing — the dashboard is laid out for desktop
underwriter screens, and 1440 produces a clean readable image on GitHub.
