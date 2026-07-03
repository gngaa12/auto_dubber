# Cross-Language Auto-Dubber (100% Free)

Paste in any video link (TikTok, RedNote, YouTube, etc.) and get it back
auto-dubbed into another language and posted to your Facebook Page —
using only free, open-source tools.

## How it works
1. **yt-dlp** downloads the video from the link you give it.
2. **ffmpeg** pulls out the audio track.
3. **faster-whisper** (free, open-source, runs locally) transcribes the
   speech to text.
4. **deep-translator** (free, no API key) translates that text into your
   target language.
5. **edge-tts** (free, uses Microsoft's natural-sounding voices) turns the
   translated text into a new audio track.
6. **ffmpeg** merges the new audio onto the original video.
7. **Facebook Graph API** uploads the finished dub to your Page (reuses
   the same Page token setup from the TikTok-to-Facebook project).

## Setup

This reuses the **same Facebook secrets** from your TikTok-to-Facebook
project. If you're adding this to a **new** repo, redo those steps from
that project's README (Page token + Page ID as `FB_PAGE_ID` and
`FB_PAGE_ACCESS_TOKEN` secrets). If you're adding this to the **same**
repo, you can skip straight to usage — the secrets are already there.

1. Add these files to your repo:
   ```
   .github/workflows/auto_dubber.yml
   scripts/dub.py
   requirements.txt   (this one has different packages — use the version
                        in this folder, not the TikTok one)
   ```

2. If this is a fresh repo, make sure `FB_PAGE_ID` and
   `FB_PAGE_ACCESS_TOKEN` secrets are set (Settings → Secrets and
   variables → Actions).

## Usage

1. Go to the **Actions** tab → **Auto Dubber** → **Run workflow**.
2. Fill in:
   - **video_url**: paste the link to the video you want dubbed
   - **target_lang**: language code, e.g. `en`, `hi`, `es`, `fr`, `de`,
     `zh`, `ja`, `ar`, `pt`, `ru`
3. Click **Run workflow**.
4. This takes a few minutes (downloading the Whisper model the first
   time adds ~1-2 min). Watch progress under the running job.
5. When it finishes:
   - Check your Facebook Page — the dubbed video should be posted.
   - There's also a downloadable **artifact** attached to the run
     (bottom of the run summary page) with the dubbed video file, so you
     can preview it even if the Facebook upload step has an issue.

## Notes & limits

- **First run is slower** — downloading the Whisper speech-recognition
  model happens once per run (GitHub Actions doesn't cache it by
  default), adding a minute or two.
- **Video/audio length mismatch**: if the translated sentence is longer
  or shorter than the original speech, the dubbed audio and video length
  might not perfectly match. The script uses ffmpeg's `-shortest` flag,
  so extra video or audio gets trimmed rather than looping. Fine for
  short clips; noticeable on longer ones.
- **Translation quality**: deep-translator uses Google's translation
  under the hood — good for most everyday speech, not perfect for
  slang/idioms.
- **RedNote specifically**: RedNote's video pages are known to be
  unreliable for yt-dlp (they change their site protections often). If a
  RedNote link fails, that's expected sometimes — try a different link,
  or wait and retry, or use a TikTok/YouTube link instead while RedNote
  support catches up.
- **Cost**: $0. Everything here is open-source or has a generous free
  tier used well within its limits for occasional runs.
