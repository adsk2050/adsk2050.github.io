"""Every clip on blog/speech-you-can-hear.html, new batch (2026-10-14).

One list, read by tools/speech_synth.py (makes the raw audio, may cost money)
and tools/speech_audio.py (encodes it for the page, free). Each clip is
identified by slide + name; the file lands at blog/audio/speech/<slide>/<name>.m4a.

provider:
- sarvam: Bulbul V4 Flash. Raw audio lives in bulbul-build's TTS cache.
- openai, cartesia: raw audio in tmp/speech-raw/<provider>/.
- kokoro: local, free. `lang` is Kokoro's lang code; `phonemes` skips G2P.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

NARR = ("shubh_en_narration", "en-IN")
NARR_ENHI = ("ishita_enhi_companion", "hi-IN")


@dataclass(frozen=True)
class C:
    slide: str
    name: str
    provider: str
    text: str
    voice: str
    lang: str = ""
    pace: float = 1.0
    instructions: str = ""
    phonemes: str = ""
    model: str = ""

    def key(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24]


def bulbul(slide: str, name: str, text: str, voice: str, lang: str, pace: float = 1.0) -> C:
    return C(slide, name, "sarvam", text, voice, lang, pace)


def narr(slide: str, name: str, text: str, who: tuple[str, str] = NARR) -> C:
    return bulbul(slide, name, text, *who)


ROMAN = "Main do minute mein aata hoon, bus ruko."
DEVA = "मैं दो मिनट में आता हूँ, बस रुको।"
MIXED = "Kal की meeting cancel हो गई, तो weekend पर movie plan करते हैं।"
ROMAN_MIX = "Kal ki meeting cancel ho gayi, toh weekend pe movie plan karte hain."
STATION = "अगला स्टेशन नई दिल्ली है। कृपया अपना सामान साथ रखें।"
MATCH = "आज रात आठ बजे भारत का मैच है, देर मत करना!"
MATCH_EN = "The match starts at eight tonight. Don't be late."
STOLE = "I didn't say she stole it."

CLIPS: list[C] = [
    # ---- Text normalisation ----
    narr("numbers", "intro2", "Text normalisation. Before I speak, I rewrite symbols as words. Digits are the hardest: "
         "the same four digits can be a phone number, a year, a price or a time. Only the words around them tell me which. Listen."),
    narr("numbers", "outro2", "Same digits, four readings. Context decides, and a reader trained on other rules gets it wrong."),
    bulbul("numbers", "in-loan", "Your loan of ₹5,00,000 is due on 12/10/2026.", "simran_en_customer", "en-IN"),
    C("numbers", "us-loan", "kokoro", "Your loan of ₹5,00,000 is due on 12/10/2026.", "af_heart", "a"),
    bulbul("numbers", "n-phone", "Call 1800 now.", "simran_en_customer", "en-IN"),
    bulbul("numbers", "n-year", "He was born in 1800.", "simran_en_customer", "en-IN"),
    bulbul("numbers", "n-price", "Pay ₹1800 today.", "simran_en_customer", "en-IN"),
    bulbul("numbers", "n-time", "The train leaves at 18:00.", "simran_en_customer", "en-IN"),

    # ---- Spelling to sound ----
    narr("script", "intro2", "Spelling to sound. I turn letters into sounds. Devanagari spells Hindi almost one to one. "
         "Latin letters bring English habits with them: main can become mane, and do can become doo. "
         "Same sentence, different scripts and readers."),
    narr("script", "outro2", "The script carries the sound. Write Hindi in Devanagari and nobody has to guess."),
    C("script", "k-deva", "kokoro", DEVA, "hf_alpha", "h"),
    C("script", "k-roman", "kokoro", ROMAN, "hf_alpha", "h"),
    C("script", "k-roman-en", "kokoro", ROMAN, "af_heart", "a"),
    bulbul("script", "b-deva", DEVA, "simran_hi_conversation", "hi-IN"),
    bulbul("script", "b-roman", ROMAN, "simran_hi_conversation", "hi-IN"),
    bulbul("script", "b-roman-en", ROMAN, "simran_en_conversation", "en-IN"),
    bulbul("script", "pita-deva", "मेरा बेटा रोज़ दूध पीता है।", "simran_hi_conversation", "hi-IN"),
    bulbul("script", "pita-roman", "mera beta roz doodh pita hai", "simran_hi_conversation", "hi-IN"),
    bulbul("script", "kam-roman", "aaj kam hai", "simran_hi_conversation", "hi-IN"),

    # ---- Code-mixing ----
    C("codemix", "k-english", "kokoro", ROMAN_MIX, "af_heart", "a"),
    bulbul("codemix", "b-roman-mix", ROMAN_MIX, "simran_enhi_companion", "hi-IN"),
    bulbul("codemix", "b-en-voice", MIXED, "simran_en_conversation", "en-IN"),
    bulbul("codemix", "ebitda-hi", "Kal की board meeting में CFO ने Q3 का EBITDA review किया।", "simran_hi_conversation", "hi-IN"),
    bulbul("codemix", "ebitda-enhi", "Kal की board meeting में CFO ने Q3 का EBITDA review किया।", "simran_enhi_companion", "hi-IN"),
    narr("codemix", "intro2", "Code-mixing. India बोलता है Hinglish. हर शब्द पर reader को decide करना पड़ता है: Hindi rules या English rules. "
         "जो reader सिर्फ़ एक language जानता है, वो आधा sentence गलत बोलेगा। सुनिए।", NARR_ENHI),

    # ---- Heteronyms (new) ----
    narr("heteronyms", "intro", "Same spelling, two sounds. Read can be reed or red. Record can be record or record. "
         "Letters alone cannot decide; I have to work out the grammar of the whole sentence. Each clip says one spelling two ways."),
    narr("heteronyms", "outro", "Hindi in Devanagari almost never has this problem. English has hundreds of these words."),
    bulbul("heteronyms", "read", "I read it yesterday, and I will read it again tomorrow.", "simran_en_conversation", "en-IN"),
    bulbul("heteronyms", "record", "Please record the record before the shop closes.", "simran_en_conversation", "en-IN"),
    bulbul("heteronyms", "wind", "The wind was so strong that I had to wind the window shut.", "simran_en_conversation", "en-IN"),

    # ---- Schwa deletion (new, Kokoro only) ----
    C("schwa", "dropped", "kokoro", "कमला ने नमकीन खरीदा।", "hf_alpha", "h", phonemes="kˈʌmlaː neː nəmkˈiːn kʰəɾˈiːdaː"),
    C("schwa", "kept", "kokoro", "कमला ने नमकीन खरीदा।", "hf_alpha", "h", phonemes="kˈʌməlaː neː nəməkˈiːnə kʰəɾˈiːdaː"),

    # ---- Names (new): probe which ones Bulbul gets wrong ----
    bulbul("names", "probe", "Zerodha, Swiggy Instamart, CRED, Meesho, aur Sarvam.", "simran_hi_conversation", "hi-IN"),
    C("names", "as-written", "openai", "Your flight from Thiruvananthapuram to Visakhapatnam is on time.", "alloy", model="tts-1"),
    C("names", "respelled", "openai", "Your flight from Thiru-vanan-tha-puram to Vi-shaa-kha-patnam is on time.", "alloy", model="tts-1"),
    C("names", "k-as-written", "kokoro", "Your flight from Thiruvananthapuram to Visakhapatnam is on time.", "af_heart", "a"),

    # ---- Pauses and melody ----
    narr("punctuation", "intro2", "Pauses and melody. I have no pause tags. Punctuation is how you steer my pauses and my pitch. "
         "Move one comma and the meaning flips. Change a full stop to a question mark and the end of the sentence should rise."),
    bulbul("punctuation", "ruko-a", "रुको, मत जाओ।", "simran_hi_conversation", "hi-IN"),
    bulbul("punctuation", "ruko-b", "रुको मत, जाओ।", "simran_hi_conversation", "hi-IN"),
    bulbul("punctuation", "statement", "आप कल आ रहे हैं।", "simran_hi_conversation", "hi-IN"),
    bulbul("punctuation", "question", "आप कल आ रहे हैं?", "simran_hi_conversation", "hi-IN"),

    # ---- Emphasis (new, OpenAI only) ----
    *[C("emphasis", w, "openai", STOLE, "coral", model="gpt-4o-mini-tts",
        instructions=f'Say this calmly. Put strong, clear contrastive stress on the word "{w}", as if correcting someone. '
                     "No stress on any other word.") for w in ("she", "say", "stole")],
    *[C("emphasis", f"{w}-caps", "openai", STOLE.replace(f" {w} ", f" {w.upper()} "), "coral", model="gpt-4o-mini-tts",
        instructions=f'Say this calmly. Put strong, clear contrastive stress on the word "{w}", as if correcting someone. '
                     "No stress on any other word.") for w in ("she", "say", "stole")],

    # ---- Duration ----
    narr("pace", "intro2", "Duration. Inside the model, every sound gets a predicted length. The pace setting scales those lengths, "
         "from half speed to double. Because the model re-plans the speech, fast speech stays clear. "
         "Compare it with a recording simply played twice as fast."),
    narr("pace", "outro2", "A sped-up recording squeezes everything equally. A model speaking fast chooses what to shorten."),
    bulbul("pace", "p05", STATION, "simran_hi_narration", "hi-IN", 0.5),
    bulbul("pace", "p20", STATION, "simran_hi_narration", "hi-IN", 2.0),

    # ---- Speaker and style ----
    narr("styles", "intro2", "Speaker and style. A voice has two parts: who is speaking, and how. "
         "One speaker, Ratan, in four styles: sports, late-night radio, devotional and documentary. "
         "The words stay the same. Only the delivery changes."),
    *[bulbul("styles", f"ratan-{s}", MATCH, f"ratan_hi_{s}", "hi-IN") for s in ("sports", "latenight", "devotional", "documentary")],
    *[bulbul("styles", f"wide-{v}", MATCH, v, "hi-IN") for v in ("chhavi_hi_kids", "mukul_hi_suspense", "mani_hi_devotional")],
    *[C("styles", f"oa-{n}", "openai", MATCH_EN, "coral", model="gpt-4o-mini-tts", instructions=i) for n, i in [
        ("whisper", "Whisper, very softly, as if in a library."),
        ("commentator", "Shout like an ecstatic cricket commentator after a last-ball six. Very loud, very fast, high pitch."),
        ("bored", "Completely bored and flat. Monotone, slow, a small sigh before speaking."),
        ("upset", 'On the verge of tears. Voice shaking, slow, breaking on "late".'),
        ("angry", "Angry and clipped, every word bitten off."),
    ]],

    # ---- Limits ----
    narr("limits", "intro2", "Limits. Laughs, sighs and whispers are not words. A model needs a separate way to make them: "
         "a tag or an instruction. I am Bulbul V4 Flash, and I have neither. Listen to what happens when you type them."),
    narr("limits", "outro2", "Expression comes from choosing a voice, not from the text. Emotion in speech is still an open problem."),
    bulbul("limits", "whisper-tag", "(whispers) Come closer, I have a secret.", "simran_en_conversation", "en-IN"),
    bulbul("limits", "sigh-tag", "[sighs] I am so tired today.", "simran_en_conversation", "en-IN"),
    bulbul("limits", "dramatic", "Come closer, I have a secret.", "shubh_hi_stories_dramatic", "hi-IN"),
    C("limits", "cartesia-laugh", "cartesia", "[laughter] That was so funny.", "", model="sonic-3"),
    C("limits", "openai-laugh", "openai", "Haha! That was so funny.", "coral", model="gpt-4o-mini-tts",
      instructions="Burst out laughing for a moment first, then say the line still giggling."),
]

assert len({(c.slide, c.name) for c in CLIPS}) == len(CLIPS), "duplicate slide/name"
