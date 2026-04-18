# Multimodal AI Pipeline — Django

Système d'analyse de fichiers multimodaux par intelligence artificielle. Uploadez un document, une image ou un fichier de données, posez une question, et obtenez une réponse générée par un modèle IA local.

---

## Prérequis

Avant de démarrer, vous avez besoin de :

- Python 3.10 ou supérieur
- pip (gestionnaire de paquets Python)
- Ollama installé sur votre machine — https://ollama.com/download

---

## Installation en 5 étapes

**Étape 1 — Cloner le projet**

https://github.com/marmouraaa/multimodal-django.git

**Étape 2 — Créer l'environnement virtuel**

```bash
python -m venv venv
```

**Étape 3 — Activer l'environnement virtuel**

Sur Windows :
```bash
venv\Scripts\activate
```

Sur Linux / Mac :
```bash
source venv/bin/activate
```

**Étape 4 — Installer les dépendances**

```bash
pip install -r requirements.txt
```

**Étape 5 — Appliquer les migrations de base de données**

```bash
python manage.py migrate
```

---

## Télécharger les modèles IA

Le projet utilise Ollama pour faire tourner les modèles en local. Téléchargez les 4 modèles nécessaires :

```bash
ollama pull llama3.2:latest
ollama pull llava:latest
ollama pull qwen3:8b
ollama pull mistral:7b
```

> Le téléchargement peut prendre plusieurs minutes selon votre connexion. Les modèles occupent environ 15 Go au total.

---

## Lancer le projet

**Terminal 1 — Démarrer Ollama**

```bash
ollama serve
```

Laissez ce terminal ouvert pendant toute l'utilisation.

**Terminal 2 — Démarrer le serveur Django**

```bash
python manage.py runserver
```

**Accéder à l'application**

Ouvrez votre navigateur et allez sur :

```
http://127.0.0.1:8000
```

---

## Utilisation

### 1. Uploader un fichier

Sur la page d'accueil, glissez-déposez votre fichier dans la zone prévue, ou cliquez dessus pour ouvrir le sélecteur de fichiers. Cliquez ensuite sur **Analyser le fichier**.

Formats acceptés :

| Type | Extensions |
|------|-----------|
| Documents | PDF, DOCX, DOC, TXT |
| Images | JPG, JPEG, PNG, GIF, BMP, WebP |
| Données structurées | CSV, JSON, XLSX, XLS |

Taille maximale : 10 Mo par fichier.

### 2. Poser une question

Une fois le fichier traité, vous arrivez sur la page de question. Tapez votre question dans le champ prévu, ou cliquez sur une des suggestions proposées selon le type de fichier.

Exemples de questions selon le type :

- **Document** — "Résume ce document", "Quels sont les points clés ?", "Quelle est la durée du contrat ?"
- **Image** — "Que vois-tu sur cette image ?", "Y a-t-il du texte ?", "Décris cette image en détail"
- **Données** — "Combien de lignes contient le fichier ?", "Quel est le total ?", "Quelles sont les statistiques principales ?"

### 3. Lire la réponse

La réponse s'affiche avec un **score de confiance** entre 0 et 100% :

- **Vert (≥ 80%)** — Réponse fiable
- **Orange (40–79%)** — Réponse à vérifier
- **Rouge (< 40%)** — Réponse peu fiable, reformulez votre question

Si la confiance est trop faible, le système active automatiquement un **fallback** qui essaie d'autres stratégies pour améliorer la réponse.

### 4. Historique

Toutes vos questions précédentes sur un fichier sont affichées en bas de la page. Vous pouvez cliquer sur une ancienne question pour revoir sa réponse complète.

---

## Fichiers récents

La page d'accueil affiche les 10 derniers fichiers uploadés. Cliquez sur l'un d'eux pour poser de nouvelles questions sans re-uploader.

---

## Lancer les tests

Pour vérifier que tout fonctionne correctement :

Tests rapides (sans Ollama, environ 3 secondes) :
```bash
pytest tests/ -v -m "not ollama"
```

Tests complets avec les modèles IA (environ 2 minutes, Ollama doit tourner) :
```bash
pytest tests/ -v -m ollama
```

Tous les tests d'un coup :
```bash
pytest tests/ -v
```

---

## Résolution des problèmes fréquents

**Le modèle ne répond pas**
Vérifiez qu'Ollama tourne bien dans un terminal avec `ollama serve`. Vérifiez aussi que les modèles sont téléchargés avec `ollama list`.

**L'image retourne "Aucune image fournie"**
Vérifiez que le fichier est bien un format image supporté (JPG, PNG, etc.) et que sa taille ne dépasse pas 10 Mo.

**Le CSV retourne des données vides**
Vérifiez que le fichier CSV utilise une virgule ou un point-virgule comme séparateur et qu'il contient au moins une ligne d'en-tête.

**La page d'upload ouvre le sélecteur deux fois**
Ce bug est corrigé dans la dernière version. Assurez-vous d'utiliser le fichier home.html mis à jour.

**Erreur "INSTALLED_APPS not configured"**
Vérifiez que pytest.ini est bien à la racine du projet et que conftest.py est également à la racine.

---

## Architecture résumée

```
Fichier uploadé
      ↓
Détection automatique du type (document / image / données)
      ↓
Extraction du contenu (texte, statistiques, description)
      ↓
Routage vers le bon modèle IA
      ↓
Réponse avec score de confiance
      ↓
Fallback automatique si confiance insuffisante
```

---

## Liens utiles

- Documentation Ollama — https://github.com/ollama/ollama
- Transformers (Hugging Face) — https://huggingface.co/docs/transformers
- LlamaIndex — https://docs.llamaindex.ai
- Pydantic — https://docs.pydantic.dev
- Django — https://docs.djangoproject.com
- pytest-django — https://pytest-django.readthedocs.io

---

*Projet académique — Multimodal AI with Django — 2025/2026*