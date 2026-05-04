# site — rekwa.xyz

Mono-repo qui contient les **trois sites** déployés sur Cloudflare Pages.

## 🌐 Sites en ligne

| URL                          | Source local | Description                                    |
|------------------------------|--------------|------------------------------------------------|
| `rekwa.xyz`                  | `landing/`   | Hub principal (page d'accueil)                 |
| `cv.rekwa.xyz`               | `cv/`        | Curriculum Vitae                               |
| `write-ups.rekwa.xyz`        | `writeups/`  | Write-ups CTF (généré depuis markdown)         |

## 📁 Structure

```
site/
├── DEPLOIEMENT.md          ← 📖 Guide de mise en ligne (à lire en premier)
├── README.md
├── .gitignore
│
├── landing/                ← Site rekwa.xyz (statique)
│   ├── index.html
│   ├── style.css
│   └── README.md
│
├── cv/                     ← Site cv.rekwa.xyz (statique)
│   ├── index.html
│   ├── style.css
│   └── README.md
│
└── writeups/               ← Site write-ups.rekwa.xyz (généré)
    ├── writeups/           ← 📝 TES .md VONT ICI (drag & drop)
    │   └── example-login-bypass.md
    ├── templates/          ← templates HTML (Jinja2)
    ├── static/css/         ← styles
    ├── scripts/build.py    ← générateur Python
    ├── requirements.txt
    └── README.md
```

## 🚀 Comment ça marche

Tout est dans **un seul repo GitHub**. Cloudflare Pages crée **3 projets** distincts qui tirent tous depuis ce repo, mais chacun avec :
- Un **dossier de build** différent (`landing/`, `cv/`, `writeups/dist/`)
- Une **commande de build** différente (vide pour les sites statiques, `python scripts/build.py` pour les write-ups)
- Un **domaine** différent

Quand tu pushes un commit, Cloudflare relance les 3 builds en parallèle et déploie. ⚡

## 📝 Workflow quotidien

### Ajouter un write-up

1. Va sur `github.com/Rekwaa/site/writeups/writeups/` (interface web)
2. **Add file → Create new file** (ou drag & drop un `.md`)
3. Format requis :

```markdown
---
title: "Nom du challenge"
ctf: "Nom du CTF"
category: "web"
difficulty: "medium"
date: "2026-05-04"
tags: ["sqli", "blind"]
---

# Description
...
```

4. Commit → Cloudflare build → ~1 min plus tard c'est en ligne 🎉

### Modifier le CV ou la landing

Édite `cv/index.html` ou `landing/index.html` directement sur GitHub → Commit → ~30 sec.

## 🛠 Tester en local

```bash
# Landing ou CV (statique)
cd landing/    # ou cd cv/
python3 -m http.server 8000

# Write-ups (build Python)
cd writeups/
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/build.py
cd dist && python3 -m http.server 8000
```

## 📖 Premier déploiement

Lis **`DEPLOIEMENT.md`** — guide complet pas à pas (~30 min).
