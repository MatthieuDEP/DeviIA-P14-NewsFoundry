# Discussions avec Mistral

## Utilisation

Après connexion, écrire un premier message ou sélectionner « Nouvelle discussion ». La barre latérale affiche les discussions personnelles, triées par dernière activité. Cliquer sur une discussion recharge son historique. L'adresse `/?chat=<id>` retrouve la discussion après rechargement.

Pendant la génération, un indicateur d'attente s'affiche. En cas d'erreur, la saisie reste disponible. Un échange utilisateur/assistant est enregistré après une réponse réussie ; un appel IA échoué ne laisse pas de message incomplet en base.

## Configuration

Ajouter dans `backend/.env` et dans les variables Railway :

```text
MISTRAL_API_KEY=<clé privée>
MISTRAL_MODEL=ministral-8b-latest
```

La clé reste exclusivement dans le backend. La variable du modèle contient son nom sans le préfixe `mistral:` utilisé par PydanticAI. Redémarrer le backend après changement des variables.

Le modèle par défaut est [Ministral 3 8B](https://docs.mistral.ai/models/ministral-3-8b-25-12). Lors de la vérification, l'API identifiait l'alias `ministral-8b-latest` comme `ministral-8b-2512` et un appel réel avec PydanticAI a répondu correctement. Pour figer cette version, utiliser `MISTRAL_MODEL=ministral-8b-2512`.

## Structure et choix techniques

- `models.py` : `Chat`, propriétaire, titre, dates, historique JSON et compteur de révision.
- `chat_agent.py` : agent PydanticAI Mistral, prompt et conversion des messages visibles.
- `chats.py` : routes, contrôle d'accès et sauvegarde.
- `frontend/src/lib/chats.js` : appels authentifiés avec le JWT existant.
- `ChatWorkspace.jsx` : historique, sélection et formulaire.
- `MessageBubble.jsx` : messages et Markdown, sans interprétation du HTML du modèle.

Le JSON conserve l'historique PydanticAI complet : prompt système, messages et métadonnées. `ModelMessagesTypeAdapter` sérialise et reconstruit cet historique. Le navigateur reçoit uniquement les messages visibles utilisateur/assistant et leurs dates.

Chaque lecture ou écriture SQL filtre aussi le propriétaire. Une discussion absente ou appartenant à quelqu'un d'autre retourne le même `404`. Le propriétaire est issu du JWT, jamais du body du client.

Le compteur `revision` empêche une requête concurrente d'écraser un échange enregistré entre la lecture et la sauvegarde. Un conflit retourne `409` et le frontend recharge l'historique sans renvoi automatique au LLM. La connexion SQL est libérée pendant l'attente réseau. La liste latérale charge les métadonnées seules, sans tous les historiques JSON. Les réponses privées utilisent `Cache-Control: no-store`.

## Prompt

NewsFoundry répond en français, de façon concise et factuelle, en tenant compte de la discussion. Le prompt demande de clarifier les ambiguïtés et interdit les sources et citations inventées.

Cette étape ne fournit pas encore de recherche d'actualités : le modèle doit signaler les informations récentes qu'il ne peut pas vérifier. Cette règle sera adaptée lors de l'intégration de sources d'actualités.

## API

Toutes les routes exigent `Authorization: Bearer <JWT>`.

| Route | Résultat |
| --- | --- |
| `POST /chats` | Crée une discussion personnelle et retourne son `id` |
| `GET /chats` | Liste uniquement les discussions de l'utilisateur |
| `GET /chats/{id}` | Retourne les messages de sa discussion |
| `POST /chats/{id}/messages` | Reçoit `{"content":"Votre message"}` et retourne `reply` ainsi que l'historique sauvegardé |

Le premier message réussi fournit un titre limité à 80 caractères. Un message est limité à 4000 caractères, une réponse du modèle à 2048 tokens. La génération est interrompue après 50 secondes.

| Statut | Situation |
| --- | --- |
| `401` | Session absente, invalide ou expirée |
| `404` | Discussion absente ou non autorisée |
| `409` | Modification concurrente |
| `422` | Message vide, trop long ou identifiant invalide |
| `429` | Limite de requêtes ou quota Mistral |
| `502` | Réponse IA inutilisable ou erreur du fournisseur |
| `503` | Configuration IA ou base indisponible |
| `504` | Délai de réponse dépassé |

Les détails internes du fournisseur ne sont pas renvoyés au navigateur. Si Mistral retourne `429`, vérifier les limites du compte dans Studio et réessayer lorsque de nouvelles requêtes sont autorisées.

## Tests et CI

```bash
cd backend
uv sync --frozen
uv run --no-sync pytest -q
```

SQLite en mémoire, `TestModel`, `FunctionModel` et `Agent.override` isolent les tests. `ALLOW_MODEL_REQUESTS=False` interdit les appels réels.

Les tests couvrent les accès autorisés, les lectures et modifications interdites sur les discussions d'autrui, la liste filtrée, la persistance JSON, la reprise du contexte, les erreurs IA et les conflits de sauvegarde. Pytest collecte aussi les tests d'authentification existants. La GitHub Action lance les tests, le lint frontend et la compilation sur les pushes et pull requests de `main`.

## Piste d'optimisation

Sur un jeu de discussions de 50 à 100 échanges, mesurer les tokens d'entrée et la latence. Une amélioration possible consiste à résumer les anciens échanges, conserver l'historique complet en base, puis transmettre le résumé et les derniers messages au modèle. Objectif à valider : réduire d'au moins 50 % les tokens d'entrée sans perte d'information essentielle dans les réponses.

## Références

- [PydanticAI : exemple de chat](https://ai.pydantic.dev/examples/chat-app/)
- [PydanticAI : historique](https://ai.pydantic.dev/message-history/)
- [PydanticAI : tests](https://ai.pydantic.dev/testing/)
- [PydanticAI : Mistral](https://ai.pydantic.dev/models/mistral/)
