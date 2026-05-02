# Pousser le code vers GitHub — contournement Vercel Hobby

## Le problème

Vercel **Hobby plan** applique une règle de sécurité : les builds ne sont
déclenchés **que** pour les commits dont l'author email appartient à un
membre du projet Vercel. Or les commits que je produis (depuis Emergent)
sont signés `emergent-agent-e1 <github@emergent.sh>` — qui **n'est pas**
un membre de votre Vercel. Résultat :

- Le push GitHub part bien sur votre repo.
- Vercel le voit mais **refuse de builder** (log : `Git author has no access`).
- Votre site prod reste sur l'ancien build tant que vous n'y remédiez pas.

Vous avez déjà mis en place un contournement avec les **Deploy Hooks** :
un webhook qui force un build sur une branche, peu importe l'author.
C'est la solution recommandée. Ce doc récapitule le workflow complet.

---

## Workflow complet (à suivre après chaque session Emergent)

### 1. Dans Emergent : pousser le code

Le workspace `/app` est un clone git local. Emergent l'a déjà auto-committé.
Vous avez **un bouton** dans l'interface Emergent (coin haut-droit) :

- **"Save to GitHub"** — Emergent pousse les commits locaux vers votre repo
  GitHub (la branche configurée, en général `main`).

**À faire** : cliquez ce bouton une fois à la fin de chaque session. Sans ça,
aucune modification n'arrive sur GitHub.

> Si le bouton est masqué, il faut d'abord lier votre repo GitHub
> à Emergent dans **Settings → Integrations → GitHub**.

---

### 2. Sur Vercel : déclencher le Deploy Hook

Le Deploy Hook est une URL secrète qu'un `POST` HTTP **force** Vercel à
lancer un build sur une branche donnée, en ignorant la règle author.

**Configuration initiale** (à faire une seule fois) :

1. Vercel Dashboard → votre projet → `Settings` → `Git` → `Deploy Hooks`
2. Cliquez sur `Create Hook`
3. Nom : `emergent-push` · Branche : `main` (ou celle que vous voulez)
4. Vercel génère une URL du type :
   `https://api.vercel.com/v1/integrations/deploy/prj_xxx/yyy`
5. **Copiez-la** et gardez-la privée.

**Déclenchement** (à chaque push Emergent) :

```bash
curl -X POST "https://api.vercel.com/v1/integrations/deploy/prj_xxx/yyy"
```

Retour attendu :
```json
{ "job": { "id": "...", "state": "PENDING", "createdAt": ... } }
```

Puis suivez le build dans **Vercel → Deployments**. Compte 1–3 minutes.

> Pour économiser un `curl`, créez un **bookmark navigateur** avec
> `javascript:fetch('https://api.vercel.com/v1/integrations/deploy/prj_xxx/yyy',{method:'POST'}).then(r=>r.json()).then(j=>alert('Vercel build launched: '+j.job.id))`
> — un clic = un build.

---

### 3. Sur Render : auto-deploy normal

Render (backend) **n'a pas** cette restriction author — il accepte tout commit
sur la branche watched. Le backend se redéploie donc automatiquement ~2 min
après le push GitHub.

Vérifiez dans **Render → votre service → Events** que vous voyez bien
`Deploy live` avec le SHA commit le plus récent.

---

## Checklist post-session Emergent

À reproduire à la main (3 minutes) à chaque fin de session :

- [ ] **"Save to GitHub"** dans Emergent (bouton top-right)
- [ ] Ouvrir GitHub → votre repo → vérifier que les derniers commits sont visibles
- [ ] Trigger **Vercel Deploy Hook** (curl ou bookmark)
- [ ] Attendre **~2 min** (Render + Vercel build en parallèle)
- [ ] Ouvrir https://www.deepotus.xyz/admin et valider que le changement est en prod
- [ ] Si un nouveau secret a été ajouté au Cabinet Vault **en preview** mais pas
      en prod, le re-saisir sur Render (les vaults preview ↔ prod sont isolés)

---

## Alternatives au Deploy Hook

