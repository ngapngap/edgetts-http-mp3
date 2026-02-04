# EdgeTTS HTTP Service (MP3)

A lightweight HTTP service that generates **MP3** speech using Microsoft **Edge TTS** (`edge-tts`) via **aiohttp**.

> ⚠️ Security note: this service currently has **no authentication** and **no rate-limiting**. If you bind to `0.0.0.0` / expose it to the Internet, you should add auth + limits (or restrict by firewall / VPN).

---

## Features

- Simple HTTP API
- Returns **MP3** (`audio/mpeg`)
- Optional voice + prosody params (`rate`, `pitch`, `volume`)
- Response includes resolved voice header: `X-Voice`

---

## Requirements

- Python 3.10+ (recommended)
- Network access to Microsoft Edge TTS backend (used by `edge-tts`)

---

## Quickstart

```bash
git clone https://github.com/ngapngap/edgetts-http-mp3
cd edgetts-http-mp3

python3 -m venv .venv
source .venv/bin/activate

python3 -m pip install -r requirements.txt
python3 app.py
```

Default bind: `127.0.0.1:19090`

---

## Configuration (Environment Variables)

- `EDGE_TTS_HOST` (default: `127.0.0.1`)
- `EDGE_TTS_PORT` (default: `19090`)
- `EDGE_TTS_VOICE` (default: `vi-VN-HoaiMyNeural`)

Example (public bind):

```bash
EDGE_TTS_HOST=0.0.0.0 EDGE_TTS_PORT=19090 python3 app.py
```

---

## Endpoints

### `GET /health`
Returns service status.

**Response (200, JSON)**
```json
{ "status": "ok" }
```

---

### `POST /tts`
Generate speech and return **MP3** (`audio/mpeg`).

#### Request

**Headers**
- `Content-Type: application/json`
- (recommended) `Accept: audio/mpeg`

**JSON body**
```json
{
  "text": "Xin chào Nam",
  "voice": "vi-VN-HoaiMyNeural",
  "rate": "+0%",
  "pitch": "+0Hz",
  "volume": "+0%",
  "format": "mp3"
}
```

Notes:
- `text` can also be provided as `input`.
- `voice` is optional. If omitted, the server attempts to pick a Vietnamese voice; otherwise it falls back to `EDGE_TTS_VOICE`.
- `rate`, `pitch`, `volume` are optional strings in Edge-TTS format.
- `format` currently only supports MP3 (`mp3`, `mpeg`, `audio/mpeg`).

#### Success response

**200** with binary MP3 body
- `Content-Type: audio/mpeg`
- `Cache-Control: no-store`
- `X-Voice: <resolved voice name>`

#### Error response

All errors return **JSON**:
```json
{ "error": { "message": "..." } }
```

Common status codes:
- `415` Unsupported `Content-Type` (must be `application/json`)
- `400` Invalid JSON / unsupported format
- `422` Missing `text` (or `input`)
- `500` TTS failed (edge-tts error)

---

## Test

### Health
```bash
curl -sS http://127.0.0.1:19090/health
```

### TTS → mp3 file
```bash
curl -sS http://127.0.0.1:19090/tts \
  -H 'Content-Type: application/json' \
  -H 'Accept: audio/mpeg' \
  -d '{"text":"Xin chào Nam"}' \
  --output out.mp3
```

### TTS with voice + prosody
```bash
curl -sS http://127.0.0.1:19090/tts \
  -H 'Content-Type: application/json' \
  -H 'Accept: audio/mpeg' \
  -d '{"text":"Xin chào Nam","voice":"vi-VN-HoaiMyNeural","rate":"+5%","pitch":"+0Hz","volume":"+0%"}' \
  --output out.mp3
```

---

## Picking a voice

You can use any voice supported by Edge TTS.

List voices (on the same machine):
```bash
python3 -m pip install edge-tts
edge-tts --list-voices | grep -i "vi-VN" | head
```

If `voice` is omitted, the server tries to auto-select a Vietnamese voice.

---

## Limits

- Max request body size is **2MB** (see `client_max_size` in `app.py`).
- This is a simple service; for public exposure you should add:
  - authentication
  - rate-limiting
  - reverse proxy (nginx) and TLS

---

## Integration note (Clawdbot Android Talk Mode)

If using the Android patch that supports a custom TTS URL, configure:
- `talk.ttsUrl` = full endpoint URL, e.g. `http://43.228.213.7:19090/tts`

The Android client sends JSON like:
```json
{ "text": "...", "voice": "...", "format": "mp3" }
```

---

## Run as a service (systemd example)

> This is an example snippet; adjust paths/user/port as needed.

Create `/etc/systemd/system/edgetts.service`:

```ini
[Unit]
Description=EdgeTTS HTTP MP3 Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/root/edgetts-http-mp3
ExecStart=/root/edgetts-http-mp3/.venv/bin/python /root/edgetts-http-mp3/app.py
Restart=always
RestartSec=2
Environment=EDGE_TTS_HOST=0.0.0.0
Environment=EDGE_TTS_PORT=19090
Environment=EDGE_TTS_VOICE=vi-VN-HoaiMyNeural

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now edgetts
sudo systemctl status edgetts --no-pager
```

---

## Dependencies

- `edge-tts`
- `aiohttp`
