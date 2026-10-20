// Google Form -> GitHub. Attach this to the Google Sheet linked to the form
// (Extensions > Apps Script), then add a trigger: onFormSubmit, From spreadsheet, On form submit.
// Store the token under Project Settings > Script properties as GITHUB_TOKEN.

const OWNER = 'YOUR_GITHUB_USER';
const REPO  = 'etichette';

// Left: key used by generate_label.py. Right: exact question title in your form.
const FIELD_MAP = {
  name:    'Recipient name',
  street:  'Street and number',
  city:    'Postcode and city',
  country: 'Country',
  province:'Province',
  contents:'Contents',
  weight:  'Weight (kg)',
  eta:     'Estimated delivery',
};

function onFormSubmit(e) {
  const answers = e.namedValues;                       // { 'Question title': ['answer'] }
  const payload = {};
  Object.keys(FIELD_MAP).forEach(k => {
    const v = answers[FIELD_MAP[k]];
    if (v && v[0]) payload[k] = v[0];
  });
  // Unique tracking code per submission: SPY-2026-<row number>
  payload.tracking = 'SPY-2026-' + String(e.range.getRow()).padStart(6, '0');

  const token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  const res = UrlFetchApp.fetch(`https://api.github.com/repos/${OWNER}/${REPO}/dispatches`, {
    method: 'post',
    contentType: 'application/json',
    headers: { Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json' },
    payload: JSON.stringify({ event_type: 'new-label', client_payload: payload }),
    muteHttpExceptions: true,
  });
  if (res.getResponseCode() !== 204) console.error(res.getResponseCode(), res.getContentText());
}
