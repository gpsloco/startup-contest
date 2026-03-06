# 🚀 StartUp Contest – Setup Anleitung

Dieses Projekt besteht aus einer statischen Website (GitHub Pages) und einem Python-Script zum Zusammenführen von Google Slides Präsentationen.

---

## Projektstruktur

```
startup-contest/
├── index.html          → Landing Page
├── register.html       → Bewerbungsformular
├── css/
│   └── style.css       → Alle Styles
└── scripts/
    ├── appsscript.js   → Google Apps Script (in script.google.com einfügen)
    └── merge_slides.py → Python-Script zum Slides-Merger
```

---

## Schritt 1 – Google Sheets einrichten

1. Gehe zu [sheets.google.com](https://sheets.google.com) und erstelle ein neues Sheet
2. Nenne es z.B. **"StartUp Contest Bewerbungen"**
3. Notiere die **Spreadsheet-ID** aus der URL:
   `https://docs.google.com/spreadsheets/d/**DIESE_ID**/edit`

---

## Schritt 2 – Google Apps Script deployen

1. Gehe zu [script.google.com](https://script.google.com) → Neues Projekt
2. Kopiere den Inhalt von `scripts/appsscript.js` in den Editor
3. Ersetze `DEINE_SPREADSHEET_ID_HIER` mit deiner echten ID
4. Klicke **Bereitstellen → Neue Bereitstellung**
   - Typ: **Web-App**
   - Ausführen als: **Ich**
   - Zugriff: **Jeder**
5. Kopiere die **Web-App-URL**

---

## Schritt 3 – Website konfigurieren

Öffne `register.html` und ersetze in Zeile ~90:

```javascript
const APPS_SCRIPT_URL = 'HIER_DEINE_WEB_APP_URL_EINFÜGEN';
```

---

## Schritt 4 – GitHub Repository erstellen & deployen

```bash
# Im Terminal (Mac):
cd /pfad/zu/startup-contest

git init
git add .
git commit -m "Initial commit: StartUp Contest Website"

# GitHub Repo erstellen (gh CLI):
gh repo create startup-contest --public --source=. --push

# GitHub Pages aktivieren:
gh api repos/:owner/startup-contest/pages \
  --method POST \
  --field source[branch]=main \
  --field source[path]=/
```

Deine Website ist dann live unter:
`https://DEIN-USERNAME.github.io/startup-contest`

---

## Schritt 5 – Google API für Slides-Merger einrichten

1. Gehe zu [console.cloud.google.com](https://console.cloud.google.com)
2. Neues Projekt erstellen: **"startup-contest"**
3. APIs aktivieren (Bibliothek):
   - **Google Slides API**
   - **Google Sheets API**
   - **Google Drive API**
4. Anmeldedaten → **OAuth 2.0-Client-ID** → Desktop-Anwendung
5. JSON herunterladen → speichern als `credentials.json` im `scripts/` Ordner

---

## Schritt 6 – Python-Abhängigkeiten installieren

```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

---

## Schritt 7 – Merge-Script verwenden

1. Setze in Google Sheets den **Status** der gewünschten Bewerber auf `Finalist`
2. Öffne `scripts/merge_slides.py` und ersetze `DEINE_SPREADSHEET_ID_HIER`
3. Führe das Script aus:

```bash
cd scripts
python merge_slides.py
```

Das Script:
- Fragt beim ersten Start nach Google-Authentifizierung (einmalig im Browser)
- Zeigt alle Finalisten zur Bestätigung
- Merged die Präsentationen und gibt den Link zur Master-Präsentation aus

---

## Workflow für den Wettbewerb

| Schritt | Was passiert |
|---------|-------------|
| StartUp meldet sich an | Formular ausfüllen → landet automatisch in Google Sheets |
| Du prüfst Bewerbungen | Im Sheet Status auf `Finalist` setzen |
| Merge starten | `python merge_slides.py` ausführen |
| Master-Präsentation | Automatisch in deinem Google Drive erstellt |

---

## Kontakt

Fragen: gpsloco@googlemail.com
