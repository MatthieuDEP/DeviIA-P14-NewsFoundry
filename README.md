# NewsFoundry

## Besoins fonctionnels

- L'utilisateur peut se connecter.
- L’utilisateur peut voir la liste de ses discussions passées.
- L’utilisateur peut démarrer une nouvelle discussion ou reprendre une ancienne discussion.
- Un utilisateur n’est pas autorisé à accéder aux discussions d’un autre utilisateur.
- Le LLM répond aux messages envoyés par l’utilisateur.
- L'utilisateur peut faire générer une revue de presse à partir d'une discussion.
- L'application doit afficher des messages d'erreur à l'utilisateur final en cas d'erreur.

## Prérequis

- Docker
- Python 3.13
- uv
- Node.js 22.19

## Installation

1. Cloner le repository
2. Démarrer le backend aved les instructions du fichier `backend/README.md`
3. Installer et démarrer le frontend depuis le dossier `frontend/` :

```bash
npm install
cp .env.example .env.local
npm run dev
```

Le frontend est accessible sur `http://localhost:3000`. Voir `frontend/README.md` pour plus de détails.

La connexion est disponible sur `/connexion` avec `test@test.com` et le mot de passe `test`. Le JWT est enregistré dans le local storage. Configurer `JWT_SECRET_KEY` et `CORS_ORIGINS` dans le backend, et `NEXT_PUBLIC_API_URL` dans le frontend, comme indiqué dans leurs README.

## Choix technologiques

### Frontend

**Next.js**, avec JavaScript, App Router, CSS Modules et ESLint.

### Backend

- **Python** pour bénéficier de son écosystème de librairies IA
- **FastAPI** pour le développement de l'API
- Connection avec des **JWT**
- **SQLModel** comme ORM : fait pour bien marcher avec FastAPI.
  - Branché à une base de données **PostgreSQL**
- **PydanticAI** comme client qui s'intégrera aussi bien avec les autres outils de la stack backend
- Attention à la **sécurité des données**. On ne veut pas qu’un utilisateur puisse accéder aux chats d’un autre utilisateur ou les modifier.
  - Le produit aura rapidement beaucoup d’utilisateurs professionnels il est donc crucial de garantir le fonctionnement correct de cette fonctionnalité par l'**implémentation de tests automatisés qui s'exécutent par une Github Action**.
- Pour les sources de news, on utilisera l’API [**WorldNewsAPI**](https://worldnewsapi.com/).
- Pour déployer on mettra le frontend sur **Vercel** et le backend sur **Railway**.

### Documentation

Une documentation claire devra être rédigée et ajoutée dans un dossier `docs/`.

Elle devra inclure des suggestions d'amélioration concernant la qualité et la performance de la partie IA du système. Chaque recommandation doit être illustrée par une une métrique ou un exemple, une proposition d’implémentation réalisable, ainsi qu'un objectif mesurable.


Par ailleurs, pour faciliter la maintenance du projet à long terme, le code du projet devra être clair et bien structuré, accompagné de commentaires qui expliquent les sections de code complexes.

### Deploiement

Les étapes et réglages sont décrits dans le [guide de déploiement](docs/deploiement.md). Les URL publiques y seront renseignées après le premier déploiement.

#### Frontend

Déployer le frontend sur [Vercel](https://vercel.com/dashboard), avec `frontend` comme **Root Directory** et `main` comme branche de production.

#### Backend

Déployer le backend sur [Railway](https://railway.com/dashboard).

Configurer `/backend` comme **Root Directory** et suivre la branche `main`. Railway utilise le Dockerfile de ce dossier.

Créer PostgreSQL dans le même projet Railway et ajouter `DATABASE_URL` aux variables du backend comme référence vers le service PostgreSQL. Générer ensuite un domaine public pour le backend dans **Networking → Public Networking**.

Les intégrations GitHub de Vercel et Railway doivent déclencher les déploiements à chaque push sur `main`.
