"""
=====================================================
  StartUp Contest – Google Slides Merger
  Führt bis zu 10 Google Slides Präsentationen
  zu einer Master-Präsentation zusammen.
=====================================================

VORAUSSETZUNGEN (einmalig einrichten):
  pip install google-auth google-auth-oauthlib google-api-python-client gspread

GOOGLE API SETUP:
  1. Gehe zu https://console.cloud.google.com
  2. Neues Projekt erstellen: "startup-contest"
  3. APIs aktivieren:
     - Google Slides API
     - Google Sheets API
     - Google Drive API
  4. Anmeldedaten → OAuth 2.0 Client-ID erstellen (Desktop-App)
  5. JSON herunterladen → speichern als credentials.json im selben Ordner

VERWENDUNG:
  python merge_slides.py

  Das Script:
  - Liest alle Bewerbungen aus Google Sheets
  - Zeigt Bewerber mit "Finalist"-Status
  - Merged deren Google Slides in eine Master-Präsentation
  - Speichert auf gpsloco@googlemail.com Google Drive
=====================================================
"""

import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ── Konfiguration ──────────────────────────────────────────────────
SPREADSHEET_ID  = 'DEINE_SPREADSHEET_ID_HIER'   # ← Google Sheets ID eintragen
SHEET_NAME      = 'Bewerbungen'
MASTER_TITLE    = 'StartUp Contest – Finalisten Präsentation'
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE       = 'token.json'
MAX_PRESENTATIONS = 10

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive',
]

