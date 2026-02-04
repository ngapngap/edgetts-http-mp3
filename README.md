# EdgeTTS HTTP Service (MP3)

A lightweight HTTP service that generates **MP3** speech using Microsoft **Edge TTS** (`edge-tts`) via **aiohttp**.

> ⚠️ Security note: this service currently has **no authentication** and **no rate-limiting**. If you bind to `0.0.0.0` / expose it to the Internet, you should add auth + limits (or restrict by firewall / VPN).

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
- `voice` is optional. If omitted, the server attempts to pick a Vietnamese voice; otherwise it falls back to the default.
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

## Configuration (Environment Variables)

- `EDGE_TTS_HOST` (default: `127.0.0.1`)
- `EDGE_TTS_PORT` (default: `19090`)
- `EDGE_TTS_VOICE` (default: `vi-VN-HoaiMyNeural`)

---

## Install

```bash
cd /root/edgetts
python3 -m pip install -r requirements.txt
```

---

## Run

### Local only (default)
```bash
cd /root/edgetts
python3 app.py
```
Binds to: `127.0.0.1:19090`

### Public bind (temporary)
```bash
cd /root/edgetts
EDGE_TTS_HOST=0.0.0.0 EDGE_TTS_PORT=19090 python3 app.py
```
Binds to: `0.0.0.0:19090`

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

---

## Integration note (Clawdbot Android Talk Mode)

If using the Android patch that supports a custom TTS URL, configure:
- `talk.ttsUrl` = full endpoint URL, e.g. `http://43.228.213.7:19090/tts`

The Android client sends JSON like:
```json
{ "text": "...", "voice": "...", "format": "mp3" }
```

---

## Dependencies

- `edge-tts`
- `aiohttp`
