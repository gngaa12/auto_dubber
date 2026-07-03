#!/usr/bin/env python3
"""
Cross-language Auto-Dubber
Free stack:
  - yt-dlp        -> download the source video (any platform it supports)
  - ffmpeg        -> extract audio / merge new audio back onto the video
  - faster-whisper -> free open-source speech-to-text (runs locally, no API key)
  - deep-translator -> free translation (no API key)
  - edge-tts      -> free text-to-speech using Microsoft's voices (no API key)
  - Facebook Graph API -> upload the finished dub

Triggered manually with two inputs:
  VIDEO_URL    the link to the source video (TikTok, RedNote, YouTube, etc.)
  TARGET_LANG  language code to dub into, e.g. "en", "hi", "es"

Env vars required (GitHub Actions secrets):
  FB_PAGE_ID
  FB_PAGE_ACCESS_TOKEN
"""

import asyncio
import os
import subprocess
import sys

import requests
from deep_translator import GoogleTranslator
import edge_tts
from faster_whisper import WhisperModel

VIDEO_URL = os.environ["VIDEO_URL"]
TARGET_LANG = os.environ.get("TARGET_LANG", "en")
FB_PAGE_ID = os.environ["FB_PAGE_ID"]
FB_PAGE_TOKEN = os.environ["FB_PAGE_ACCESS_TOKEN"]
GRAPH_VERSION = "v19.0"

WORKDIR = "work"
ORIGINAL_VIDEO = f"{WORKDIR}/original.mp4"
AUDIO_WAV = f"{WORKDIR}/audio.wav"
DUB_AUDIO = f"{WORKDIR}/dub_audio.mp3"
OUTPUT_VIDEO = f"{WORKDIR}/dubbed_output.mp4"

# A few common voices; falls back to English if the language isn't listed
VOICE_MAP = {
    "en": "en-US-AriaNeural",
    "hi": "hi-IN-SwaraNeural",
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "ar": "ar-SA-ZariyahNeural",
    "pt": "pt-BR-FranciscaNeural",
    "ru": "ru-RU-SvetlanaNeural",
}


def run(cmd):
    print("RUN:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def download_video():
    os.makedirs(WORKDIR, exist_ok=True)
    run(["yt-dlp", "-f", "mp4", "-o", ORIGINAL_VIDEO, VIDEO_URL])


def extract_audio():
    run([
        "ffmpeg", "-y", "-i", ORIGINAL_VIDEO,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        AUDIO_WAV,
    ])


def transcribe_audio():
    print("Loading Whisper model (first run downloads it, ~150MB)...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, info = model.transcribe(AUDIO_WAV)
    text = " ".join(seg.text.strip() for seg in segments)
    print(f"Detected source language: {info.language}")
    print(f"Transcript: {text}")
    return text


def translate_text(text):
    translated = GoogleTranslator(source="auto", target=TARGET_LANG).translate(text)
    print(f"Translated ({TARGET_LANG}): {translated}")
    return translated


async def synthesize_speech(text):
    voice = VOICE_MAP.get(TARGET_LANG, "en-US-AriaNeural")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(DUB_AUDIO)


def merge_audio_video():
    run([
        "ffmpeg", "-y",
        "-i", ORIGINAL_VIDEO,
        "-i", DUB_AUDIO,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac",
        "-shortest",
        OUTPUT_VIDEO,
    ])


def upload_to_facebook(caption):
    url = f"https://graph-video.facebook.com/{GRAPH_VERSION}/{FB_PAGE_ID}/videos"
    params = {"access_token": FB_PAGE_TOKEN}
    with open(OUTPUT_VIDEO, "rb") as f:
        resp = requests.post(
            url,
            params=params,
            data={"description": caption},
            files={"source": f},
            timeout=600,
        )
    if resp.status_code != 200:
        print("FACEBOOK ERROR DETAILS:", resp.text)
    resp.raise_for_status()
    print("Facebook response:", resp.json())


def main():
    print(f"=== Dubbing {VIDEO_URL} into '{TARGET_LANG}' ===")
    download_video()
    extract_audio()
    original_text = transcribe_audio()
    if not original_text.strip():
        print("No speech detected in video. Nothing to dub.", file=sys.stderr)
        sys.exit(1)
    translated_text = translate_text(original_text)
    asyncio.run(synthesize_speech(translated_text))
    merge_audio_video()
    upload_to_facebook(translated_text[:500])
    print("=== Done! Dubbed video posted to Facebook. ===")


if __name__ == "__main__":
    main()
