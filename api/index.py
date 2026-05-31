from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import re
app = Flask(__name__)
api = YouTubeTranscriptApi()
LANGS = ["hi","en","es","fr","de","pt","ja","ko","zh","ar","ru","it","bn","ta","te","mr","gu","kn","ml","pa","ur"]
def vid_id(url):
    for p in [r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})", r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
              r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})", r"(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
              r"^([a-zA-Z0-9_-]{11})$"]:
        m = re.search(p, url)
        if m: return m.group(1)
    return None
def fmt(sec):
    h,m,s = int(sec//3600), int((sec%3600)//60), int(sec%60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
def srt_t(sec):
    h,m,s = int(sec//3600), int((sec%3600)//60), int(sec%60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp
@app.route("/api/extract", methods=["GET","POST","OPTIONS"])
def extract():
    if request.method == "OPTIONS":
        return cors(jsonify({}))
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        url = data.get("url","").strip()
        lang = data.get("lang","").strip()
    else:
        url = request.args.get("url","").strip()
        lang = request.args.get("lang","").strip()
    if not url:
        return cors(jsonify({"status":"ok","message":"SA Transcript API. Send ?url=YOUTUBE_URL"}))
    v = vid_id(url)
    if not v:
        return cors(jsonify({"error":"Invalid YouTube URL."})), 400
    try:
        langs = ([lang]+[l for l in LANGS if l!=lang]) if lang else LANGS
        try:
            raw = api.fetch(v, languages=langs)
        except:
            tl = api.list(v)
            raw = None
            for t in tl:
                raw = t.fetch()
                break
        if not raw:
            return cors(jsonify({"error":"No subtitles found."})), 404
        segs = []
        for e in raw:
            txt = (e.text if hasattr(e,"text") else e.get("text","")).strip()
            st = e.start if hasattr(e,"start") else e.get("start",0)
            dur = e.duration if hasattr(e,"duration") else e.get("duration",0)
            if txt:
                segs.append({"timestamp":fmt(st),"offsetMs":round(st*1000),"duration":round(dur*1000),"text":txt})
        if not segs:
            return cors(jsonify({"error":"No subtitles found."})), 404
        full = " ".join(s["text"] for s in segs)
        srt_lines = []
        for i,s in enumerate(segs):
            st = s["offsetMs"]/1000
            srt_lines.append(f"{i+1}\n{srt_t(st)} --> {srt_t(st+s['duration']/1000)}\n{s['text']}\n")
        srt = "\n".join(srt_lines)
        return cors(jsonify({"videoId":v,"segmentCount":len(segs),"segments":segs,"fullText":full,"srt":srt}))
    except Exception as e:
        msg = str(e)
        if "disabled" in msg.lower():
            return cors(jsonify({"error":"Subtitles are disabled for this video."})), 403
        return cors(jsonify({"error":f"Failed: {msg[:200]}"})), 500
