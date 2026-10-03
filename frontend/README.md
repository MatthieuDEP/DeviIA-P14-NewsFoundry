# NewsFoundry Frontend

Projet Next.js avec JavaScript, App Router, CSS Modules et ESLint.

## Démarrage

Depuis le dossier `frontend/` :

```bash
npm install
npm run dev
```

Ouvrir `http://localhost:3000`.

## Organisation

- `src/app/page.js` : page d'accueil.
- `src/app/page.module.css` : styles locaux de la page d'accueil.
- `src/app/layout.js` : mise en page commune et métadonnées.
- `src/app/globals.css` : styles globaux.
- `public/` : fichiers statiques.

L'alias `@/*` pointe vers `src/*`. Pour les styles d'un composant, créer un fichier `*.module.css` et l'importer dans le composant.

## Vérifications

```bash
npm run lint
npm run build
```

Pour lancer la version de production après compilation :

```bash
npm run start
```

Les polices Geist du modèle initial utilisent `next/font/google` : la compilation nécessite un accès réseau à Google Fonts.

Documentation : [Next.js](https://nextjs.org/docs).
