# Audit MLOps du projet churn


## Défaut 1 - CI/CD fichiers ci.yml 

**Localisation** : .github/workflows/ci.yml (lignes 3 à 5)

**Description** : il n'y a pas d'identification de branches donc n'importe quel push distant déclenchera le github action. 

**Criticité** : HAUTE

**Justification** : Si n'importe quelle personne peut push sur le main, le CI/CD peut être déclenché et potentiellement mettre en production du code qui n'est pas testé.

## Défaut 2 - API Secret token

**Localisation** : app.py (ligne 12)

**Description** : Un secret (API_TOKEN = "churn-demo-token") est en dur dans le code. 

**Criticité** : HAUTE

**Justification** : Le codage en dur d'un secret expose le système entier si le dépôt est compromis ou public.

## Défaut 3 - Test des prédictions

**Localisation** : tests/test_api.py (ligne 47-48)

**Description** : Dans test_predict_valid_input, l'assertion se contente de vérifier assert response.status_code == 200 et assert "prediction" in response.json(). 

**Criticité** : BASSE

**Justification** : Le test ne vérifie pas la qualité de la prédiction.

## Défaut 4 - Absence de test sur les cas critiques 

**Localisation** : tests/test_api.py (lignes 18-22)

**Description** : Le fichier de test vérifie que le endpoint /health fonctionne en cas normal, mais il n'y a aucun test d'échec. Exemple : il ne test pas ce qui se passe si le chargement du modèle échoue.

**Criticité** : MOYENNE

**Justification** : Le système pourrait échouer sans que les tests ne le détectent.

## Défaut 5 - Fuite de données dans l'API

**Localisation** : app.py (ligne 85)

**Description** : Dans le bloc d'erreur (except exception as e :), l'api va renvoyer l'erreur technique brute directement à l'utilisateur (raise HTTPException (status code = 500, detail=str(e))). 

**Criticité** : MOYENNE

**Justification** : Renvoyer des traces brutes à l'utilisateur est une vulnérabilité de sécurité, cela peut révéler des informations sensibles sur le serveur comme des mots de passe, des chemins d'accès, des fichiers importants, etc.

## Défaut 6 - Execution de l'entraînement dans la CI

**Localisation** : .github/workflows/ci.yml (étape "Run training")

**Description** : Le workflow exécute l'entraînement du modèle, ce qui est très long (plusieurs minutes).

**Criticité** : HAUTE

**Justification** : L'entraînement du modèle devrait être exécuté dans le CD et non dans le CI. Le CI devrait seulement vérifier que le code est valide.

## Défaut 7 - Environnement

**Localisation** : requirements.txt

**Description** : Les versions des bibliothèques ne sont pas fixées. 

**Criticité** : BASSE

**Justification** : Risque que le code ne fonctionne plus si une bibliothèque fait une mise à jour incompatible.

## Défaut 8 - Manque de documentation

**Localisation** : README.md

**Description** : Le README.md est très sommaire et ne contient pas d'instructions claires sur la manière d'installer et d'exécuter le projet.

**Criticité** : BASSE

**Justification** : Le projet est simple, mais une meilleure documentation améliorerait l'expérience utilisateur.

## Défaut 9 - Confidentialité 

**Localisation** : .gitignore

**Description** : Le fichier .gitignore n'ignore pas le dossier data donc il va envoyer toutes les données dans le répertoire GitHub.

**Criticité** : HAUTE

**Justification** : Cela peut exposer des données sensibles comme des informations personnelles.