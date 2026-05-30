# Push CosmoCore to GitHub

Local files are at `C:\Users\Lenovo\Projects\cosmocore`. Use these steps to create the remote repo and push.

## Option A — GitHub CLI (recommended)

```powershell
cd $env:USERPROFILE\Projects\cosmocore

git init
git add .
git commit -m "Initial CosmoCore platform: Swiss Ephemeris API, Celery, Expo mobile"

# Create private repo on your account (change name if taken)
gh repo create cosmocore --private --source=. --remote=origin --push
```

If the repo name exists:

```powershell
gh repo create cosmocore-enterprise --private --source=. --remote=origin --push
```

## Option B — GitHub website

1. Open https://github.com/new
2. Repository name: `cosmocore`
3. Do **not** add README (this project already has one)
4. Run:

```powershell
cd $env:USERPROFILE\Projects\cosmocore
git init
git add .
git commit -m "Initial CosmoCore platform"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/cosmocore.git
git push -u origin main
```

## Verify

```powershell
git remote -v
git log -1 --oneline
```

## After push

- Add GitHub Actions later for CI
- Add ephemeris files locally only (they are gitignored); document download in README
