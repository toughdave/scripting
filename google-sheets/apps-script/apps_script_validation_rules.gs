/*
  Google Apps Script template: apply validation rules and export a sanitized CSV.

  Setup:
  1) Open Google Sheet -> Extensions -> Apps Script.
  2) Paste this file.
  3) Update SHEET_NAME and EXPORT_FOLDER_NAME.
  4) Run applyValidationRules(), then exportSanitizedCsv().
*/

const SHEET_NAME = 'Data';
const EXPORT_FOLDER_NAME = 'scripting-exports';

function applyValidationRules() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) throw new Error('Sheet not found: ' + SHEET_NAME);

  const lastRow = Math.max(2, sheet.getLastRow());

  // Column mapping (A=1, B=2, ...)
  // A: student_id (required text)
  // C: email (must contain @)
  // G: score (number between 0 and 100)
  // H: status (open|closed|in_progress|completed)

  const studentIdRange = sheet.getRange(2, 1, lastRow - 1, 1);
  const emailRange = sheet.getRange(2, 3, lastRow - 1, 1);
  const scoreRange = sheet.getRange(2, 7, lastRow - 1, 1);
  const statusRange = sheet.getRange(2, 8, lastRow - 1, 1);

  const requiredRule = SpreadsheetApp.newDataValidation()
    .requireTextIsEmail()
    .setAllowInvalid(true)
    .build();

  // Keep student_id simple: non-empty enforced via conditional formatting/check script.
  studentIdRange.clearDataValidations();

  const emailRule = SpreadsheetApp.newDataValidation()
    .requireTextContains('@')
    .setAllowInvalid(false)
    .build();

  const scoreRule = SpreadsheetApp.newDataValidation()
    .requireNumberBetween(0, 100)
    .setAllowInvalid(false)
    .build();

  const statusRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(['open', 'closed', 'in_progress', 'completed'], true)
    .setAllowInvalid(false)
    .build();

  emailRange.setDataValidation(emailRule);
  scoreRange.setDataValidation(scoreRule);
  statusRange.setDataValidation(statusRule);

  SpreadsheetApp.flush();
}

function exportSanitizedCsv() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) throw new Error('Sheet not found: ' + SHEET_NAME);

  const values = sheet.getDataRange().getValues();
  if (values.length < 2) throw new Error('No data rows to export.');

  const headers = values[0];
  const rows = values.slice(1);

  const outRows = [];
  outRows.push(headers);

  rows.forEach(function(row) {
    const studentId = String(row[0] || '').trim();
    const email = String(row[2] || '').trim();
    const scoreRaw = row[6];
    const status = String(row[7] || '').trim().toLowerCase();

    const score = Number(scoreRaw);
    const validEmail = email.indexOf('@') > 0;
    const validScore = !isNaN(score) && score >= 0 && score <= 100;
    const validStatus = ['open', 'closed', 'in_progress', 'completed'].indexOf(status) >= 0;

    if (studentId && validEmail && validScore && validStatus) {
      outRows.push(row);
    }
  });

  const csv = outRows
    .map(function(r) {
      return r
        .map(function(cell) {
          const s = String(cell == null ? '' : cell);
          return '"' + s.replace(/"/g, '""') + '"';
        })
        .join(',');
    })
    .join('\n');

  const folder = getOrCreateFolder_(EXPORT_FOLDER_NAME);
  const timestamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMdd-HHmmss');
  const fileName = 'sanitized-export-' + timestamp + '.csv';
  folder.createFile(fileName, csv, MimeType.CSV);
}

function getOrCreateFolder_(name) {
  const iter = DriveApp.getFoldersByName(name);
  if (iter.hasNext()) return iter.next();
  return DriveApp.createFolder(name);
}
