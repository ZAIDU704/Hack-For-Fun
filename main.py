import os
import re
import json
import time
import secrets
import shutil
import threading
import subprocess
import urllib.request
from urllib.parse import urlparse
from flask import Flask, request, render_template_string, jsonify, abort

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
PAGES = {}
ROOT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(ROOT, "submissions"), exist_ok=True)

STYLE = """
body{margin:0;padding:24px;min-height:100vh;display:grid;place-items:center;
background:linear-gradient(135deg,#101827,#30204d);color:#f8fafc;
font-family:system-ui,sans-serif}
.card{width:min(100%,620px);padding:32px;box-sizing:border-box;
border:1px solid #ffffff30;border-radius:22px;background:#ffffff10}
.brand{color:#c4b5fd;font-weight:800;letter-spacing:2px}
h1{font-size:clamp(2rem,7vw,3rem)}
button,.button{padding:13px 18px;border:0;border-radius:10px;
background:#c4b5fd;color:#171127;font-weight:800;text-decoration:none;cursor:pointer}
button:disabled{opacity:.5}label{display:block;line-height:1.6;margin:20px 0}
video{width:100%;max-height:300px}small{color:#ddd}
"""

@app.get("/")
def home():
    return f"""<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>{STYLE}</style><main class="card"><p class="brand">HACK FOR FUN</p>
    <h1>Make a moment worth sharing ✨</h1>
    <p>Greeting links made with care.</p><p>Instagram: cybergenius.io</p></main>"""

@app.get("/p/<pid>")
def greeting(pid):
    d = PAGES.get(pid)
    if not d or d["kind"] == "checkin":
        abort(404)
    yt = ""
    if d.get("youtube"):
        yt = f'<p><a class="button" target="_blank" rel="noopener noreferrer" href="{d["youtube"]}">Watch on YouTube</a></p>'
    return f"""<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{d["title"]}</title><style>{STYLE}</style><main class="card">
    <p class="brand">HACK FOR FUN ✨</p><h1>{d["title"]}</h1>
    <p>{d["message"]}</p>{yt}<small>Instagram: cybergenius.io</small></main>"""

@app.get("/check/<pid>")
def checkin(pid):
    if pid not in PAGES or PAGES[pid]["kind"] != "checkin":
        abort(404)
    return render_template_string("""<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>""" + STYLE + """</style><main class="card">
    <p class="brand">HACK FOR FUN · DEVICE CHECK-IN</p><h1>Optional check-in</h1>
    <p>If you continue, this page will take one camera photo and request your current location,
    then send both to the operator of this check-in page. Nothing is collected on page load.
    You may decline by leaving this page.</p>
    <label><input type="checkbox" id="agree"> I understand and agree to submit one photo and my location.</label>
    <button id="start" disabled>Start Check</button><p id="status" role="status">Waiting for your choice.</p>
    <video id="video" autoplay playsinline hidden></video><canvas id="canvas" hidden></canvas>
    <script>
    const agree=document.getElementById('agree'),start=document.getElementById('start');
    const statusEl=document.getElementById('status');
    agree.onchange=()=>start.disabled=!agree.checked;
    start.onclick=async()=>{
      if(!agree.checked)return;
      start.disabled=true;let stream;
      try{
        statusEl.textContent='Requesting camera permission…';
        stream=await navigator.mediaDevices.getUserMedia({video:true,audio:false});
        const v=document.getElementById('video');v.hidden=false;v.srcObject=stream;
        await new Promise(r=>v.onloadedmetadata=r);
        await new Promise(r=>setTimeout(r,700));
        const c=document.getElementById('canvas');c.width=v.videoWidth;c.height=v.videoHeight;
        c.getContext('2d').drawImage(v,0,0);
        statusEl.textContent='Requesting location permission…';
        const pos=await new Promise((resolve,reject)=>
          navigator.geolocation.getCurrentPosition(resolve,reject,{enableHighAccuracy:true,timeout:15000}));
        const blob=await new Promise(resolve=>c.toBlob(resolve,'image/jpeg',0.82));
        const form=new FormData();form.append('consent','yes');
        form.append('latitude',String(pos.coords.latitude));
        form.append('longitude',String(pos.coords.longitude));form.append('photo',blob,'check-in.jpg');
        statusEl.textContent='Submitting your check-in…';
        const res=await fetch('/api/check/""" + pid + """',{method:'POST',body:form});
        const data=await res.json();if(!res.ok)throw Error(data.error||'Submission failed');
        statusEl.textContent=data.message;
      }catch(e){statusEl.textContent='Not completed: '+(e.message||'permission denied');}
      finally{if(stream)stream.getTracks().forEach(t=>t.stop());vCleanup();}
      function vCleanup(){document.getElementById('video').hidden=true;start.disabled=!agree.checked;}
    };
    </script><p><small>Camera and location are requested only after you agree and press Start Check.
    A public HTTPS link is required outside localhost.</small></p></main>""", pid=pid)

