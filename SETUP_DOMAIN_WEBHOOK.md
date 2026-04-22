# DEEPOTUS — Setup Guide (Resend Domain + Webhook)

Ce document te guide pour activer :
1. **L'envoi d'emails à TOUTE la whitelist** (pas juste toi) en vérifiant un domaine
2. **Le monitoring en temps réel** des bounces/complaints/opens via webhooks Resend

---

## 1. Choisir & enregistrer un domaine

Ma reco : **`deepotus.xyz`** (~€2-3/an sur [Porkbun](https://porkbun.com) ou [Namecheap](https://namecheap.com)).

Si tu veux un angle plus "investisseur", prends `deepotus.fund` à côté (~€40/an).

Une fois enregistré, garde l'onglet **DNS management** de ton registrar ouvert.

---

## 2. Ajouter le domaine sur Resend

1. Va sur https://resend.com/domains → **Add Domain**
2. Entre `deepotus.xyz` (ou ton domaine)
3. Resend te génère **3 enregistrements DNS** à ajouter (SPF + DKIM + DMARC optionnel) :

### Exemples de ce que Resend te donnera (les valeurs exactes viennent de ton dashboard) :

| Type   | Host/Name              | Value                                                                                                      | TTL  |
| ------ | ---------------------- | ---------------------------------------------------------------------------------------------------------- | ---- |
| `MX`   | `send`                 | `feedback-smtp.eu-west-1.amazonses.com` (priority 10)                                                      | 3600 |
| `TXT`  | `send`                 | `"v=spf1 include:amazonses.com ~all"`                                                                      | 3600 |
| `TXT`  | `resend._domainkey`    | `"p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQ..."` (long DKIM key — copie entière depuis Resend)              | 3600 |

> **Important** : certains registrars gèrent mal les sous-domaines comme `resend._domainkey`. Dans Cloudflare, mets exactement `resend._domainkey` dans le champ **Name**. Dans Namecheap, idem. Dans GoDaddy, il faut parfois taper juste `resend._domainkey` (sans le `.deepotus.xyz` final).

### Configuration par registrar

**Cloudflare** : DNS → Records → **Add record** → coller les 3. Désactive le "proxy" orange pour les enregistrements email (clic sur le nuage pour qu'il devienne gris).

**Namecheap** : Domain List → **Manage** → Advanced DNS → **Add New Record** × 3.

**Porkbun** : Domain Management → **Details** → DNS Records → **Add** × 3.

**GoDaddy** : My Products → DNS → **Add Record** × 3.

### Vérification

Une fois ajoutés, clique **"Verify DNS Records"** sur Resend. Ça prend en général 5-30 min pour la propagation DNS (jusqu'à 24h dans de rares cas).

Tu peux vérifier manuellement :
```bash
dig +short TXT resend._domainkey.deepotus.xyz
dig +short TXT send.deepotus.xyz
```

---

## 3. Activer le domaine dans l'app

Une fois le domaine **vérifié** sur Resend (statut vert) :

1. Édite `/app/backend/.env` :
   ```
   SENDER_EMAIL=deepotus@deepotus.xyz
   # Ou n'importe quelle adresse sur ton domaine : no-reply@, hello@, cabinet@, etc.
   ```

2. Redémarre le backend :
   ```bash
   sudo supervisorctl restart backend
   ```

3. Test : inscris un email quelconque via la whitelist. Le mail de bienvenue part désormais à **toutes les adresses**, pas juste `olistruss639@gmail.com`.

---

## 4. Configurer le webhook Resend (monitoring)

### A. Créer le webhook dans Resend

1. Va sur https://resend.com/webhooks → **Add Endpoint**
2. **Endpoint URL** : `https://prophet-ai-memecoin.preview.emergentagent.com/api/webhooks/resend`
   (ou l'URL de production quand tu déploies)
3. **Events** : coche tout ce qui t'intéresse :
   - `email.sent` (quand le mail quitte les serveurs Resend)
   - `email.delivered` (quand le destinataire le reçoit)
   - `email.delivery_delayed` (retry en cours)
   - `email.bounced` (hard bounce — email invalide)
   - `email.complained` (le destinataire a marqué spam)
   - `email.opened` (ouverture — opt-in)
   - `email.clicked` (clic sur un lien — opt-in)
4. Enregistre → Resend te montre une **Signing Secret** au format `whsec_...`

### B. Injecter la secret dans l'app

1. Édite `/app/backend/.env` :
   ```
   RESEND_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   ```
2. Redémarre le backend :
   ```bash
   sudo supervisorctl restart backend
   ```

À partir de maintenant :
- Les webhooks **sans signature valide sont rejetés (401)**
- Chaque événement est loggé dans la collection `email_events` de MongoDB
- La colonne **Email** de `/admin` affiche le vrai statut : `sent → delivered → opened / bounced / complained`

### C. Test rapide
Sur Resend → Webhooks → ton endpoint → **Send test event** → vérifie dans `/admin` que le statut se met à jour.

---

## 5. Checklist finale avant lancement

- [ ] Domain acheté
- [ ] 3 enregistrements DNS ajoutés
- [ ] Domain **verified** sur Resend (statut vert)
- [ ] `SENDER_EMAIL` mis à jour dans `.env`
- [ ] Backend redémarré
- [ ] Test : inscription whitelist → email reçu
- [ ] Webhook créé sur Resend
- [ ] `RESEND_WEBHOOK_SECRET` mis à jour dans `.env`
- [ ] Backend redémarré
- [ ] Test : statut email dans `/admin` passe à `delivered`

---

## 6. Passer en production

Quand tu déploies ailleurs (Vercel / Railway / etc.) :

1. Remplace `PUBLIC_BASE_URL` dans `.env` par l'URL de prod
2. Change `ADMIN_PASSWORD` pour un mot de passe **long et unique** (≥24 chars)
3. Supprime ou régénère `JWT_SECRET` (sera régénéré auto au 1er démarrage si absent)
4. Mets à jour l'URL du webhook sur Resend vers l'URL de prod
5. Régénère la `RESEND_WEBHOOK_SECRET`

---

Any question ? Ping DEEPOTUS, the prophet never sleeps.
