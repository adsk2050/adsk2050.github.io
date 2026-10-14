"""Build the audio for blog/speech-you-can-hear.html. Never calls a paid API.

Two free sources:
- Bulbul Lab clips already synthesised by bulbul-build, read from its TTS cache
  (files named by the hash of the exact Sarvam request).
- exp001 (streaming TTS) chunks, synthesised locally with Kokoro.

Every clip is encoded as mono AAC in .m4a, which every browser plays.

    python tools/speech_audio.py [--bulbul-cache DIR] [--exp001 DIR]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "blog" / "audio" / "speech"
BITRATE = "48k"

TTS_MODEL = "bulbul:v4-flash"
NARRATOR = ("en-IN", "shubh_en_narration")
NARRATOR_ENHI = ("hi-IN", "ishita_enhi_companion")

# (name, text, language, speaker, pace). Text must match the cached request byte for byte.
LESSONS: dict[str, dict] = {
    "numbers": {
        "intro": "Lesson one: text normalisation. Before I can speak, I must decide how to say what is written. "
                 "Rupees, dates, times, a PNR, a phone number, and acronyms: some are read as words, some letter by letter. "
                 "Listen.",
        "clips": [
            ("Your loan of ₹5,00,000 is approved.", "en-IN", "simran_en_customer"),
            ("Your train leaves on 12/10/2026 at 9:47 am.", "en-IN", "simran_en_customer"),
            ("PNR 4521876390. For help, call 98765 43210.", "en-IN", "simran_en_customer"),
            ("ISRO launched it, but the EMI is still due.", "en-IN", "simran_en_customer"),
        ],
        "outro": "ISRO is a word. EMI is three letters. Nobody wrote that down for me; context decided.",
    },
    "script": {
        "intro": "Lesson two: grapheme to phoneme. I turn letters into sounds. "
                 "Devanagari spells Hindi sounds almost one to one. Romanised Hindi makes me guess: "
                 "is this a short a or a long a? Same sentence, same voice, two scripts.",
        "clips": [
            ("आज मौसम बहुत अच्छा है, चलो बाहर चाय पीते हैं।", "hi-IN", "simran_hi_conversation"),
            ("Aaj mausam bahut accha hai, chalo bahar chai peete hain.", "hi-IN", "simran_hi_conversation"),
        ],
        "outro": "Sarvam's own guide says it plainly: write Hindi in Devanagari. Romanised text sounds worse.",
    },
    "codemix": {
        "narrator": NARRATOR_ENHI,
        "intro": "Lesson three: code-mixing. India बोलता है Hinglish. Hindi words Devanagari में, English words Latin में. "
                 "पहले एक pure Hindi voice, फिर एक Hinglish voice. English words पर ध्यान दीजिए।",
        "clips": [
            ("Kal की meeting cancel हो गई, तो weekend पर movie plan करते हैं।", "hi-IN", "simran_hi_conversation"),
            ("Kal की meeting cancel हो गई, तो weekend पर movie plan करते हैं।", "hi-IN", "simran_enhi_companion"),
        ],
        "outro": "Hinglish voice तभी चुनिए जब sentence सच में mixed हो, सिर्फ़ एक-दो English शब्द हों तो नहीं।",
    },
    "punctuation": {
        "intro": "Lesson four: prosody. I have no SSML and no pause tags. Punctuation is how you steer my pauses "
                 "and my pitch. Same words, four marks: comma, full stop, exclamation, and ellipsis.",
        "clips": [
            ("Okay, I am coming, give me five minutes.", "en-IN", "simran_en_narration"),
            ("Okay. I am coming. Give me five minutes.", "en-IN", "simran_en_narration"),
            ("Okay! I am coming! Give me five minutes!", "en-IN", "simran_en_narration"),
            ("Okay… I am coming… give me five minutes…", "en-IN", "simran_en_narration"),
        ],
        "outro": "Prosody belongs to the phrase. Move the boundary and the melody moves with it.",
    },
    "pace": {
        "intro": "Lesson five: speaking rate. Inside the model, every sound gets a predicted duration. "
                 "The pace setting stretches or squeezes those durations. "
                 "Slow for teaching, normal for talking, fast for announcements.",
        "clips": [
            ("अगला स्टेशन नई दिल्ली है। कृपया अपना सामान साथ रखें।", "hi-IN", "simran_hi_narration", 0.8),
            ("अगला स्टेशन नई दिल्ली है। कृपया अपना सामान साथ रखें।", "hi-IN", "simran_hi_narration", 1.0),
            ("अगला स्टेशन नई दिल्ली है। कृपया अपना सामान साथ रखें।", "hi-IN", "simran_hi_narration", 1.25),
        ],
    },
    "styles": {
        "intro": "Lesson six: voice and style. My voice IDs read name, language, style. "
                 "Here is one speaker, Simran, in four styles: recovery desk, news, late night radio, "
                 "and excited social. The words stay the same. The delivery changes.",
        "clips": [
            ("आज रात आठ बजे, शहर में बारिश की संभावना है।", "hi-IN", "simran_hi_recovery"),
            ("आज रात आठ बजे, शहर में बारिश की संभावना है।", "hi-IN", "simran_hi_news"),
            ("आज रात आठ बजे, शहर में बारिश की संभावना है।", "hi-IN", "simran_hi_latenight"),
            ("आज रात आठ बजे, शहर में बारिश की संभावना है।", "hi-IN", "simran_hi_social_excited"),
        ],
    },
    "languages": {
        "intro": "Lesson seven: languages. Each language has its own sounds and its own script, "
                 "and a model is only as good as its data in each. Here is one greeting in all ten "
                 "languages that have Bulbul V4 voices.",
        "clips": [
            ("नमस्ते! आप कैसे हैं?", "hi-IN", "simran_hi_conversation"),
            ("Hello! How are you?", "en-IN", "simran_en_conversation"),
            ("Hello! आप कैसे हो?", "hi-IN", "ishita_enhi_companion"),
            ("नमस्कार! तुम्ही कसे आहात?", "mr-IN", "ishita_mr_conversational"),
            ("নমস্কার! আপনি কেমন আছেন?", "bn-IN", "arnab_bn_conversation"),
            ("નમસ્તે! તમે કેમ છો?", "gu-IN", "bhavik_gu_conversation"),
            ("ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ?", "pa-IN", "anand_pa_conversation"),
            ("வணக்கம்! எப்படி இருக்கீங்க?", "ta-IN", "gokul_ta_narration"),
            ("నమస్కారం! మీరు ఎలా ఉన్నారు?", "te-IN", "kavitha_te_conversation"),
            ("ನಮಸ್ಕಾರ! ಹೇಗಿದ್ದೀರಾ?", "kn-IN", "chaitra_kn_conversation"),
        ],
        "outro": "Hindi and English have over a hundred voices. Tamil, Telugu and Kannada have four each.",
    },
    "phone": {
        "intro": "Lesson eight: telephony. A phone line samples at 8 kilohertz and passes only about "
                 "300 to 3400 hertz. The high frequencies that make s and sh crisp are cut off. "
                 "Listen to this sentence, then press the phone-line button to hear it narrowband.",
        "clips": [
            ("नमस्ते, मैं आपके बैंक से बोल रहा हूँ। आपकी अगली EMI 15 तारीख़ को है।", "hi-IN", "shubh_hi_customer"),
        ],
        "outro": "Most Indian voice bots live on this narrow channel, so a voice must stay clear on it.",
        "phone_line": True,
    },
    "limits": {
        "intro": "Lesson nine: honest limits. I am Bulbul V4 Flash, the fast model. I have no laughter, "
                 "whisper or emotion tags; those are promised for V4 Pro, which is not out. I do not sing. "
                 "I cannot clone your voice. I have no SSML. Malayalam and Odia have no V4 voices yet. "
                 "Here is what happens when you type a laugh.",
        "clips": [
            ("Haha! That was so funny.", "en-IN", "simran_en_conversation"),
        ],
        "outro": "I read the laugh as a word. Emotion in speech is still the open problem.",
    },
}

# exp001: arms to compare, and the text each excerpt must cover (the essay's first sentence).
STREAM_ARMS = ["sentence", "clause", "word", "token"]
STREAM_UNTIL = "from a single speaker."


def cache_key(text: str, language: str, speaker: str, pace: float) -> str:
    body = {
        "text": text, "language_code": language, "model": TTS_MODEL, "speaker": speaker,
        "pace": pace, "speech_sample_rate": 24000, "output_audio_codec": "wav",
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def first_pause_end(src: Path, within: float = 1.6) -> float:
    """End of the first pause in the opening seconds, in seconds; 0 if there is none."""
    log = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(src), "-t", str(within), "-af", "silencedetect=n=-35dB:d=0.12",
         "-f", "null", "-"], capture_output=True, text=True, check=True,
    ).stderr
    ends = re.findall(r"silence_end: ([0-9.]+)", log)
    return float(ends[0]) if ends else 0.0


def encode(src: Path, dst: Path, *, phone: bool = False, start: float = 0.0) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    # A phone line: band-limit to 300-3400 Hz and resample to 8 kHz.
    af = ["-af", "highpass=f=300,lowpass=f=3400", "-ar", "8000"] if phone else []
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{start:.3f}", "-i", str(src), "-ac", "1", *af,
         "-c:a", "aac", "-b:a", "24k" if phone else BITRATE, "-movflags", "+faststart", str(dst)],
        check=True,
    )


def build_lessons(cache: Path) -> None:
    missing = []
    for key, lesson in LESSONS.items():
        lang, voice = lesson.get("narrator", NARRATOR)
        lines = [("intro", lesson["intro"], lang, voice, 1.0)]
        for i, clip in enumerate(lesson["clips"]):
            text, clang, speaker, *pace = clip
            lines.append((chr(ord("a") + i), text, clang, speaker, pace[0] if pace else 1.0))
        if lesson.get("outro"):
            lines.append(("outro", lesson["outro"], lang, voice, 1.0))
        for name, text, clang, speaker, pace in lines:
            wav = cache / f"tts-{cache_key(text, clang, speaker, pace)}.wav"
            if not wav.exists():
                missing.append(f"{key}/{name}")
                continue
            # Each intro opens with "Lesson N:"; the page is ordered by concept, so cut that off.
            start = max(0.0, first_pause_end(wav) - 0.05) if name == "intro" else 0.0
            encode(wav, OUT / key / f"{name}.m4a", start=start)
            if lesson.get("phone_line") and name == "a":
                encode(wav, OUT / key / "a-phone.m4a", phone=True)
    if missing:
        sys.exit(f"not in the TTS cache (would cost money to synthesise): {', '.join(missing)}")


def build_streaming(exp001: Path) -> None:
    runs = [json.loads(line) for line in (exp001 / "results" / "runs.jsonl").read_text(encoding="utf-8").splitlines()]
    for arm in STREAM_ARMS:
        run = next(r for r in runs if r["engine"] == "kokoro" and r["arm"] == arm and not r["excerpt"])
        files, text = [], ""
        for chunk in sorted(run["schedule"], key=lambda c: c["i"]):
            files.append(exp001 / "results" / "audio" / "kokoro" / f"essay__{arm}" / f"{chunk['i']:03d}.wav")
            text += chunk["text"]
            if STREAM_UNTIL in text:
                break
        with tempfile.TemporaryDirectory() as tmp:
            listing = Path(tmp) / "list.txt"
            listing.write_text("".join(f"file '{f.as_posix()}'\n" for f in files), encoding="utf-8")
            joined = Path(tmp) / "joined.wav"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                            "-i", str(listing), "-c", "copy", str(joined)], check=True)
            encode(joined, OUT / "streaming" / f"{arm}.m4a")
        print(f"streaming/{arm}: {len(files)} chunks")


def build_clips() -> None:
    """Clips listed in speech_clips.py, from the raw audio speech_synth.py made."""
    from speech_clips import CLIPS
    from speech_synth import raw_path

    missing = []
    for c in CLIPS:
        src = raw_path(c)
        if not src.exists():
            missing.append(f"{c.provider}:{c.slide}/{c.name}")
            continue
        encode(src, OUT / c.slide / f"{c.name}.m4a")
    if missing:
        print("not made yet (run speech_synth.py):", ", ".join(missing))


def build_derived(cache: Path) -> None:
    """Pace 1.0 played twice as fast: a plain time-stretch, to compare with the model's pace 2.0."""
    text, lang, speaker, pace = LESSONS["pace"]["clips"][1]
    wav = cache / f"tts-{cache_key(text, lang, speaker, pace)}.wav"
    dst = OUT / "pace" / "sped2x.m4a"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-af", "atempo=2.0", "-ac", "1",
                    "-c:a", "aac", "-b:a", BITRATE, "-movflags", "+faststart", str(dst)], check=True)


def prune() -> None:
    """Delete encoded clips the page does not play (unused candidates, replaced narration)."""
    page = (OUT.parent.parent / "speech-you-can-hear.html").read_text(encoding="utf-8")
    used = set(re.findall(r'data-src="audio/speech/([^"]+)"', page))
    for f in OUT.rglob("*.m4a"):
        if f.relative_to(OUT).as_posix() not in used:
            f.unlink()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bulbul-cache", type=Path, default=Path("D:/bulbul-build/data/cache"))
    ap.add_argument("--exp001", type=Path,
                    default=Path("D:/learn/speech/cs224s/experiments/exp001-streaming-tts"))
    args = ap.parse_args()
    build_lessons(args.bulbul_cache)
    build_streaming(args.exp001)
    build_derived(args.bulbul_cache)
    build_clips()
    prune()


if __name__ == "__main__":
    main()
