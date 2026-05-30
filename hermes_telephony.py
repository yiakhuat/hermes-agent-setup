"""
hermes_telephony.py
Victor's Assistant — Telephony Agent
Simple, robust bilingual English/Chinese support
Flow: Greeting → Language Select → Q&A Loop → Goodbye
"""

import re
import subprocess
from pathlib import Path
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather

app = Flask(__name__)

HERMES_CMD = "/usr/local/bin/hermes"
VOICE_EN   = "Polly.Joanna"
VOICE_ZH   = "Polly.Zhiyu"
LANG_EN    = "en-US"
LANG_ZH    = "cmn-CN"
STT_EN     = "en-US"
STT_ZH     = "zh-CN"


# ── Hermes ─────────────────────────────────────────────

def ask_hermes(question: str, lang: str) -> str:
    """Ask Hermes a question. Force Chinese reply if lang=zh."""
    try:
        if lang == "zh":
            prompt = f"请务必只用中文回答，不要用英文回答。问题是：{question}"
        else:
            prompt = question

        result = subprocess.run(
            [HERMES_CMD, "chat", "-q", prompt, "-Q"],
            capture_output=True, text=True, timeout=25,
        )
        text = result.stdout.strip()

        # Clean up metadata
        for marker in ["Session:", "Resume this session", "Duration:", "Messages:"]:
            if marker in text:
                text = text.split(marker)[0].strip()

        # Clean ANSI codes
        text = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', text)
        text = re.sub(r'\x1b\].*?(\x07|\x1b\\)', '', text)
        text = text.strip()

        if not text:
            return "对不起，请再试一次。" if lang == "zh" else "Sorry, please try again."

        return text[:450]

    except subprocess.TimeoutExpired:
        return "问题太复杂了，请简短一点。" if lang == "zh" else "That took too long, please ask something shorter."
    except Exception as e:
        print(f"[Hermes error] {e}")
        return "系统错误，请再试。" if lang == "zh" else "System error, please try again."


# ── Helper ─────────────────────────────────────────────

def say(response, text, lang):
    """Speak text in correct language."""
    if lang == "zh":
        response.say(text, voice=VOICE_ZH, language=LANG_ZH)
    else:
        response.say(text, voice=VOICE_EN, language=LANG_EN)


def listen(action, lang, prompt_text):
    """Build a Gather that listens in correct language."""
    stt_lang = STT_ZH if lang == "zh" else STT_EN
    voice    = VOICE_ZH if lang == "zh" else VOICE_EN
    tts_lang = LANG_ZH if lang == "zh" else LANG_EN

    gather = Gather(
        input="speech",
        action=action,
        timeout=8,
        speech_timeout="auto",
        language=stt_lang,
    )
    gather.say(prompt_text, voice=voice, language=tts_lang)
    return gather


# ── Routes ─────────────────────────────────────────────

@app.route("/voice/incoming", methods=["GET", "POST"])
def incoming_call():
    """Step 1: Greet and ask caller to choose language."""
    response = VoiceResponse()

    gather = Gather(
        input="dtmf",
        action="/voice/set_language",
        timeout=8,
        num_digits=1,
    )
    gather.say(
        "Hello! You have reached Victor's Assistant. Press 1 for English. "
        "你好！这里是Victor的智能助手。按2说中文。",
        voice=VOICE_EN,
        language=LANG_EN,
    )
    response.append(gather)

    # No key pressed — default English
    response.redirect("/voice/qa/en")
    return Response(str(response), mimetype="text/xml")


@app.route("/voice/set_language", methods=["GET", "POST"])
def set_language():
    """Step 2: Set language and go to Q&A."""
    digit = request.values.get("Digits", "1").strip()
    print(f"[Telephony] Key pressed: '{digit}'")
    response = VoiceResponse()
    lang = "zh" if digit == "2" else "en"
    response.redirect(f"/voice/qa/{lang}")
    return Response(str(response), mimetype="text/xml")


@app.route("/voice/qa/<lang>", methods=["GET", "POST"])
def qa(lang):
    """Step 3: Ask caller for their question."""
    response = VoiceResponse()

    if lang == "zh":
        prompt = "请说出您的问题。"
        no_speech_msg = "我没有听到您说话。请再次拨打。再见！"
    else:
        prompt = "Please speak your question now."
        no_speech_msg = "I did not hear anything. Please call back. Goodbye!"

    gather = listen(
        action=f"/voice/answer/{lang}",
        lang=lang,
        prompt_text=prompt,
    )
    response.append(gather)

    # Truly no speech at all — say goodbye and hang up
    say(response, no_speech_msg, lang)
    response.hangup()
    return Response(str(response), mimetype="text/xml")


@app.route("/voice/answer/<lang>", methods=["GET", "POST"])
def answer(lang):
    """Step 4: Get Hermes answer and speak it. Then loop back for more questions."""
    speech = request.values.get("SpeechResult", "").strip()
    print(f"[Telephony] [{lang}] Question: '{speech}'")

    response = VoiceResponse()

    # Nothing transcribed — retry once
    if not speech:
        if lang == "zh":
            response.say("对不起，我没有听清楚。", voice=VOICE_ZH, language=LANG_ZH)
        else:
            response.say("Sorry, I did not catch that.", voice=VOICE_EN, language=LANG_EN)
        response.redirect(f"/voice/qa/{lang}")
        return Response(str(response), mimetype="text/xml")

    # Get Hermes response
    hermes_reply = ask_hermes(speech, lang)
    print(f"[Telephony] [{lang}] Hermes reply: {hermes_reply[:120]}")

    # Speak the answer
    say(response, hermes_reply, lang)

    # Loop — ask if they have another question
    if lang == "zh":
        follow_up = "您还有其他问题吗？请说出来。"
        goodbye   = "感谢您拨打Victor的智能助手。再见！"
    else:
        follow_up = "Do you have another question? Please speak now."
        goodbye   = "Thank you for calling Victor's Assistant. Goodbye!"

    gather = listen(
        action=f"/voice/answer/{lang}",
        lang=lang,
        prompt_text=follow_up,
    )
    response.append(gather)

    # No follow-up question — say goodbye
    say(response, goodbye, lang)
    response.hangup()
    return Response(str(response), mimetype="text/xml")


@app.route("/voice/status", methods=["GET", "POST"])
def call_status():
    status  = request.values.get("CallStatus", "unknown")
    call_id = request.values.get("CallSid", "unknown")
    print(f"[Telephony] Call {call_id}: {status}")
    return Response("OK", status=200)


@app.route("/health")
def health():
    return {"status": "ok", "service": "Victor's Assistant Telephony Agent"}


if __name__ == "__main__":
    print("📞 Victor's Assistant — port 5001")
    print("Press 1 = English | Press 2 = 中文")
    app.run(host="0.0.0.0", port=5001, debug=False)
