# Guide 2FA — DEEPOTUS Admin

Ce guide vous accompagne dans l'activation (ou la réinitialisation)
de la **double authentification** sur l'admin de DEEPOTUS.

> **Pourquoi c'est obligatoire pour le Cabinet Vault ?**
> Tous les endpoints `/api/admin/cabinet-vault/*` exigent que la 2FA soit
> activée — c'est la deuxième couche de sécurité après votre seed BIP39.
> Sans 2FA, le coffre-fort reste verrouillé.

---

## 1. État actuel (post-reset)

La 2FA a été **wipée** : aucune configuration en base, aucun secret
TOTP enregistré. Vous pouvez vous loguer admin avec **uniquement votre
mot de passe** (`deepotus2026`) sans code à 6 chiffres.

```bash
# Vérification rapide — devrait répondre 200 et retourner {enabled: false}
curl -s "$REACT_APP_BACKEND_URL/api/admin/2fa/status" \
     -H "Authorization: Bearer <votre token>"
```

---

## 2. Procédure de configuration (UI)

### Étape 1 — Préparer une app TOTP sur votre smartphone
Choisissez l'une de ces apps (gratuites, open standard) :

| App                | iOS / Android | Sauvegarde cloud |
|--------------------|---------------|------------------|
| **Authy**          | Oui / Oui     | Oui (recommandé) |
| **1Password**      | Oui / Oui     | Oui              |
| **Google Authenticator** | Oui / Oui | Oui (compte Google) |
| **Aegis** (Android) | —  / Oui     | Export local seul |

### Étape 2 — Activer la 2FA
1. Connectez-vous sur `https://prophet-ai-memecoin.preview.emergentagent.com/admin`
   avec le mot de passe `deepotus2026`. **Aucun code 2FA ne sera demandé**.
2. Dans le dashboard, ouvrez l'onglet **Sessions / Sécurité**.
3. Cliquez sur **« Activer la 2FA »** (le bouton apparaît tant que `enabled=false`).
4. Un **QR code** s'affiche, accompagné :
   - d'un **secret texte** (ex : `JBSWY3DPEHPK3PXP…`) à saisir manuellement si vous ne pouvez pas scanner,
   - de **10 codes de secours** (sauvegardez-les dans un endroit sûr — ils servent si vous perdez le téléphone).
5. Scannez le QR avec votre app TOTP. Un code à 6 chiffres apparaît, valable 30 s.
6. Saisissez ce code dans le champ **« Code de vérification »** et cliquez **Valider**.
7. Vous voyez maintenant `2FA enabled` ✅ — la session courante est marquée 2FA-OK et le Cabinet Vault devient accessible.

### Étape 3 — Tester
1. Déloguez-vous (`Logout`).
2. Reloguez-vous : le formulaire vous demande maintenant **mot de passe + code 2FA**.
3. Naviguez vers `/admin/cabinet-vault` — le formulaire d'init / unlock du Cabinet Vault doit s'afficher sans erreur 403.

---

## 3. Procédure rapide (CLI / curl)

Si vous préférez la ligne de commande :

```bash
export BURL="$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d'=' -f2)"

# 1) Login (sans 2FA puisqu'on vient de la reset)
TOKEN=$(curl -s -X POST "$BURL/api/admin/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"password":"deepotus2026"}' | jq -r .access_token)

# 2) Lancer le setup — récupère secret + URI + QR base64 + 10 backup codes
curl -s -X POST "$BURL/api/admin/2fa/setup" \
  -H "Authorization: Bearer $TOKEN" | jq

# Réponse :
# {
#   "secret": "JBSWY3DPEHPK3PXP...",
#   "otpauth_uri": "otpauth://totp/DEEPOTUS%3Aadmin%40deepotus?secret=...&issuer=DEEPOTUS",
#   "qr_png_base64": "iVBORw0KGgo...",
#   "backup_codes": ["abcd1234", ...]   # NOTÉS dans un coffre-fort
# }

# 3) Saisir l'URI dans votre app TOTP, ou décoder le QR :
echo "<base64 du QR>" | base64 -d > qr.png   # puis scanner avec une app

# 4) Récupérer un code à 6 chiffres dans l'app et le valider :
CODE="123456"
curl -s -X POST "$BURL/api/admin/2fa/verify" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"code\":\"$CODE\"}"
# → {"ok": true, "message": "2FA enabled."}
```

---

## 4. Récupération si vous perdez votre téléphone

Deux niveaux de récupération sont disponibles :

### A. Code de secours (préféré)
Dans le formulaire de login, cliquez sur **« Utiliser un code de secours »** et
saisissez l'un des 10 codes générés à l'étape 2. Chaque code n'est utilisable
qu'une seule fois ; pensez à régénérer la liste après usage.

### B. Force-reset (perte totale du device + des codes de secours)
Le nouvel endpoint **`POST /api/admin/2fa/force-reset`** wipe la 2FA
en n'exigeant que le mot de passe admin. Ensuite, repartez à l'étape 2.

```bash
TOKEN=...   # via /api/admin/auth/login (qui en mode 2FA-désactivée ne demande pas de code)
curl -s -X POST "$BURL/api/admin/2fa/force-reset" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"password":"deepotus2026"}'
# → {"ok": true, "message": "2FA reset. Run /2fa/setup to re-enroll."}
```

> Cette opération est **journalisée** dans `db.config.admin_2fa.reset_history`
> pour audit de sécurité.

---

## 5. Résumé des accès
| Endpoint | Requiert 2FA active ? | Requiert mot de passe ? |
|----------|----------------------|-------------------------|
| `POST /api/admin/auth/login` | non (login lui-même), mais demande TOTP au login si activée | oui |
| `POST /api/admin/2fa/setup` | non | non (token JWT suffit) |
| `POST /api/admin/2fa/verify` | non | non (token JWT suffit) |
| `POST /api/admin/2fa/disable` | **oui** (TOTP/backup) + password | oui |
| `POST /api/admin/2fa/force-reset` | non | **oui** (recovery) |
| `GET/POST /api/admin/cabinet-vault/*` | **oui** | implicite via JWT |

Tant que la 2FA est désactivée, la route `/admin/cabinet-vault` retourne **403 TWOFA_REQUIRED**. Activez la 2FA → le Cabinet Vault redevient utilisable.

---

## 6. Bonnes pratiques

- Sauvegardez les 10 backup codes dans un **gestionnaire de mots de passe** (1Password, Bitwarden) ou imprimez-les et rangez-les dans un coffre physique.
- Activez la **synchronisation cloud** de votre app TOTP (Authy, 1Password) pour ne pas perdre l'accès en cas de changement de téléphone.
- Une fois la 2FA active, **changez le mot de passe par défaut** (`deepotus2026`) via `Sécurité → Rotation du mot de passe` (l'endpoint exige TOTP + ancien mot de passe).
- Ne partagez jamais le **secret TOTP** ni l'URI `otpauth://` — il équivaut à votre mot de passe dynamique.
