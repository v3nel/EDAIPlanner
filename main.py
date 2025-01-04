import requests
import json
import base64
import sqlite3
import uuid


# Configuration
ECOLE_DIRECTE_URL = "https://api.ecoledirecte.com/v3"

# Fonction pour récupérer les informations de l'utilisateur
def store_user_data(username, eleve_id, token, cn, cv, uuid):
    conn = sqlite3.connect("user_data.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS user_data (
        id INTEGER PRIMARY KEY,
        username TEXT,
        eleve_id TEXT,
        token TEXT,
        cn TEXT,
        cv TEXT,
        uuid TEXT
    )""")

    # Vérifier si l'utilisateur existe déjà
    c.execute("SELECT * FROM user_data WHERE username = ?", (username,))
    user = c.fetchone()

    if user:
        # Mettre à jour les informations de l'utilisateur
        c.execute("""UPDATE user_data SET eleve_id = ?, token = ?, cn = ?, cv = ?, uuid = ?
                     WHERE username = ?""", (eleve_id, token, cn, cv, uuid, username))
    else:
        # Insérer un nouvel utilisateur
        c.execute("INSERT INTO user_data (username, eleve_id, token, cn, cv, uuid) VALUES (?, ?, ?, ?, ?, ?)",
                  (username, eleve_id, token, cn, cv, uuid))

    conn.commit()
    conn.close()


# Fonction pour récupérer les devoirs de l'API EcoleDirecte
def get_ecole_directe_homework():
    # Étape 1 : Authentification
    USERNAME = input("Nom d'utilisateur : ")
    PASSWORD = input("Mot de passe : ")
    useruid = str(uuid.uuid4())
    print (useruid)
    login_url = f"{ECOLE_DIRECTE_URL}/login.awp"
    login_data = {
        "identifiant":USERNAME,
        "motdepasse":PASSWORD,
        "sesouvenirdemoi": True,
        "isRelogin": False,
        "uuid": useruid
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(login_url, data={"data":json.dumps(login_data)}, headers=headers)

    # Vérifiez le statut HTTP
    if response.json().get("code") == 250:
        doubleauth_urlget = f"{ECOLE_DIRECTE_URL}/connexion/doubleauth.awp?verbe=get"
        doubleauth_data = {}
        doubleauth_headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Token": response.json().get("token")
        }
        form = requests.post(doubleauth_urlget, data={"data":json.dumps(doubleauth_data)}, headers=doubleauth_headers)
        print(form.json())

        question = base64.b64decode(form.json().get("data").get("question")).decode("utf-8")
        propositions = form.json().get("data").get("propositions")

        decoded_props = {}
        count = 1
        for prop in propositions:
            decoded_props[count] = base64.b64decode(prop).decode("utf-8")
            count += 1

        print(f"Question : {question}")
        print(f"Propositions : ")
        for prop in decoded_props:
            print(f"{prop}" + " : " + f"{decoded_props[prop]}")

        answer = int(input("Réponse : "))

        doubleauth_url = f"{ECOLE_DIRECTE_URL}/connexion/doubleauth.awp?verbe=post"
        doubleauth_data = {"choix":base64.b64encode(decoded_props[answer].encode("utf-8")).decode("utf-8")}

        authobject = requests.post(doubleauth_url, data={"data":json.dumps(doubleauth_data)}, headers=doubleauth_headers)
        print(authobject.json())

        cn = authobject.json().get("data").get("cn")
        cv = authobject.json().get("data").get("cv")

        if authobject.json().get("code") != 200:
            print(f"Erreur HTTP {response.status_code} : {response.text}")
            return []

        login_data = {
            "identifiant":USERNAME,
            "motdepasse":PASSWORD,
            "sesouvenirdemoi": True,
            "isRelogin": False,
            "uuid": useruid,
            "fa": [
                {
                    "cn":cn ,
                    "cv": cv
                }
            ]
        }
        response = requests.post(login_url, data={"data":json.dumps(login_data)}, headers=headers)
        store_user_data(USERNAME, response.json().get("data").get("accounts")[0].get("id"),
                        response.json().get("token"), cn, cv, useruid)


    elif response.json().get("code") != 200 or response.json().get("code") != 250:
        print(f"Erreur HTTP {response.status_code} : {response.text}")
    # Parsez la réponse JSON
    try:
        login_response = response.json()
    except json.JSONDecodeError:
        print(f"Erreur de parsing JSON : {response.text}")
        return []

    # Vérifiez le code de réponse de l'API
    if "code" not in login_response or login_response.get("code") != 200 and login_response.get("code") != 250:
        print(f"Réponse inattendue : {login_response}")
        return []

    # Récupérer le token et l'ID élève
    token = login_response.get("token")
    accounts = login_response.get("data", {}).get("accounts", [])
    if not accounts:
        print("Erreur : Aucun compte trouvé dans la réponse.")
        return []

    eleve_id = accounts[0].get("id")
    if not eleve_id:
        print("Erreur : ID élève introuvable.")
        return []

    # Étape 2 : Récupération des devoirs
    homework_url = f"{ECOLE_DIRECTE_URL}/eleves/{eleve_id}/cahierdetexte.awp?verbe=get"
    headers["X-Token"] = token
    response = requests.post(homework_url, data={"data": "{}"}, headers=headers)

    # Vérifiez le statut HTTP
    if response.status_code != 200:
        print(f"Erreur HTTP {response.status_code} : {response.text}")
        return []

    # Parsez la réponse JSON pour les devoirs
    try:
        homework_response = response.json()
    except json.JSONDecodeError:
        print(f"Erreur de parsing JSON : {response.text}")
        return []

    if "code" not in homework_response or homework_response.get("code") != 200:
        print(f"Erreur lors de la récupération des devoirs : {homework_response.get('message', 'Réponse inconnue')}")
        return []

    # Extraction des devoirs
    homework_list = []
    for day in homework_response["data"]["days"]:
        for homework in day["matieres"]:
            homework_list.append({
                "id": homework["idDevoir"],
                "matiere": homework["matiere"],
                "contenu": homework["aFaire"]["contenu"],
                "date": day["date"]
            })

    return homework_list

# Exemple d'utilisation
if __name__ == "__main__":
    homework = get_ecole_directe_homework()
    for hw in homework:
        print(f"ID: {hw['id']}, Matière: {hw['matiere']}, Date: {hw['date']}")
        print(f"Contenu: {hw['contenu']}\n")