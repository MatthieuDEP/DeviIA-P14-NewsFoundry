# NewsFoundry Backend

1. Copier le fichier `.env.example` dans `.env`


2. Installer les dépendances:
```bash
uv sync
```

2. Démarrer la base de données:
```bash
docker run \
  --name newsfoundry_db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=newsfoundry \
  -p 127.0.0.1:5434:5432 \
  postgres:17
```

PostgreSQL est accessible sur `localhost:5434`. Le port interne du conteneur reste `5432`.

3. Lancer le backend:
```bash
uv run --env-file .env src/main.py
```

## Connexion

L'utilisateur de test est `test@test.com`, avec le mot de passe `test`.

Ajouter dans `.env` :

```text
JWT_SECRET_KEY=<clé aléatoire>
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Générer la clé avec `python3 -c "import secrets; print(secrets.token_hex(32))"`. Elle doit rester stable entre les redémarrages et ne doit pas être commitée. Une clé locale a déjà été générée pour ce poste.

`POST /login` reçoit un JSON avec `email` et `password` et retourne `access_token` et `token_type`. Le JWT est signé en HS256 et expire après une heure. `GET /me` vérifie le token transmis dans `Authorization: Bearer <token>` et retourne uniquement l'identifiant et l'email.

| Statut | Signification |
| --- | --- |
| `401` | Identifiants incorrects ou session invalide/expirée |
| `422` | Champs de connexion invalides |
| `503` | Base indisponible ou clé JWT non configurée |

Les hashes bcrypt sont conservés dans la base, sans journalisation SQL des paramètres. Les anciennes valeurs binaires du compte de test sont normalisées en texte au démarrage, sans changer son mot de passe.

## Tests

```bash
uv sync --frozen
uv run --no-sync pytest -q
```

Les tests utilisent SQLite en mémoire et couvrent l'authentification, les discussions et leurs autorisations. `TestModel` et `FunctionModel` remplacent Mistral, sans appels facturés. La GitHub Action `.github/workflows/ci.yml` exécute les tests, le lint et la compilation frontend.

Sur Railway, ajouter `JWT_SECRET_KEY` avec une clé propre à la production et `CORS_ORIGINS` avec l'origine exacte du frontend Vercel. La variable `DATABASE_URL` reste configurée comme auparavant.

## Chat Mistral

Configurer `MISTRAL_API_KEY` dans `.env`, puis redémarrer le backend. Le modèle par défaut est `ministral-8b-latest`, configurable via `MISTRAL_MODEL`. La table `Chat` est créée au démarrage sans supprimer les données existantes.

Les routes `/chats` et `/chats/{id}/messages` vérifient le JWT et le propriétaire de la discussion. Voir le [guide du chat](../docs/chat.md) pour le prompt, les routes, les erreurs et les tests.
