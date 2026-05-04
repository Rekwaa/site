#!/usr/bin/env python3
"""
build.py — Générateur statique pour write-ups.rekwa.xyz

Lit tous les .md dans writeups/, parse le front matter YAML,
convertit le markdown en HTML et génère le site dans dist/.

Front matter attendu dans chaque .md :
---
title: "Nom du challenge"
ctf: "Nom du CTF"
category: "web"          # web, crypto, pwn, reverse, forensics, misc
difficulty: "medium"     # easy, medium, hard, insane
date: "2026-01-15"
tags: ["sqli", "blind"]
---

Le contenu markdown commence ici.
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime
import html

import yaml
import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

# ============ CONFIG ============
ROOT = Path(__file__).parent.parent
WRITEUPS_DIR = ROOT / "writeups"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
OUTPUT_DIR = ROOT / "dist"

CATEGORIES = {
    "web": {"icon": "⚡", "color": "#60a5fa", "label": "Web"},
    "crypto": {"icon": "🔐", "color": "#a78bfa", "label": "Crypto"},
    "pwn": {"icon": "💥", "color": "#f87171", "label": "Pwn"},
    "reverse": {"icon": "⚙", "color": "#fbbf24", "label": "Reverse"},
    "forensics": {"icon": "🔍", "color": "#34d399", "label": "Forensics"},
    "misc": {"icon": "✦", "color": "#a1a1aa", "label": "Misc"},
    "osint": {"icon": "👁", "color": "#fb923c", "label": "OSINT"},
}

DIFFICULTIES = {
    "easy": {"label": "Easy", "level": 1},
    "medium": {"label": "Medium", "level": 2},
    "hard": {"label": "Hard", "level": 3},
    "insane": {"label": "Insane", "level": 4},
}


def slugify(text):
    """Convertit un titre en slug URL-friendly."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def parse_writeup(filepath):
    """Parse un fichier markdown avec front matter YAML."""
    content = filepath.read_text(encoding="utf-8")

    # Extraction du front matter
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if not match:
        print(f"⚠ {filepath.name} : pas de front matter détecté, ignoré")
        return None

    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as e:
        print(f"⚠ {filepath.name} : erreur YAML — {e}")
        return None

    body = match.group(2)

    # Validation
    required = ["title", "ctf", "category", "date"]
    for field in required:
        if field not in meta:
            print(f"⚠ {filepath.name} : champ '{field}' manquant, ignoré")
            return None

    # Conversion markdown → HTML avec extensions
    md = markdown.Markdown(extensions=[
        "fenced_code",
        "codehilite",
        "tables",
        "toc",
        "attr_list",
        "footnotes",
    ], extension_configs={
        "codehilite": {
            "css_class": "highlight",
            "guess_lang": False,
        }
    })
    html_content = md.convert(body)

    # Normalisation
    category = meta["category"].lower()
    if category not in CATEGORIES:
        print(f"⚠ {filepath.name} : catégorie '{category}' inconnue, classée en 'misc'")
        category = "misc"

    difficulty = meta.get("difficulty", "medium").lower()
    if difficulty not in DIFFICULTIES:
        difficulty = "medium"

    # Date
    date_val = meta["date"]
    if isinstance(date_val, str):
        try:
            date_obj = datetime.strptime(date_val, "%Y-%m-%d")
        except ValueError:
            date_obj = datetime.now()
    else:
        date_obj = datetime.combine(date_val, datetime.min.time())

    slug = slugify(f"{meta['ctf']}-{meta['title']}")

    return {
        "slug": slug,
        "filename": filepath.name,
        "title": meta["title"],
        "ctf": meta["ctf"],
        "category": category,
        "category_info": CATEGORIES[category],
        "difficulty": difficulty,
        "difficulty_info": DIFFICULTIES[difficulty],
        "date": date_obj,
        "date_str": date_obj.strftime("%d %b %Y"),
        "date_iso": date_obj.strftime("%Y-%m-%d"),
        "tags": meta.get("tags", []),
        "author": meta.get("author", "Ekwa"),
        "points": meta.get("points"),
        "html": html_content,
        "toc": md.toc if hasattr(md, "toc") else "",
        "url": f"/writeups/{slug}/",
    }


def build_site():
    print("🔨 Building write-ups site...\n")

    # Reset output
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir()

    # Copy static assets
    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, OUTPUT_DIR / "static")
        print(f"✓ Static files copied to dist/static/")

    # Setup Jinja2
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Parse all writeups
    writeups = []
    if WRITEUPS_DIR.exists():
        for md_file in sorted(WRITEUPS_DIR.glob("*.md")):
            wu = parse_writeup(md_file)
            if wu:
                writeups.append(wu)
                print(f"✓ Parsed: {wu['ctf']} / {wu['title']}")

    # Sort by date desc
    writeups.sort(key=lambda x: x["date"], reverse=True)

    # Stats
    stats = {
        "total": len(writeups),
        "by_category": {},
        "by_ctf": {},
    }
    for wu in writeups:
        stats["by_category"][wu["category"]] = stats["by_category"].get(wu["category"], 0) + 1
        stats["by_ctf"][wu["ctf"]] = stats["by_ctf"].get(wu["ctf"], 0) + 1

    # Render index page
    index_tpl = env.get_template("index.html")
    (OUTPUT_DIR / "index.html").write_text(
        index_tpl.render(
            writeups=writeups,
            categories=CATEGORIES,
            stats=stats,
            current_page="home",
        ),
        encoding="utf-8",
    )
    print(f"\n✓ Generated: index.html")

    # Render each writeup
    writeup_tpl = env.get_template("writeup.html")
    for wu in writeups:
        wu_dir = OUTPUT_DIR / "writeups" / wu["slug"]
        wu_dir.mkdir(parents=True, exist_ok=True)
        (wu_dir / "index.html").write_text(
            writeup_tpl.render(
                wu=wu,
                categories=CATEGORIES,
                current_page="writeup",
            ),
            encoding="utf-8",
        )
        print(f"✓ Generated: writeups/{wu['slug']}/")

    # Render category pages
    category_tpl = env.get_template("category.html")
    for cat_slug, cat_info in CATEGORIES.items():
        cat_writeups = [w for w in writeups if w["category"] == cat_slug]
        if not cat_writeups:
            continue
        cat_dir = OUTPUT_DIR / "category" / cat_slug
        cat_dir.mkdir(parents=True, exist_ok=True)
        (cat_dir / "index.html").write_text(
            category_tpl.render(
                writeups=cat_writeups,
                category=cat_slug,
                category_info=cat_info,
                categories=CATEGORIES,
                current_page="category",
            ),
            encoding="utf-8",
        )
        print(f"✓ Generated: category/{cat_slug}/")

    # 404 page
    not_found_tpl = env.get_template("404.html")
    (OUTPUT_DIR / "404.html").write_text(
        not_found_tpl.render(categories=CATEGORIES),
        encoding="utf-8",
    )
    print(f"✓ Generated: 404.html")

    print(f"\n✅ Build complete: {len(writeups)} write-ups → {OUTPUT_DIR}")


if __name__ == "__main__":
    build_site()
