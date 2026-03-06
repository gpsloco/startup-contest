/**
 * =====================================================
 *  StartUp Contest – Google Apps Script
 *  Speichert Formular-Einreichungen in Google Sheets
 * =====================================================
 *
 *  SETUP (einmalig, dauert ~5 Min):
 *
 *  1. Gehe zu https://script.google.com
 *  2. Klicke "Neues Projekt"
 *  3. Kopiere diesen Code in den Editor
 *  4. Ersetze SPREADSHEET_ID mit der ID deines Google Sheets
 *     (aus der URL: docs.google.com/spreadsheets/d/HIER_IST_DIE_ID/edit)
 *  5. Klicke "Speichern", dann "Bereitstellen" → "Neue Bereitstellung"
 *  6. Typ: "Web-App", Zugriff: "Jeder"
 *  7. Kopiere die Web-App-URL in register.html → APPS_SCRIPT_URL
 * =====================================================
 */

const SPREADSHEET_ID = 'DEINE_SPREADSHEET_ID_HIER'; // ← ersetzen
const SHEET_NAME = 'Bewerbungen';

/**
 * Verarbeitet POST-Anfragen vom Formular
 */
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    appendToSheet(data);
    sendConfirmationEmail(data);

    return ContentService
      .createTextOutput(JSON.stringify({ success: true }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ success: false, error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Schreibt die Daten in das Google Sheet
 */
function appendToSheet(data) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  let sheet = ss.getSheetByName(SHEET_NAME);

  // Sheet anlegen falls nicht vorhanden
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    // Header-Zeile
    sheet.appendRow([
      'Timestamp',
      'StartUp-Name',
      'Gründungsjahr',
      'Produkt / Leistung',
      'Ansprechpartner',
      'E-Mail',
      'Postanschrift',
      'Google Slides Link',
      'Status'
    ]);
    // Header formatieren
    const headerRange = sheet.getRange(1, 1, 1, 9);
    headerRange.setBackground('#1a1a2e');
    headerRange.setFontColor('#ffffff');
    headerRange.setFontWeight('bold');
    sheet.setFrozenRows(1);
  }

  // Datenzeile einfügen
  sheet.appendRow([
    new Date(data.timestamp),
    data.startupName   || '',
    data.foundingYear  || '',
    data.productName   || '',
    data.contactName   || '',
    data.email         || '',
    data.address       || '',
    data.slidesUrl     || '',
    'Neu'  // Status: Neu / Finalist / Abgelehnt
  ]);

  // Spaltenbreiten automatisch anpassen
  sheet.autoResizeColumns(1, 9);
}

/**
 * Sendet eine Bestätigungs-E-Mail an den Bewerber
 */
function sendConfirmationEmail(data) {
  if (!data.email) return;

  const subject = `✅ Bewerbung erhalten – StartUp Contest`;
  const body = `
Hallo ${data.contactName},

vielen Dank für deine Bewerbung beim StartUp Contest!

Wir haben folgende Angaben erhalten:
• StartUp: ${data.startupName}
• Gründungsjahr: ${data.foundingYear}
• Produkt / Leistung: ${data.productName}
• Präsentation: ${data.slidesUrl}

Wir prüfen deine Bewerbung und melden uns in Kürze bei dir.

Viele Grüße,
Das StartUp Contest Team
  `.trim();

  MailApp.sendEmail({
    to: data.email,
    subject: subject,
    body: body
  });
}

/**
 * GET-Handler für Testzwecke
 */
function doGet(e) {
  return ContentService
    .createTextOutput('StartUp Contest API läuft ✓')
    .setMimeType(ContentService.MimeType.TEXT);
}
