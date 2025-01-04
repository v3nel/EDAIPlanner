# ED AI Planer
## The new way to plan your homework

Connect your Google account and your Ecole Directe account to start syncronizing your homework with your calendar.
Let AI look at what you have and it will automatically start previsionning how much time each one of your homework will take and will planify this in your Google Calendar

## Startup :

### Set the OpenAI token

To get it to work, clone this repo on a folder on your computer or on a VPS with Python 3.12 installed, create a .env file and insert your OpenAI token like this :

```dotenv
OPEN_AI_TOKEN=sk-proj-xxxxx...
```

### Then create a virtual environement :

Sous MacOS/Linux :

```bash
python3 -m venv env
```

Sous Windows :

````powershell
python -m venv env
````

### Activer l'environnement virtuel :

Sous Unix/macOS :
````bash
source env/bin/activate
````
Sous Windows :
````powershell
.\env\Scripts\activate
````

### Installer les dépendances depuis requirements.txt :

````pycon
pip install -r requirements.txt
````