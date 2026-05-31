from http.server import BaseHTTPRequestHandler
import json
import re
from urllib.parse import parse_qs, urlparse
from youtube_transcript_api import YouTubeTranscriptApi
api = YouTubeTranscriptApi()
ALL_LANGS = ["hi", "en", "es", "fr", "de", "pt", "ja", "ko", "zh", "ar", "ru",
             "it", "bn", "ta", "te", "mr", "gu", "kn", "ml", "pa", "ur"]
def extract_video_id(url):
    patterns = [
        r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for p in patterns:
    for p in [r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})",
              r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
              r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
              r"(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
              r"^([a-zA-Z0-9_-]{11})$"]:
        m = re.search(p, url)
        if m:
            return m.group(1)
        if m: return m.group(1)
    return None
def fmt_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
    h, m, s = int(sec // 3600), int((sec % 3600) // 60), int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
def fmt_srt(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    h, m, s = int(sec // 3600), int((sec % 3600) // 60), int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json; charset=utf-8",
    }
class handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json; charset=utf-8")
class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        for k, v in cors_headers().items():
            self.send_header(k, v)
        self._cors()
        self.end_headers()
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        params = parse_qs(urlparse(self.path).query)
        url = params.get("url", [""])[0]
        lang = params.get("lang", [""])[0]
        if not url:
            self.respond(200, {"status": "running", "message": "SA Transcript API. Send ?url=YOUTUBE_URL"})
            return
            return self._send(200, {"status": "ok", "message": "SA Transcript API. ?url=YOUTUBE_URL"})
        self._process(url, lang)
        self.process(url, lang)
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length else ""
        try:
            body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
            data = json.loads(body) if body else {}
        except:
            data = {}
        url = data.get("url", "")
        lang = data.get("lang", "")
        if not url:
            self.respond(400, {"error": "YouTube URL is required."})
            return
        self.process(url, lang)
        except: data = {}
        self._process(data.get("url", ""), data.get("lang", ""))
    def process(self, url, lang):
        video_id = extract_video_id(url.strip())
        if not video_id:
            self.respond(400, {"error": "Invalid YouTube URL."})
            return
    def _process(self, url, lang):
        if not url: return self._send(400, {"error": "YouTube URL is required."})
        vid = extract_video_id(url.strip())
        if not vid: return self._send(400, {"error": "Invalid YouTube URL."})
        try:
            # Build language list
            if lang:
                languages = [lang] + [l for l in ALL_LANGS if l != lang]
            else:
                languages = ALL_LANGS
            # Try fetching
            langs = ([lang] + [l for l in ALL_LANGS if l != lang]) if lang else ALL_LANGS
            try:
                raw = api.fetch(video_id, languages=languages)
            except Exception:
                # Fallback: get any available language
                try:
                    transcript_list = api.list(video_id)
                    raw = None
                    for t in transcript_list:
                        raw = t.fetch()
                        break
                except:
                    raw = None
                raw = api.fetch(vid, languages=langs)
            except:
                tlist = api.list(vid)
                raw = None
                for t in tlist:
                    raw = t.fetch()
                    break
            if not raw:
                self.respond(404, {"error": "No subtitles found for this video."})
                return
            if not raw: return self._send(404, {"error": "No subtitles found."})
            segments = []
            for entry in raw:
                text = entry.text.strip() if hasattr(entry, "text") else str(entry.get("text", "")).strip()
                start = entry.start if hasattr(entry, "start") else entry.get("start", 0)
                dur = entry.duration if hasattr(entry, "duration") else entry.get("duration", 0)
                if text:
                    segments.append({
                        "timestamp": fmt_time(start),
                        "offsetMs": round(start * 1000),
                        "duration": round(dur * 1000),
                        "text": text,
                    })
            segs = []
            for e in raw:
                txt = (e.text if hasattr(e, "text") else e.get("text", "")).strip()
                st = e.start if hasattr(e, "start") else e.get("start", 0)
                dur = e.duration if hasattr(e, "duration") else e.get("duration", 0)
                if txt:
                    segs.append({"timestamp": fmt_time(st), "offsetMs": round(st*1000),
                                 "duration": round(dur*1000), "text": txt})
            if not segments:
                self.respond(404, {"error": "No subtitles found."})
                return
            if not segs: return self._send(404, {"error": "No subtitles found."})
            full_text = " ".join(s["text"] for s in segments)
            srt_lines = []
            for i, s in enumerate(segments):
                st = s["offsetMs"] / 1000
                end_t = st + s["duration"] / 1000
                srt_lines.append(f"{i + 1}\n{fmt_srt(st)} --> {fmt_srt(end_t)}\n{s['text']}\n")
            full = " ".join(s["text"] for s in segs)
            srt = "\n".join(f"{i+1}\n{fmt_srt(s['offsetMs']/1000)} --> {fmt_srt(s['offsetMs']/1000+s['duration']/1000)}\n{s['text']}\n"
                            for i, s in enumerate(segs))
            self.respond(200, {
                "videoId": video_id,
                "segmentCount": len(segments),
                "segments": segments,
                "fullText": full_text,
                "srt": "\n".join(srt_lines),
            })
            self._send(200, {"videoId": vid, "segmentCount": len(segs),
                             "segments": segs, "fullText": full, "srt": srt})
        except Exception as e:
            err_msg = str(e)
            if "disabled" in err_msg.lower():
                self.respond(403, {"error": "Subtitles are disabled for this video."})
            elif "unavailable" in err_msg.lower():
                self.respond(404, {"error": "Video is unavailable or private."})
            else:
                self.respond(500, {"error": f"Failed to extract subtitles: {err_msg[:200]}"})
            msg = str(e)
            if "disabled" in msg.lower(): return self._send(403, {"error": "Subtitles are disabled."})
            self._send(500, {"error": f"Failed: {msg[:200]}"})
    def respond(self, status, data):
        self.send_response(status)
        for k, v in cors_headers().items():
            self.send_header(k, v)
    def _send(self, code, data):
        self.send_response(code)
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
