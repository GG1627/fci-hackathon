# FridgeGuard dashboard

Display-only Next.js dashboard for the Gainesville Community Fridge. It requests real sensor data from the Raspberry Pi FastAPI service and refreshes every five seconds.

## Start both services

Start the Pi API from the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 pi/api.py
```

Then start the dashboard from `web/`:

```bash
npm install
npm run dev
```

Open <http://localhost:3000>.

By default, the browser connects to port `8000` on the same hostname used to open the dashboard. For example, a dashboard opened at `http://gaels-pi-5.local:3000` automatically requests `http://gaels-pi-5.local:8000/api/readings`.

If the API runs at another address, copy `.env.example` to `.env.local`, set `NEXT_PUBLIC_FRIDGEGUARD_API_URL`, and restart the Next.js development server.

The dashboard requests up to 300 recent readings, prefers `device_id = 'fridge-sensor-01'`, and falls back to the most recent available device. The recent readings provide the current closed-to-open door transition for the live timer.

## Demo thresholds

- Maximum temperature: 80°F (`DEMO_TEMP_MAX_F`)
- Door-open danger: 2 minutes (`DOOR_OPEN_TOO_LONG_MS`)
- Stale/offline: 2 minutes (`STALE_AFTER_MS`)

These named constants are in `lib/status.ts`. The frontend derives its two-minute demo stale state from the reading timestamp rather than using the Pi API's ten-second status indicator. The production refrigerator temperature threshold should be 40°F.
