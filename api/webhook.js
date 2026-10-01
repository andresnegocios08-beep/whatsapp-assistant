export default async function handler(req, res) {
  const APPS_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbzAsF6fHi66S0uYvsT9agVRAATQSbEsHESPWaKz1sbnja2kTEuetO3dX_ms2_rrYCjQ/exec';

  const query = new URLSearchParams(req.query || {}).toString();
  const targetUrl = query ? `${APPS_SCRIPT_URL}?${query}` : APPS_SCRIPT_URL;

  try {
    if (req.method === 'GET') {
      const response = await fetch(targetUrl, {
        method: 'GET',
        redirect: 'follow'
      });
      const text = await response.text();

      if (text.includes('accounts.google.com') || text.includes('signin')) {
        return res.status(500).send('Apps Script requiere autenticación');
      }

      return res.status(200).send(text);
    }

    if (req.method === 'POST') {
      const response = await fetch(targetUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body),
        redirect: 'follow'
      });
      const text = await response.text();
      return res.status(200).send(text);
    }

    return res.status(405).send('Method not allowed');

  } catch (error) {
    return res.status(500).send('Error: ' + error.message);
  }
}
