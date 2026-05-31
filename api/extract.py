from http.server import BaseHTTPRequestHandler
import json
from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import re
from urllib.parse import parse_qs, urlparse
from youtube_transcript_api import YouTubeTranscriptApi
app = Flask(__name__)
api = YouTubeTranscriptApi()
ALL_LANGS = ["hi", "en", "es", "fr", "de", "pt", "ja", "ko", "zh", "ar", "ru",
             "it", "bn", "ta", "te", "mr", "gu", "kn", "ml", "pa", "ur"]
LANGS = ["hi","en","es","fr","de","pt","ja","ko","zh","ar","ru","it","bn","ta","te","mr","gu","kn","ml","pa","ur"]
def extract_video_id(url):
    for p in [r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})",
              r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
              r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
              r"(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
def vid_id(url):
    for p in [r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})", r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
              r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})", r"(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
              r"^([a-zA-Z0-9_-]{11})$"]:
        m = re.search(p, url)
        if m: return m.group(1)
    return None
def fmt_time(sec):
    h, m, s = int(sec // 3600), int((sec % 3600) // 60), int(sec % 60)
def fmt(sec):
    h,m,s = int(sec//3600), int((sec%3600)//60), int(sec%60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
def fmt_srt(sec):
    h, m, s = int(sec // 3600), int((sec % 3600) // 60), int(sec % 60)
def srt_t(sec):
    h,m,s = int(sec//3600), int((sec%3600)//60), int(sec%60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp
class handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json; charset=utf-8")
@app.route("/api/extract", methods=["GET","POST","OPTIONS"])
def extract():
    if request.method == "OPTIONS":
        return cors(jsonify({}))
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        url = data.get("url","").strip()
        lang = data.get("lang","").strip()
    else:
        url = request.args.get("url","").strip()
        lang = request.args.get("lang","").strip()
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        url = params.get("url", [""])[0]
        lang = params.get("lang", [""])[0]
        if not url:
            return self._send(200, {"status": "ok", "message": "SA Transcript API. ?url=YOUTUBE_URL"})
        self._process(url, lang)
    if not url:
        return cors(jsonify({"status":"ok","message":"SA Transcript API. Send ?url=YOUTUBE_URL"}))
    def do_POST(self):
    v = vid_id(url)
    if not v:
        return cors(jsonify({"error":"Invalid YouTube URL."})), 400
    try:
        langs = ([lang]+[l for l in LANGS if l!=lang]) if lang else LANGS
        try:
            body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
            data = json.loads(body) if body else {}
        except: data = {}
        self._process(data.get("url", ""), data.get("lang", ""))
            raw = api.fetch(v, languages=langs)
        except:
            tl = api.list(v)
            raw = None
            for t in tl:
                raw = t.fetch()
                break
    def _process(self, url, lang):
        if not url: return self._send(400, {"error": "YouTube URL is required."})
        vid = extract_video_id(url.strip())
        if not vid: return self._send(400, {"error": "Invalid YouTube URL."})
        if not raw:
            return cors(jsonify({"error":"No subtitles found."})), 404
        try:
            langs = ([lang] + [l for l in ALL_LANGS if l != lang]) if lang else ALL_LANGS
            try:
                raw = api.fetch(vid, languages=langs)
            except:
                tlist = api.list(vid)
                raw = None
                for t in tlist:
                    raw = t.fetch()
                    break
        segs = []
        for e in raw:
            txt = (e.text if hasattr(e,"text") else e.get("text","")).strip()
            st = e.start if hasattr(e,"start") else e.get("start",0)
            dur = e.duration if hasattr(e,"duration") else e.get("duration",0)
            if txt:
                segs.append({"timestamp":fmt(st),"offsetMs":round(st*1000),"duration":round(dur*1000),"text":txt})
            if not raw: return self._send(404, {"error": "No subtitles found."})
        if not segs:
            return cors(jsonify({"error":"No subtitles found."})), 404
            segs = []
            for e in raw:
                txt = (e.text if hasattr(e, "text") else e.get("text", "")).strip()
                st = e.start if hasattr(e, "start") else e.get("start", 0)
                dur = e.duration if hasattr(e, "duration") else e.get("duration", 0)
                if txt:
                    segs.append({"timestamp": fmt_time(st), "offsetMs": round(st*1000),
                                 "duration": round(dur*1000), "text": txt})
        full = " ".join(s["text"] for s in segs)
        srt_lines = []
        for i,s in enumerate(segs):
            st = s["offsetMs"]/1000
            srt_lines.append(f"{i+1}\n{srt_t(st)} --> {srt_t(st+s['duration']/1000)}\n{s['text']}\n")
        srt = "\n".join(srt_lines)
            if not segs: return self._send(404, {"error": "No subtitles found."})
        return cors(jsonify({"videoId":v,"segmentCount":len(segs),"segments":segs,"fullText":full,"srt":srt}))
            full = " ".join(s["text"] for s in segs)
            srt = "\n".join(f"{i+1}\n{fmt_srt(s['offsetMs']/1000)} --> {fmt_srt(s['offsetMs']/1000+s['duration']/1000)}\n{s['text']}\n"
                            for i, s in enumerate(segs))
    except Exception as e:
        msg = str(e)
        if "disabled" in msg.lower():
            return cors(jsonify({"error":"Subtitles are disabled for this video."})), 403
        return cors(jsonify({"error":f"Failed: {msg[:200]}"})), 500
            self._send(200, {"videoId": vid, "segmentCount": len(segs),
                             "segments": segs, "fullText": full, "srt": srt})
        except Exception as e:
            msg = str(e)
            if "disabled" in msg.lower(): return self._send(403, {"error": "Subtitles are disabled."})
            self._send(500, {"error": f"Failed: {msg[:200]}"})
    def _send(self, code, data):
        self.send_response(code)
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
