#!/usr/bin/env python3
"""EdgeTTS local HTTP service (project: /root/edgetts).

- Binds to 127.0.0.1 only by default (not public)
- GET  /health -> {"status":"ok"}
- POST /tts    -> audio/mpeg (mp3)

JSON body:
  {
    "text": "..."                 # required (or "input")
    "voice": "vi-VN-HoaiMyNeural" # optional
    "rate": "+0%"                # optional (edge-tts format)
    "pitch": "+0Hz"              # optional
    "volume": "+0%"              # optional
    "format": "mp3"              # optional (only mp3 supported)
  }

Run:
  python3 app.py

Test:
  curl -sS http://127.0.0.1:19090/health
  curl -sS http://127.0.0.1:19090/tts -H 'Content-Type: application/json' \
    -d '{"text":"Xin chào Nam"}' --output out.mp3
"""

import os
import tempfile
import logging
from aiohttp import web

import edge_tts

HOST = os.environ.get("EDGE_TTS_HOST", "127.0.0.1")
PORT = int(os.environ.get("EDGE_TTS_PORT", "19090"))
DEFAULT_VOICE = os.environ.get("EDGE_TTS_VOICE", "vi-VN-HoaiMyNeural")


def json_error(status: int, message: str) -> web.Response:
    return web.json_response({"error": {"message": message}}, status=status)


async def pick_voice(requested: str | None) -> str:
    if requested and requested.strip():
        return requested.strip()
    try:
        voices = await edge_tts.VoicesManager.create()
        matches = voices.find(Locale="vi-VN") or voices.find(Language="vi")
        if matches:
            return matches[0]["Name"]
    except Exception:
        pass
    return DEFAULT_VOICE


async def health(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def tts(req: web.Request) -> web.StreamResponse:
    ctype = (req.headers.get("content-type") or "").lower()
    if "application/json" not in ctype:
        return json_error(415, f"Unsupported content-type: {req.headers.get('content-type','')}")

    try:
        payload = await req.json()
    except Exception:
        return json_error(400, "Invalid JSON")

    text = str(payload.get("text") or payload.get("input") or "").strip()
    if not text:
        return json_error(422, "Missing 'text' (or 'input')")

    fmt = str(payload.get("format") or "mp3").lower().strip()
    if fmt not in ("mp3", "mpeg", "audio/mpeg"):
        return json_error(400, f"Unsupported format: {fmt} (only mp3 supported)")

    voice = await pick_voice(payload.get("voice"))

    extra = {}
    for k in ("rate", "volume", "pitch"):
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            extra[k] = v.strip()

    fd, out_path = tempfile.mkstemp(prefix="edge_tts_", suffix=".mp3")
    os.close(fd)
    try:
        communicate = edge_tts.Communicate(text, voice=voice, **extra)
        await communicate.save(out_path)

        resp = web.StreamResponse(status=200)
        resp.content_type = "audio/mpeg"
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["X-Voice"] = voice
        await resp.prepare(req)

        with open(out_path, "rb") as f:
            while True:
                chunk = f.read(64 * 1024)
                if not chunk:
                    break
                await resp.write(chunk)
        await resp.write_eof()
        return resp
    except Exception as e:
        return json_error(500, f"TTS failed: {e.__class__.__name__}: {e}")
    finally:
        try:
            os.remove(out_path)
        except Exception:
            pass


def main() -> None:
    app = web.Application(client_max_size=2 * 1024 * 1024)
    app.router.add_get("/health", health)
    app.router.add_post("/tts", tts)

    # Access log enabled (useful for debugging client requests)
    logging.basicConfig(level=logging.INFO)
    access_logger = logging.getLogger("edgetts.access")

    web.run_app(app, host=HOST, port=PORT, access_log=access_logger)


if __name__ == "__main__":
    main()
