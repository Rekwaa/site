# write-ups.rekwa.xyz

Sous-projet du mono-repo `site` qui génère le site des write-ups CTF.
Auto-déployé via Cloudflare Pages à chaque push.

## Workflow ultra simple : ajouter un write-up

1. Va sur le repo dans GitHub (interface web)
2. Ouvre le dossier `writeups/writeups/` (oui, double `writeups/` — désolé)
3. Clique sur **"Add file" → "Create new file"** (ou drag & drop un `.md`)
4. Nomme le fichier (ex: `htb-baby-rsa.md`)
5. Colle le contenu en respectant le format ci-dessous
6. Commit → Cloudflare reconstruit le site → en ligne en ~1 min ✨

## Format d'un write-up

Chaque fichier `.md` dans `writeups/` doit avoir un **front matter YAML** au début :

```
---
title: "Nom du challenge"
ctf: "Nom du CTF (ex: HackTheBox - Baby RSA)"
category: "crypto"          # web, crypto, pwn, reverse, forensics, misc, osint
difficulty: "medium"        # easy, medium, hard, insane
date: "2026-01-15"
points: 250                 # optionnel
tags: ["rsa", "fermat"]     # optionnel
---

# Description
Le contenu du write-up en markdown classique...
```

**Champs obligatoires** : `title`, `ctf`, `category`, `date`
**Champs optionnels** : `difficulty` (default: medium), `points`, `tags`, `author`

## Catégories disponibles

| Slug        | Label      |
|-------------|------------|
| `web`       | Web        |
| `crypto`    | Crypto     |
| `pwn`       | Pwn        |
| `reverse`   | Reverse    |
| `forensics` | Forensics  |
| `misc`      | Misc       |
| `osint`     | OSINT      |

Une catégorie inconnue est automatiquement classée en `misc`.

## Tester en local

```bash
# Depuis writeups/
python3 -m venv .venv
source .venv/bin/activate    # Linux/Mac
# .venv\Scripts\activate     # Windows
pip install -r requirements.txt

# Build + serve
python3 scripts/build.py
cd dist && python3 -m http.server 8000
# Ouvre http://localhost:8000
```

## Architecture

```
writeups/
├── writeups/           ← tes .md vont ici
├── templates/          ← templates Jinja2 (HTML)
├── static/css/         ← styles
├── scripts/build.py    ← le générateur Python
├── requirements.txt
└── dist/               ← généré (ignoré par git)
```

## Stack

- **Python** + Jinja2 + Markdown (lib `python-markdown` avec extensions)
- **Pygments** pour le syntax highlighting
- **Cloudflare Pages** pour l'hébergement et le build automatique
