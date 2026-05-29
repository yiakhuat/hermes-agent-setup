"""
hermes_telephony.py
Hermes Telephony Agent - Handles incoming Twilio voice calls
Connects callers to Hermes AI agent with speech-to-text and text-to-speech

Run: /root/hermes-venv/bin/python3 hermes_telephony.py
"""

import os
import subprocess
import tempfile
import asyncio
import edge_tts
from pathlib import Path
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather

app = Flask(__name__)

# ── Config ─────────────────────────────────────────────
HERMES_CMD     = "/usr/local/bin/hermes"
AUDIO_DIR      = Path("/root/.hermes/audio_cache")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Greeting message
GREETING_EN = "Hello! You've reached Hermes AI Assistant. Please speak your question after the tone."
GREETING_ZH = "你好！这里是Hermes AI助手。请在提示音后说出您的问题。"

# TTS voices
VOICE_EN = "en-US-AriaNeural"
VOICE_ZH = "zh-CN-XiaoxiaoNeural"


# ── TTS Helper ─────────────────────────────────────────

async def text_to_speech_async(text: str, voice: str, output_path: str):
    """Convert text to speech using Edge TTS."""
    tts = edge_tts.Communicate(text, voice)
    await tts.save(output_path)


def text_to_speech(text: str, lang: str = "en") -> str:
    """Generate TTS audio and return file path."""
    voice = VOICE_ZH if lang == "zh" else VOICE_EN
    output_path = str(AUDIO_DIR / f"call_tts_{os.urandom(6).hex()}.mp3")
    asyncio.run(text_to_speech_async(text, voice, output_path))
    return output_path


def detect_language(text: str) -> str:
    """Simple language detection - check for Chinese characters."""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return "zh"
    return "en"


# ── Hermes Integration ─────────────────────────────────

def ask_hermes(question: str) -> str:
    """Send question to Hermes and get response."""
    try:
        result = subprocess.run(
            [HERMES_CMD, "chat", "-q", question, "-Q"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        response = result.stdout.strip()
        # Clean up session info from output
        if "Session:" in response:
            response = response.split("Session:")[0].strip()
        if "Resume this session" in response:
            response = response.split("Resume this session")[0].strip()
        # Remove ANSI escape codes
        import re
        response = re.sub(r'\x1b\[[0-9;]*m', '', response)
        response = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', response)
        response = re.sub(r'\^\[\[[0-9;]*m', '', response)
        response = response.strip()
        if not response:
            return "I'm sorry, I couldn't process your request. Please try again."
        return response[:500]  # Limit response length for voice
    except subprocess.TimeoutExpired:
        return "I'm sorry, that took too long to process. Please try a shorter question."
    except Exception as e:
        print(f"Hermes error: {e}")
        return "I'm sorry, I encountered an error. Please try again."


# ── Twilio Routes ──────────────────────────────────────

@app.route("/voice/incoming", methods=["GET", "POST"])
def incoming_call():
    """Handle incoming call - greet and start listening."""
    response = VoiceResponse()

    # Gather speech input from caller
    gather = Gather(
        input="speech",
        action="/voice/process",
        timeout=5,
        speech_timeout="auto",
        language="en-US zh-CN",
    )
    gather.say(
        "Hello! You've reached Hermes AI Assistant. "
        "Please speak your question after this message.",
        voice="Polly.Joanna",
        language="en-US",
    )
    response.append(gather)

    # If no input received
    response.say(
        "I didn't hear anything. Please call back and speak your question.",
        voice="Polly.Joanna",
    )
    return Response(str(response), mimetype="text/xml")


@app.route("/voice/process", methods=["GET", "POST"])
def process_speech():
    """Process caller's speech and respond with Hermes answer."""
    speech_result = request.values.get("SpeechResult", "")
    confidence = request.values.get("Confidence", "0")

    print(f"Caller said: '{speech_result}' (confidence: {confidence})")

    response = VoiceResponse()

    if not speech_result:
        response.say(
            "I'm sorry, I couldn't understand that. Please try again.",
            voice="Polly.Joanna",
        )
        response.redirect("/voice/incoming")
        return Response(str(response), mimetype="text/xml")

    # Detect language
    lang = detect_language(speech_result)

    # Get response from Hermes
    print(f"Asking Hermes: {speech_result}")
    hermes_response = ask_hermes(speech_result)
    print(f"Hermes replied: {hermes_response}")

    # Respond using Twilio's built-in TTS
    if lang == "zh":
        response.say(
            hermes_response,
            voice="Polly.Zhiyu",
            language="cmn-CN",
        )
    else:
        response.say(
            hermes_response,
            voice="Polly.Joanna",
            language="en-US",
        )

    # Ask if they want to continue
    gather = Gather(
        input="speech",
        action="/voice/process",
        timeout=5,
        speech_timeout="auto",
        language="en-US zh-CN",
    )
    gather.say(
        "Do you have another question? Please speak now, or hang up to end the call.",
        voice="Polly.Joanna",
    )
    response.append(gather)

    response.say("Thank you for calling Hermes. Goodbye!", voice="Polly.Joanna")
    response.hangup()

    return Response(str(response), mimetype="text/xml")


@app.route("/voice/status", methods=["GET", "POST"])
def call_status():
    """Handle call status callbacks."""
    call_status = request.values.get("CallStatus", "unknown")
    call_sid = request.values.get("CallSid", "unknown")
    print(f"Call {call_sid} status: {call_status}")
    return Response("OK", status=200)


@app.route("/health")
def health():
    return {"status": "ok", "service": "hermes-telephony"}


# ── Entry Point ────────────────────────────────────────

if __name__ == "__main__":
    print("🤖 Hermes Telephony Agent starting on port 5001...")
    print("📞 Waiting for calls...")
    app.run(host="0.0.0.0", port=5001, debug=False)