@app.post("/api/check/<pid>")
def submit_checkin(pid):
    if pid not in PAGES or PAGES[pid]["kind"] != "checkin":
        abort(404)
    if request.form.get("consent") != "yes":
        return jsonify(error="Consent is required."), 400
    photo = request.files.get("photo")
    if not photo or not photo.mimetype.startswith("image/"):
        return jsonify(error="A photo is required."), 400
    lat = request.form.get("latitude", "")[:32]
    lon = request.form.get("longitude", "")[:32]
    folder = os.path.join(ROOT, "submissions", pid)
    os.makedirs(folder, exist_ok=True)
    sid = secrets.token_hex(8)
    photo.save(os.path.join(folder, sid + ".jpg"))
    with open(os.path.join(folder, sid + ".txt"), "w") as f:
        f.write("Consent: yes\\nUTC: " + time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        f.write("\\nLatitude: " + lat + "\\nLongitude: " + lon + "\\n")
    print("\\n[HACK FOR FUN] Consent-based check-in saved:", folder, flush=True)
    print("Coordinates:", lat, lon, flush=True)
    return jsonify(message="Check-in submitted. You can close this page.")

def valid_youtube(url):
    try:
        u = urlparse(url)
        return u.scheme == "https" and u.hostname in {
            "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"
        }
    except Exception:
        return False

def create_page(kind):
    d = {"kind": kind}
    if kind == "birthday":
        name = input("Person name: ").strip()[:80] or "Friend"
        d.update(title=f"Happy Birthday, {name}!", message=f"Wishing you a wonderful birthday, {name}!")
    elif kind == "youtube":
        url = input("YouTube video URL: ").strip()
        if not valid_youtube(url):
            print("Please enter a valid HTTPS YouTube URL.")
            return None
        d.update(title="Watch this YouTube video", message="Enjoy the video!", youtube=url)
    elif kind == "social":
        d.update(title="How social are you?", message="Connect with friends and spread good vibes!")
    elif kind == "festival":
        festival = input("Festival name: ").strip()[:80] or "Festival"
        name = input("Recipient name: ").strip()[:80] or "Friend"
        d.update(title=f"Happy {festival}, {name}!", message=f"Wishing you and your family a joyful {festival}!")
    else:
        d.update(title="Device Check-In", message="")
    pid = secrets.token_urlsafe(9)
    PAGES[pid] = d
    return pid

def get_public_url(proc, timeout=25):
    deadline = time.time() + timeout
    while time.time() < deadline and proc.poll() is None:
        try:
            with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=1) as r:
                data = json.load(r)
            for tunnel in data.get("tunnels", []):
                if tunnel.get("public_url", "").startswith("https://"):
                    return tunnel["public_url"]
        except Exception:
            pass
        time.sleep(1)
    return None

def host_page(pid, kind):
    print("\\n1. Cloud hosting guidance")
    print("2. ngrok temporary public link")
    choice = input("Choose server: ").strip()
    path = ("/check/" if kind == "checkin" else "/p/") + pid
    if choice == "1":
        print("\\nFor a permanent link, push this app to GitHub and deploy it to a Python web host.")
        print("Install command: pip install -r requirements.txt")
        print("Start command: python main.py serve")
        print("After deployment, append this path to your hosting URL:", path)
        return
    if choice != "2":
        print("Invalid choice.")
        return
    exe = shutil.which("ngrok")
    if not exe:
        print("ngrok not found. Install and authenticate ngrok first.")
        return
    proc = subprocess.Popen([exe, "http", "5000"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    url = get_public_url(proc)
    if not url:
        proc.terminate()
        print("Could not get an HTTPS URL. Check ngrok authentication and try again.")
        return
    print("\\nPUBLIC LINK:", url + path)
    print("Keep this terminal open while the link is in use.")
    input("Press Enter to stop ngrok...")
    proc.terminate()

def main():
    threading.Thread(target=lambda: app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False), daemon=True).start()
    time.sleep(1)
    while True:
        print("\\n================================")
        print(" HACK FOR FUN | cybergenius.io")
        print("================================")
        print("1. Birthday greeting")
        print("2. YouTube video page")
        print("3. Social media page")
        print("4. Festival greeting")
        print("5. Device Check-In (consent required)")
        print("6. Exit")
        choice = input("Choose an option: ").strip()
        kinds = {"1":"birthday","2":"youtube","3":"social","4":"festival","5":"checkin"}
        if choice == "6":
            print("Goodbye!")
            return
        kind = kinds.get(choice)
        if not kind:
            print("Invalid option.")
            continue
        pid = create_page(kind)
        if pid:
            host_page(pid, kind)

if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "serve":
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
    else:
        main()
