# Important: Rename app.py to main.py

To fix the Vercel deployment issue, you need to rename `app.py` to `main.py`.

## Why?

The file `app.py` conflicts with the `app/` package directory. When Python tries to import `from app.config.config`, it finds `app.py` instead of the `app/` package, causing the error:
```
ModuleNotFoundError: No module named 'app.config'; 'app' is not a package
```

## Steps to Fix

1. **Rename the file:**
   ```bash
   # On Windows (PowerShell)
   Rename-Item app.py main.py
   
   # On Linux/Mac
   mv app.py main.py
   ```

2. **The `api/index.py` file is already configured to look for `main.py` first**, so no code changes are needed.

3. **Commit and push:**
   ```bash
   git add .
   git commit -m "Rename app.py to main.py to fix Vercel deployment"
   git push
   ```

4. **Redeploy on Vercel** - it should now work correctly.

## Alternative (if you can't rename)

If you cannot rename the file, you can manually update `api/index.py` to look for `app.py` instead of `main.py`, but this is not recommended as it may still cause issues.
