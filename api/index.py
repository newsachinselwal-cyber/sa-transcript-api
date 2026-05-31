from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import re, os
app = Flask(__name__)
api = YouTubeTranscriptApi()
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
@app.route("/api/index", methods=["GET","POST","OPTIONS"])
@app.route("/", methods=["GET"])
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
        # Step 1: List all available transcripts
        transcript_list = api.list(v)
        # Step 2: Collect available languages info
        available = []
        for t in transcript_list:
            available.append({
                "code": t.language_code,
                "name": t.language,
                "isGenerated": t.is_generated,
            })
        # Step 3: Pick the right transcript
        chosen = None
        chosen_info = {}
        if lang:
            # User specified a language
            try:
                chosen = transcript_list.find_transcript([lang]).fetch()
                chosen_info = {"code": lang, "isGenerated": False}
            except:
                pass
        if not chosen:
            # Auto-detect: prefer manual (original) over auto-generated
            # Manual transcripts = uploaded by creator = original language
            manual = [t for t in transcript_list if not t.is_generated]
            generated = [t for t in transcript_list if t.is_generated]
            if manual:
                # Manual transcript = original language
                t = manual[0]
                chosen = t.fetch()
                chosen_info = {"code": t.language_code, "name": t.language, "isGenerated": False}
            elif generated:
                # Auto-generated = YouTube's speech recognition
                t = generated[0]
                chosen = t.fetch()
                chosen_info = {"code": t.language_code, "name": t.language, "isGenerated": True}
        if not chosen:
            return cors(jsonify({"error":"No subtitles found."})), 404
        # Step 4: Build response
        segs = []
        for e in chosen:
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
        return cors(jsonify({
            "videoId": v,
            "language": chosen_info,
            "availableLanguages": available,
            "segmentCount": len(segs),
            "segments": segs,
            "fullText": full,
            "srt": srt,
        }))
    except Exception as e:
        msg = str(e)
        if "disabled" in msg.lower() or "TranscriptsDisabled" in msg:
            return cors(jsonify({"error":"Subtitles are disabled for this video."})), 403
        if "blocking" in msg.lower() or "IpBlocked" in msg or "RequestBlocked" in msg:
            return cors(jsonify({"error":"YouTube is temporarily blocking requests. Please try again later."})), 429
        return cors(jsonify({"error":f"Failed: {msg[:200]}"})), 500
