"""Make the raw audio for tools/speech_clips.py. Sarvam, OpenAI and Cartesia cost money.

Already-made clips are skipped, so a rerun only pays for what is missing.
Each provider runs in the environment that has its library:

    uv run --project D:/bulbul-build python tools/speech_synth.py sarvam
    D:/learn/speech/cs224s/experiments/exp001-streaming-tts/.venv/Scripts/python.exe tools/speech_synth.py kokoro
    python tools/speech_synth.py openai
    python tools/speech_synth.py cartesia

Keys come from D:/shrota/.env (OpenAI, Cartesia) and bulbul-build's own .env
(Sarvam). They are never printed.
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import sys
import urllib.request
import wave
from pathlib import Path

from speech_clips import CLIPS, C

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "tmp" / "speech-raw"
BULBUL = Path("D:/bulbul-build")


def raw_path(c: C) -> Path:
    return RAW / c.provider / f"{c.slide}-{c.name}-{c.key()}.wav"


def env_key(name: str) -> str:
    for line in Path("D:/shrota/.env").read_text(encoding="utf-8").splitlines():
        k, _, v = line.partition("=")
        if k.strip() == name:
            return v.strip().strip('"').strip("'")
    sys.exit(f"{name} not found in D:/shrota/.env")


def post(url: str, body: dict, headers: dict) -> bytes:
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def todo(provider: str) -> list[C]:
    return [c for c in CLIPS if c.provider == provider and not raw_path(c).exists()]


def run_openai() -> None:
    auth = {"Authorization": f"Bearer {env_key('OPENAI_API_KEY')}"}
    for c in todo("openai"):
        body = {"model": c.model, "voice": c.voice, "input": c.text, "response_format": "wav"}
        if c.instructions:
            body["instructions"] = c.instructions
        raw_path(c).parent.mkdir(parents=True, exist_ok=True)
        raw_path(c).write_bytes(post("https://api.openai.com/v1/audio/speech", body, auth))
        print("openai", c.slide, c.name)


def run_cartesia() -> None:
    hdr = {"X-API-Key": env_key("CARTESIA_API_KEY"), "Cartesia-Version": "2025-04-16"}
    req = urllib.request.Request("https://api.cartesia.ai/voices?limit=100", headers=hdr)
    with urllib.request.urlopen(req, timeout=60) as r:
        voices = json.loads(r.read())
    voices = voices.get("data", voices) if isinstance(voices, dict) else voices
    english = [v for v in voices if v.get("language") == "en"]
    emotive = [v for v in english if "emotive" in (v.get("name", "") + v.get("description", "")).lower()]
    voice = (emotive or english)[0]
    print("cartesia voice:", voice.get("name"))
    for c in todo("cartesia"):
        body = {"model_id": c.model, "transcript": c.text, "voice": {"mode": "id", "id": voice["id"]}, "language": "en",
                "output_format": {"container": "wav", "encoding": "pcm_s16le", "sample_rate": 24000}}
        raw_path(c).parent.mkdir(parents=True, exist_ok=True)
        raw_path(c).write_bytes(post("https://api.cartesia.ai/tts/bytes", body, hdr))
        print("cartesia", c.slide, c.name)


def run_kokoro() -> None:
    import numpy as np
    from kokoro import KPipeline

    pipes: dict[str, KPipeline] = {}
    for c in todo("kokoro"):
        pipe = pipes.setdefault(c.lang, KPipeline(lang_code=c.lang, device="cpu"))
        if c.phonemes:
            parts = [r.audio for r in pipe.generate_from_tokens(c.phonemes, voice=c.voice)]
        else:
            g, _ = pipe.g2p(c.text)
            print("  phonemes:", g if isinstance(g, str) else g)
            parts = [r.audio for r in pipe(c.text, voice=c.voice)]
        audio = np.concatenate([np.asarray(p, dtype=np.float32) for p in parts])
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
            w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
        raw_path(c).parent.mkdir(parents=True, exist_ok=True)
        raw_path(c).write_bytes(buf.getvalue())
        print("kokoro", c.slide, c.name)


def run_sarvam() -> None:
    sys.path.insert(0, str(BULBUL / "src"))
    from bulbul_build.config import load
    from bulbul_build.budget import Caps, Ledger
    from bulbul_build.sarvam import Sarvam

    s = load()
    sarvam = Sarvam(s.sarvam_api_key, Ledger(s.ledger_path, Caps(s.daily_budget_inr, s.total_budget_inr,
                                                                 s.per_call_budget_inr)), s.cache_dir)

    async def go() -> None:
        for c in todo("sarvam"):
            wav = await sarvam.tts(c.text, c.lang, c.voice, mode="blog", pace=c.pace)
            raw_path(c).parent.mkdir(parents=True, exist_ok=True)
            raw_path(c).write_bytes(wav)
            print("sarvam", c.slide, c.name)

    asyncio.run(go())


if __name__ == "__main__":
    os.chdir(ROOT)
    {"openai": run_openai, "cartesia": run_cartesia, "kokoro": run_kokoro, "sarvam": run_sarvam}[sys.argv[1]]()
