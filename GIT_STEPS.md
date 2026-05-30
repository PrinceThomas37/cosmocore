# Git setup — you create the repo, then push this folder

All project files live here:

`C:\Users\Lenovo\Projects\cosmocore`

## Step 1 — Create empty repo on GitHub

1. Go to https://github.com/new
2. **Repository name:** `cosmocore` (or any name you prefer)
3. **Public** or **Private** — your choice
4. Do **not** check “Add a README” (this folder already has one)
5. Click **Create repository**

GitHub will show you a page with setup commands. Use **Option 2** below on your PC.

## Step 2 — Initialize Git on your computer

Open **PowerShell** and run:

```powershell
cd $env:USERPROFILE\Projects\cosmocore

git init
git branch -M main
git add .
git status
```

You should see backend/, mobile/, README.md, etc. staged.

## Step 3 — First commit

```powershell
git commit -m "Initial commit: CosmoCore astrology platform"
```

## Step 4 — Connect to your GitHub repo

Replace `YOUR_USERNAME` and `REPO_NAME` with yours:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
```

Example:

```powershell
git remote add origin https://github.com/janedoe/cosmocore.git
```

## Step 5 — Push

```powershell
git push -u origin main
```

Sign in if Git asks (browser or personal access token).

## Step 6 — Verify

- Refresh your repo on GitHub — files should appear.
- Optional: `git remote -v` and `git log -1` on your PC.

---

## If Git is not installed

Download: https://git-scm.com/download/win

Then repeat from Step 2.

## If push asks for a password

GitHub no longer accepts account passwords for Git. Use either:

- **GitHub CLI:** `gh auth login`
- **Personal Access Token:** GitHub → Settings → Developer settings → Personal access tokens → use token as password when pushing

## Common issues

| Problem | Fix |
|--------|-----|
| `remote origin already exists` | `git remote remove origin` then add again |
| `failed to push` / rejected | Ensure GitHub repo is **empty** (no README added on create) |
| Large ephemeris files | `.gitignore` excludes `*.se1` — download ephemeris locally only |