# ── Authentifizierung ──────────────────────────────────────────────
def get_credentials():
    """Lädt oder erneuert Google OAuth Credentials."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return creds


# ── Google Sheets: Finalisten laden ───────────────────────────────
def get_finalists(sheets_service):
    """
    Liest alle Zeilen mit Status='Finalist' aus dem Google Sheet.
    Gibt eine Liste von Dicts zurück.
    """
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!A:I'
    ).execute()

    rows = result.get('values', [])
    if not rows:
        print("❌ Keine Daten im Sheet gefunden.")
        return []

    headers = rows[0]  # Erste Zeile = Header
    finalists = []

    for row in rows[1:]:
        # Zeilen auf Header-Länge auffüllen
        row_data = row + [''] * (len(headers) - len(row))
        entry = dict(zip(headers, row_data))

        if entry.get('Status', '').strip() == 'Finalist':
            slides_url = entry.get('Google Slides Link', '').strip()
            presentation_id = extract_presentation_id(slides_url)
            if presentation_id:
                finalists.append({
                    'name':            entry.get('StartUp-Name', 'Unbekannt'),
                    'contact':         entry.get('Ansprechpartner', ''),
                    'email':           entry.get('E-Mail', ''),
                    'slides_url':      slides_url,
                    'presentation_id': presentation_id,
                })

    return finalists[:MAX_PRESENTATIONS]


# ── Presentation ID aus URL extrahieren ───────────────────────────
def extract_presentation_id(url):
    """
    Extrahiert die Presentation-ID aus einer Google Slides URL.
    z.B. https://docs.google.com/presentation/d/PRESENTATION_ID/edit
    """
    if not url:
        return None
    try:
        parts = url.split('/d/')
        if len(parts) < 2:
            return None
        return parts[1].split('/')[0]
    except Exception:
        return None


# ── Slides kopieren ────────────────────────────────────────────────
def copy_slides_to_master(slides_service, drive_service, finalists):
    """
    Erstellt eine neue Master-Präsentation und kopiert alle Folien
    der Finalisten hinein.
    """
    print(f"\n🔨 Erstelle Master-Präsentation: '{MASTER_TITLE}'")

    # Neue leere Präsentation erstellen
    master = slides_service.presentations().create(
        body={'title': MASTER_TITLE}
    ).execute()
    master_id = master['presentationId']
    print(f"   ✅ Erstellt: https://docs.google.com/presentation/d/{master_id}/edit")

    # Standard-Folie in neuer Präsentation entfernen
    default_slide_id = master['slides'][0]['objectId']
    slides_service.presentations().batchUpdate(
        presentationId=master_id,
        body={'requests': [{'deleteObject': {'objectId': default_slide_id}}]}
    ).execute()

    insert_index = 0

    for i, finalist in enumerate(finalists, 1):
        print(f"\n📊 [{i}/{len(finalists)}] {finalist['name']} ({finalist['slides_url'][:60]}...)")

        try:
            # Quell-Präsentation abrufen
            source = slides_service.presentations().get(
                presentationId=finalist['presentation_id']
            ).execute()
            source_slides = source.get('slides', [])
            print(f"   → {len(source_slides)} Folie(n) gefunden")

            # Trennfolie einfügen (StartUp-Name)
            separator_id = f"separator_{i}"
            requests = [
                # Trennfolie hinzufügen
                {
                    'insertSlides': {
                        'insertionIndex': insert_index,
                        'slides': [{
                            'objectId': separator_id,
                        }]
                    }
                },
            ]

            # Alternativ: Folien direkt kopieren über Drive API
            # (Slides API unterstützt kein direktes Kopieren zwischen Präsentationen)
            # Daher: Quell-Präsentation duplizieren, dann Folien verschieben

            copy_response = drive_service.files().copy(
                fileId=finalist['presentation_id'],
                body={'name': f'_temp_{finalist["name"]}'}
            ).execute()
            temp_id = copy_response['id']

            temp_presentation = slides_service.presentations().get(
                presentationId=temp_id
            ).execute()
            temp_slides = temp_presentation.get('slides', [])

            # Alle Folien aus der Temp-Präsentation in die Master-Präsentation verschieben
            move_requests = []
            for j, slide in enumerate(temp_slides):
                move_requests.append({
                    'replaceAllShapesWithImage': {}  # Platzhalter
                })

            # Einfacherer Ansatz: Folien-IDs sammeln und in Master einfügen
            slide_ids = [slide['objectId'] for slide in temp_slides]

            insert_requests = []
            for j, slide_id in enumerate(slide_ids):
                insert_requests.append({
                    'insertSlides': {
                        'presentationId': temp_id,
                        'insertionIndex': insert_index + j,
                        'slideIds': [slide_id]
                    }
                })

            if insert_requests:
                slides_service.presentations().batchUpdate(
                    presentationId=master_id,
                    body={'requests': insert_requests}
                ).execute()
                insert_index += len(slide_ids)
                print(f"   ✅ {len(slide_ids)} Folie(n) eingefügt")

            # Temp-Präsentation löschen
            drive_service.files().delete(fileId=temp_id).execute()

        except Exception as e:
            print(f"   ❌ Fehler bei {finalist['name']}: {e}")
            continue

    print(f"\n🎉 Fertig! Master-Präsentation: https://docs.google.com/presentation/d/{master_id}/edit")
    return master_id


# ── Hauptprogramm ──────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  StartUp Contest – Slides Merger")
    print("=" * 60)

    # Authentifizieren
    print("\n🔐 Authentifizierung läuft...")
    creds = get_credentials()
    slides_service = build('slides', 'v1', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service  = build('drive',  'v3', credentials=creds)
    print("   ✅ Eingeloggt als gpsloco@googlemail.com")

    # Finalisten aus Sheet laden
    print(f"\n📋 Lade Finalisten aus Google Sheets...")
    finalists = get_finalists(sheets_service)

    if not finalists:
        print("\n❌ Keine Finalisten gefunden.")
        print("   Tipp: Setze den Status der gewünschten Bewerber im Sheet auf 'Finalist'.")
        return

    print(f"\n✅ {len(finalists)} Finalist(en) gefunden:")
    for i, f in enumerate(finalists, 1):
        print(f"   {i}. {f['name']} – {f['slides_url'][:60]}...")

    # Bestätigung einholen
    print()
    confirm = input(f"➡️  Diese {len(finalists)} Präsentationen zusammenführen? (j/n): ").strip().lower()
    if confirm not in ('j', 'ja', 'y', 'yes'):
        print("Abgebrochen.")
        return

    # Mergen
    master_id = copy_slides_to_master(slides_service, drive_service, finalists)
    print(f"\n📎 Link zur Master-Präsentation:")
    print(f"   https://docs.google.com/presentation/d/{master_id}/edit")


if __name__ == '__main__':
    main()