Si vous préférez ne pas dépendre du Deploy Hook :

### Option A — Forker le commit avec votre author

Après "Save to GitHub", rebaser / reauthor localement :

```bash
git clone https://github.com/VOTRE-USER/VOTRE-REPO.git
cd VOTRE-REPO
# Rewrite the latest N commits to use YOUR author
git rebase -i HEAD~5   # then replace emergent-agent-e1 with yours
# or use git filter-branch / git filter-repo for bulk rewrites
git push --force
```

Inconvénient : plus lourd, et une force-push réécrit l'historique — à
éviter si d'autres personnes pullent le repo.

### Option B — Passer à Vercel Pro

Vercel Pro (~$20/mo) lève la restriction author sur les builds. Le workflow
devient "push → auto-deploy" standard. Recommandé si vous collaborez avec
plusieurs contributeurs.

### Option C — Héberger le frontend ailleurs

Netlify, Cloudflare Pages et GitHub Pages n'ont pas cette contrainte et
offrent un niveau gratuit comparable. Vous pouvez garder Vercel en secours
et pointer votre DNS vers Netlify le temps d'une migration.

---

## Ce qui n'est **pas** poussé via GitHub

Pour des raisons de sécurité, ces éléments **ne partent PAS** vers le repo :

| Fichier | Raison | Où le stocker |
|---|---|---|
| `backend/.env` | contient `MONGO_URL`, `EMERGENT_LLM_KEY` | Render → Environment variables |
| `frontend/.env` | contient `REACT_APP_BACKEND_URL` | Vercel → Environment variables |
| Cabinet Vault secrets (TG/X/Helius/Resend keys) | chiffrés AES-256-GCM dans MongoDB | MongoDB production (via l'UI Cabinet Vault) |
| Mnemonic BIP39 (24 mots) | sécurité physique | **Papier**, offline, coffre |

Si vous recréez le backend depuis zéro (nouveau Render service), vous
devrez re-renseigner les env vars ET re-saisir les secrets dans le vault
(ou importer un backup chiffré).

---

## Troubleshooting

| Symptôme | Cause probable | Fix |
|---|---|---|
| "Save to GitHub" grisé | Intégration GitHub non liée | Emergent → Settings → Integrations → GitHub → Connect |
| Push OK mais Vercel muet | Deploy Hook oublié | Trigger le hook manuellement |
| Vercel build fail avec `Git author…` | Pas de Deploy Hook configuré | Créer le hook dans Vercel Settings |
| Vercel build OK mais site prod inchangé | Cache CDN Vercel | Hard refresh `Cmd+Shift+R` ou wait 5 min |
| Render deploy fail | Dépendance Python ajoutée sans `pip freeze` | Voir `/app/backend/requirements.txt`, relancer pip freeze |
| 404 sur `/admin` en prod | SPA rewrite manquant | Check `frontend/vercel.json` rewrites (doit contenir `/(.*)` → `/index.html`) |

---

## One-liner — tout faire en un script

```bash
#!/bin/bash
# post-session.sh — à exécuter après chaque "Save to GitHub"

VERCEL_HOOK="https://api.vercel.com/v1/integrations/deploy/prj_xxx/yyy"
RENDER_URL="https://VOTRE-BACKEND.onrender.com"
FRONT_URL="https://www.deepotus.xyz"

echo "→ Triggering Vercel Deploy Hook…"
curl -s -X POST "$VERCEL_HOOK" | python3 -m json.tool

echo "→ Waiting 120s for builds to complete…"
sleep 120

echo "→ Checking front (should be 200)…"
curl -s -o /dev/null -w "  /: %{http_code}\n  /admin: %{http_code}\n" "$FRONT_URL/" "$FRONT_URL/admin"

echo "→ Checking backend API (should be 200)…"
curl -s -o /dev/null -w "  /api/: %{http_code}\n" "$RENDER_URL/api/"

echo "✅ Done — open $FRONT_URL to verify manually"
```

Sauvegardez ce script, ajoutez `chmod +x post-session.sh`, et
lancez-le à chaque fin de session Emergent.
