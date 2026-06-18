Identification des défauts liés au MLops


## Défaut 1 - CI/CD fichiers ci.yml 

**Localisation** : .github/workflows/ci.yml

**Description** : il n'y a pas d'identification de branches donc n'importe quel push distant déclenchera le github action. (ligne 3 à 5)

**Niveau de criticité** : haute (si n'importe quelle personne peut push sur le main, le CI/CD peut être déclenché et potentiellement mettre en production du code qui n'est pas testé.)

## Défaut 2 - API Secret token

**Localisation** : app.py 

**Description** : Un secret (API_TOKEN = "churn-demo-token") est en dur dans le code. 

**Niveau de criticité** : Haute (Le codage en dur d'un secret expose le système entier si le dépôt est compromis ou public.)

# Défaut 3 - Test des prédictions

**Localisation** : tests/test_api.py (ligne 47-48)

**Description** : Dans test_predict_valid_input, l'assertion se contente de vérifier assert response.status_code == 200 et assert "prediction" in response.json(). 

**Niveau de criticité** : Basse (Le test ne vérifie pas la qualité de la prédiction.)

# Défauts 4 - Absence de test sur les cas critiques 

**Localisation** : tests/test_api.py (lignes 18-22)

**Description** : Le fichier de test vérifie que le endpoint /health fonctionne en cas normal, mais il n'y a aucun test d'échec. Exemple : il ne test pas ce qui se passe si le chargement du modèle échoue.

**Niveau de criticité** : Moyenne (Le système pourrait échouer sans que les tests ne le détectent.)

# Défaut 5 - Fuite de données dans l'API

**Localisation** : app.py (ligne 85)

**Description** : Dans le bloc d'erreur (except exception as e :), l'api va renvoyer l'erreur technique brute directement à l'utilisateur (raise HTTPException (status code = 500, detail=str(e))). 

**Niveau de criticité** : Moyenne (renvoyer des traces brutes à l'utilisateur est une vulnérabilité de sécurité, cela peut évéler des inforamtions senseibles sur le serveur comme des mots de passes, des chemins d'accès, des fichiers importants, etc.)

# Défaut 6 - Execution de l'entraînement dans la CI

**Localisation** : .github/workflows/ci.yml

**Description** : Le workflow exécute l'entraînement du modèle, ce qui est très long (plusieurs minutes).

**Niveau de criticité** : Haute (L'entraînement du modèle devrait être exécuté dans le CD et non dans le CI. Le CI devrait seulement vérifier que le code est valide.)