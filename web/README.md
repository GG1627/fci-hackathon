# Community Chill dashboard

The Next.js dashboard displays live sensor health from the Raspberry Pi's local
SQLite database and the newest camera images from Supabase Storage. The browser
only talks to the Pi API; Supabase credentials remain on the Pi.

## Start the complete Pi service

From the repository root on the Raspberry Pi:

```bash
python3 -m pip install -r requirements.txt
python3 pi/main.py
```

This starts serial logging, the local API, periodic camera capture, and Discord
alerts when their environment variables are configured.

## Start the dashboard

From `web/` on either the Pi or another computer on the same network:

```bash
npm install
npm run dev
```

Open <http://localhost:3000>. By default, the browser uses port `8000` on the
same hostname used to open the dashboard. For example, opening
`http://gaels-pi-5.local:3000` makes the browser call
`http://gaels-pi-5.local:8000`.

If the dashboard and API use different hosts, copy `.env.example` to
`.env.local`, set `NEXT_PUBLIC_FRIDGEGUARD_API_URL`, and restart Next.js.
This URL is public browser configuration; never add a Supabase secret key to
`web/.env.local`.

The dashboard polls sensor readings and server-side health rules every five
seconds. Camera images refresh every 30 seconds. The latest image and up to ten
previous images are available in the gallery.
