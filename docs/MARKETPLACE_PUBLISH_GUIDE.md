# 📦 Zero-Cost Extension & Package Publishing Guide

This guide covers how to publish T-Zero to the official VS Code / Cursor marketplaces and package registries at **$0.00 cost**.

---

## 1. Open VSX Registry (For Cursor, Windsurf, VSCodium)

Open VSX is the open-source extension registry used by **Cursor**, **Windsurf**, Gitpod, and VSCodium. Publishing is 100% free and instant.

### Steps:
1. Go to [https://open-vsx.org](https://open-vsx.org) and sign in with your GitHub account (`toprakahmetaydogmus`).
2. Click your profile picture -> **Settings** -> **Access Tokens**.
3. Generate a new Access Token.
4. Create a namespace `siber-akademi` (matches `publisher` in `package.json`).
5. Run from your terminal:
   ```bash
   npx ovsx publish dist/tzero-vscode-10.0.0.vsix -p <YOUR_ACCESS_TOKEN>
   ```
6. **Done!** Cursor and Windsurf users can now search and install "T-Zero" directly inside their editor!

---

## 2. Microsoft Visual Studio Code Marketplace

The official Microsoft VS Code Marketplace is also **100% free**.

### Steps:
1. Go to [https://marketplace.visualstudio.com/manage](https://marketplace.visualstudio.com/manage) and sign in.
2. Create a Publisher named `siber-akademi`.
3. Create a Personal Access Token (PAT) on Azure DevOps with "Marketplace (Manage)" scope.
4. Run from your terminal:
   ```bash
   npx @vscode/vsce publish -p <YOUR_PAT_TOKEN>
   ```
5. **Done!**

---

## 3. PyPI (Python Package Index) — `tzero-mcp 10.0.0`

Publishing python packages to PyPI is 100% free.

### Steps:
1. Build distribution wheel and sdist:
   ```bash
   python -m build
   ```
2. Upload to PyPI via twine:
   ```bash
   twine upload dist/*
   ```
3. Developers can now run:
   ```bash
   pip install --upgrade tzero-mcp
   ```
