simple-stock-api README

Descrizione

Simple Stock Market API è un'applicazione Flask che espone un'API REST per dati di borsa in tempo reale, prezzi storici e gestione portafoglio. Include autenticazione tramite JWT e due livelli di utente:

Basic User: accesso limitato a 3 titoli, 100 richieste di quote al giorno.

Pro User: accesso completo, 5+ anni di storico, 1000 richieste di quote al giorno.

Funzionalità principali

Autenticazione e registrazione via token JWT

Endpoint API per:

registrazione, login, profilo

liste e quote azioni

storico prezzi

gestione portafoglio (buy/sell, transazioni)

Client React minimale per interagire con l'API

Struttura del repository

stock-market_project/
├─ backend/            # Codice Flask + database
├─ frontend/           # Codice React + build Gh-Pages
└─ README.md           # Questo file

Credenziali di esempio

Basic User: user@example.com / user

Pro User: pro@example.com / prouser

Come eseguire l'app in locale

Backend

Entra nella cartella backend/

Crea un virtualenv e installa le dipendenze:

python3 -m venv venv
source venv/bin/activate   # su Windows: venv\Scripts\activate
pip install -r requirements.txt

Avvia l'app:

flask run --host=0.0.0.0 --port=5500

Verifica l'health check: curl http://localhost:5500/health

Frontend

Entra in frontend/

Avvia in modalità sviluppo:

npm install
npm start

Oppure visita la versione statica (GitHub Pages):
https://github.com/edoardo-nicoli03/stock-market_project
Link di deployment, è sufficiente il link al Frontend :

Frontend (GitHub Pages): https://edoardo-nicoli03.github.io/stock-market_project/

Backend (Railway): https://stock-marketproject-production.up.railway.app/