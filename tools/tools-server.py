#!/usr/bin/env python3
import os, sys, uuid, shutil, subprocess, io, json
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_file
from PIL import Image

HERE = Path(__file__).parent
UPLOAD_DIR = HERE / "uploads"
OUTPUT_DIR = HERE / "output"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = "45dgof8-tools-2026"
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

TOOLS = [
    {"slug": "pdf-merge", "name": "PDF Merge", "desc": "Combine multiple PDFs into one document", "icon": "merge"},
    {"slug": "pdf-compress", "name": "PDF Compress", "desc": "Reduce PDF file size while keeping quality", "icon": "compress"},
    {"slug": "image-compress", "name": "Image Compress", "desc": "Compress JPEG/PNG images", "icon": "image"},
    {"slug": "text-diff", "name": "Text Diff", "desc": "Compare two texts and highlight differences", "icon": "diff"},
    {"slug": "qr-code", "name": "QR Code", "desc": "Generate QR codes from text or URLs", "icon": "qr"},
    {"slug": "json-formatter", "name": "JSON Formatter", "desc": "Format, validate, and pretty-print JSON", "icon": "json"},
    {"slug": "color-palette", "name": "Color Palette", "desc": "Extract dominant colors from an image", "icon": "palette"},
    {"slug": "video-to-gif", "name": "Video to GIF", "desc": "Convert video clips to animated GIFs", "icon": "gif"},
    {"slug": "scrape", "name": "Web Scraper", "desc": "Extract structured data from any webpage using AI", "icon": "scrape"},
]

LAYOUT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} — 45dgof8 Tools</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#08080e;color:#e0d8d0;font-family:system-ui,-apple-system,sans-serif;min-height:100vh}
.container{max-width:960px;margin:0 auto;padding:24px 20px 40px}

header{text-align:center;padding:24px 0 32px}
header .badge{display:inline-block;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#887a6a;margin-bottom:8px}
header h1{font-size:34px;font-weight:800;letter-spacing:-0.5px;background:linear-gradient(135deg,#c8a87c,#e8d5b0,#d4b88a);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
header p{color:#6a5d4a;font-size:14px;margin-top:4px}
header .nav{display:flex;gap:16px;justify-content:center;margin-top:10px;flex-wrap:wrap}
header .nav a{color:#887a6a;text-decoration:none;font-size:12px;font-weight:600;letter-spacing:0.3px;transition:.15s}
header .nav a:hover{color:#c8a87c}

.card{background:#111118;border:1px solid #1c1c2a;border-radius:14px;padding:24px;margin-bottom:20px}
.card h2{font-size:13px;font-weight:700;color:#c8a87c;margin-bottom:14px;text-transform:uppercase;letter-spacing:0.8px}

.tool-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;margin-top:8px}
.tool-card{background:#111118;border:1px solid #1c1c2a;border-radius:12px;padding:20px;text-decoration:none;color:#e0d8d0;transition:.25s;display:flex;flex-direction:column}
.tool-card:hover{border-color:#c8a87c;transform:translateY(-2px);box-shadow:0 4px 24px rgba(200,168,124,0.1)}
.tool-card .icon{font-size:28px;margin-bottom:10px}
.tool-card .name{font-size:16px;font-weight:700;margin-bottom:4px}
.tool-card .desc{font-size:12px;color:#6a5d4a;line-height:1.5}

label{display:block;font-size:11px;color:#6a5d4a;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.5px;font-weight:600}
input[type=file],input[type=number],select{width:100%;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:9px 12px;font-size:13px;margin-bottom:12px}
input:focus,select:focus{outline:none;border-color:#c8a87c}
input[type=file]::file-selector-button{background:#1c1c2a;border:none;border-radius:4px;color:#c8a87c;padding:5px 12px;font-weight:600;font-size:12px;cursor:pointer}

.btn{background:linear-gradient(135deg,#c8a87c,#b8945a);color:#0a0a0f;border:none;padding:11px 28px;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;transition:.2s}
.btn:hover{transform:translateY(-1px);box-shadow:0 4px 20px rgba(200,168,124,0.25)}
.btn:disabled{opacity:.4;cursor:not-allowed;transform:none}

.status{padding:12px 16px;border-radius:8px;font-size:13px;margin-top:14px;display:none}
.status.ok{display:block;background:#0f1a0f;border:1px solid #1a2a1a;color:#8ab87a}
.status.err{display:block;background:#1a0f0f;border:1px solid #2a1a1a;color:#b87a7a}
.status a{color:#c8a87c}

footer{text-align:center;padding:32px 0 16px;color:#3a3a4a;font-size:12px}
footer a{color:#6a5d4a;text-decoration:none}
footer a:hover{color:#c8a87c}

@media(max-width:540px){.tool-grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="container">
<header>
<div class="badge">45dgof8</div>
<h1>{{ title }}</h1>
<p>{{ subtitle }}</p>
<div class="nav">
<a href="https://45dgof8.com">Home</a>
<a href="/tools">All Tools</a>
<a href="https://yt-producer.45dgof8.com">YT Producer</a>
<a href="https://paypal.me/45dgof8" target="_blank">Donate</a>
</div>
</header>
{{ content|safe }}
<footer>45dgof8 Tools &middot; <a href="https://45dgof8.com">45dgof8.com</a></footer>
</div>
</body>
</html>"""

def render_index():
    icons = {"merge": "&#128196;", "compress": "&#128190;", "image": "&#127912;", "diff": "&#128220;", "qr": "&#128247;", "json": "&#123;&#125;", "palette": "&#127912;", "gif": "&#127916;", "scrape": "&#128269;"}
    cards = ""
    for t in TOOLS:
        icon = icons.get(t["icon"], "&#128196;")
        cards += f'<a class="tool-card" href="/tools/{t["slug"]}">\n<div class="icon">{icon}</div>\n<div class="name">{t["name"]}</div>\n<div class="desc">{t["desc"]}</div>\n</a>\n'
    cards += '<a class="tool-card" href="https://yt-producer.45dgof8.com" style="border-color:#2a2218;background:linear-gradient(135deg,#111118,#151218)">\n<div class="icon">&#127916;</div>\n<div class="name" style="color:#c8a87c">YT Producer <span style="font-size:9px;background:#c8a87c;color:#0a0a0f;padding:1px 6px;border-radius:4px;margin-left:4px;vertical-align:middle">NEW</span></div>\n<div class="desc">Turn a still image into an animated YouTube Short with AI voiceover</div>\n</a>\n'
    return f'<div class="tool-grid">\n{cards}</div>'

PDF_MERGE_HTML = """
<div class="card">
<h2>Merge PDFs</h2>
<p style="color:#6a5d4a;font-size:13px;margin-bottom:14px">Upload multiple PDF files and merge them into one document.</p>
<input type="file" id="pdfs" name="pdfs" multiple accept=".pdf">
<button class="btn" id="go" onclick="merge()">Merge PDFs</button>
<div id="status" class="status"></div>
</div>
<script>
async function merge() {
  const input = document.getElementById('pdfs');
  const status = document.getElementById('status');
  const btn = document.getElementById('go');
  if (!input.files.length) { status.className='status err'; status.textContent='Please select at least one PDF.'; return; }
  status.className='status ok'; status.textContent='Processing...';
  btn.disabled = true;
  const form = new FormData();
  for (const f of input.files) form.append('pdfs', f);
  try {
    const r = await fetch('/tools/pdf-merge', { method:'POST', body:form });
    if (!r.ok) { const e = await r.json(); throw new Error(e.error); }
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'merged.pdf'; a.click();
    status.className='status ok'; status.textContent='Done! Download started.';
  } catch(e) {
    status.className='status err'; status.textContent='Error: ' + e.message;
  } finally { btn.disabled = false; }
}
</script>
"""

PDF_COMPRESS_HTML = """
<div class="card">
<h2>Compress PDF</h2>
<p style="color:#6a5d4a;font-size:13px;margin-bottom:14px">Reduce PDF file size. Select quality level — higher = smaller but lower quality.</p>
<input type="file" id="pdf" name="pdf" accept=".pdf">
<select id="level">
<option value="screen">Screen (smallest)</option>
<option value="ebook" selected>eBook (recommended)</option>
<option value="printer">Printer (high quality)</option>
<option value="prepress">Prepress (best quality)</option>
</select>
<button class="btn" id="go" onclick="compress()">Compress PDF</button>
<div id="status" class="status"></div>
</div>
<script>
async function compress() {
  const input = document.getElementById('pdf');
  const status = document.getElementById('status');
  const btn = document.getElementById('go');
  if (!input.files.length) { status.className='status err'; status.textContent='Please select a PDF.'; return; }
  status.className='status ok'; status.textContent='Processing...';
  btn.disabled = true;
  const form = new FormData();
  form.append('pdf', input.files[0]);
  form.append('level', document.getElementById('level').value);
  try {
    const r = await fetch('/tools/pdf-compress', { method:'POST', body:form });
    if (!r.ok) { const e = await r.json(); throw new Error(e.error); }
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'compressed.pdf'; a.click();
    status.className='status ok'; status.textContent='Done! Download started.';
  } catch(e) {
    status.className='status err'; status.textContent='Error: ' + e.message;
  } finally { btn.disabled = false; }
}
</script>
"""

IMAGE_COMPRESS_HTML = """
<div class="card">
<h2>Compress Image</h2>
<p style="color:#6a5d4a;font-size:13px;margin-bottom:14px">Reduce JPEG/PNG file size. Quality: 1-100 (lower = smaller file).</p>
<input type="file" id="img" name="img" accept=".jpg,.jpeg,.png,.webp">
<div style="display:flex;gap:12px;align-items:center;margin-bottom:12px">
<div style="flex:1">
<label>Quality</label>
<input type="number" id="quality" value="70" min="1" max="100">
</div>
<div style="flex:1">
<label>Max Width (px, 0 = keep)</label>
<input type="number" id="width" value="0" min="0" max="10000">
</div>
</div>
<button class="btn" id="go" onclick="compressImg()">Compress Image</button>
<div id="status" class="status"></div>
</div>
<script>
async function compressImg() {
  const input = document.getElementById('img');
  const status = document.getElementById('status');
  const btn = document.getElementById('go');
  if (!input.files.length) { status.className='status err'; status.textContent='Please select an image.'; return; }
  status.className='status ok'; status.textContent='Processing...';
  btn.disabled = true;
  const form = new FormData();
  form.append('img', input.files[0]);
  form.append('quality', document.getElementById('quality').value);
  form.append('width', document.getElementById('width').value);
  try {
    const r = await fetch('/tools/image-compress', { method:'POST', body:form });
    if (!r.ok) { const e = await r.json(); throw new Error(e.error); }
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const ext = input.files[0].name.split('.').pop();
    const a = document.createElement('a');
    a.href = url; a.download = 'compressed.' + ext; a.click();
    status.className='status ok'; status.textContent='Done! Download started.';
  } catch(e) {
    status.className='status err'; status.textContent='Error: ' + e.message;
  } finally { btn.disabled = false; }
}
</script>
"""


def page(title, subtitle, content, back=False):
    return render_template_string(LAYOUT, title=title, subtitle=subtitle, content=content, back=back)


@app.route("/")
def root():
    return page("Tools", "Free online tools by 45dgof8", render_index())

@app.route("/tools")
def index():
    return page("Tools", "Free online tools by 45dgof8", render_index())


@app.route("/tools/pdf-merge", methods=["GET", "POST"])
def pdf_merge():
    if request.method == "GET":
        return page("PDF Merge", "Combine multiple PDFs into one", PDF_MERGE_HTML, back=True)

    files = request.files.getlist("pdfs")
    if not files:
        return jsonify({"error": "No PDFs uploaded"}), 400

    uid = uuid.uuid4().hex
    work = OUTPUT_DIR / uid
    work.mkdir(exist_ok=True)

    try:
        pdfs = []
        for f in files:
            if f.filename and f.filename.lower().endswith(".pdf"):
                dst = work / f.filename
                f.save(dst)
                pdfs.append(str(dst))

        if not pdfs:
            raise ValueError("No valid PDF files found")

        merged = str(work / "merged.pdf")
        # Ghostscript merge
        args = ["gs", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite", f"-sOutputFile={merged}"] + pdfs
        subprocess.run(args, check=True, capture_output=True, timeout=120)

        return send_file(merged, as_attachment=True, download_name="merged.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        shutil.rmtree(work, ignore_errors=True)


@app.route("/tools/pdf-compress", methods=["GET", "POST"])
def pdf_compress():
    if request.method == "GET":
        return page("PDF Compress", "Reduce PDF file size", PDF_COMPRESS_HTML, back=True)

    f = request.files.get("pdf")
    if not f:
        return jsonify({"error": "No PDF uploaded"}), 400

    uid = uuid.uuid4().hex
    work = OUTPUT_DIR / uid
    work.mkdir(exist_ok=True)

    try:
        inp = str(work / "input.pdf")
        f.save(inp)

        level = request.form.get("level", "ebook")
        quality_map = {"screen": "/screen", "ebook": "/ebook", "printer": "/printer", "prepress": "/prepress"}
        quality = quality_map.get(level, "/ebook")

        out = str(work / "compressed.pdf")
        subprocess.run(
            ["gs", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite",
             f"-dPDFSETTINGS={quality}", "-dCompatibilityLevel=1.7",
             f"-sOutputFile={out}", inp],
            check=True, capture_output=True, timeout=120
        )

        return send_file(out, as_attachment=True, download_name="compressed.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        shutil.rmtree(work, ignore_errors=True)


@app.route("/tools/image-compress", methods=["GET", "POST"])
def image_compress():
    if request.method == "GET":
        return page("Image Compress", "Compress JPEG/PNG images", IMAGE_COMPRESS_HTML, back=True)

    f = request.files.get("img")
    if not f:
        return jsonify({"error": "No image uploaded"}), 400

    try:
        quality = int(request.form.get("quality", 70))
        max_width = int(request.form.get("width", 0))
    except ValueError:
        return jsonify({"error": "Invalid quality or width"}), 400

    quality = max(1, min(100, quality))

    uid = uuid.uuid4().hex
    work = OUTPUT_DIR / uid
    work.mkdir(exist_ok=True)

    try:
        img = Image.open(f)
        ext = img.format or "JPEG"

        if max_width > 0 and img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)

        out_path = work / f"compressed.{ext.lower()}"
        save_kwargs = {"optimize": True}
        if ext.upper() in ("JPEG", "JPG"):
            save_kwargs["quality"] = quality
        elif ext.upper() == "PNG":
            png_qual = max(0, min(9, int((100 - quality) / 11)))
            save_kwargs["compress_level"] = png_qual

        img.save(str(out_path), **save_kwargs)

        return send_file(str(out_path), as_attachment=True, download_name=f"compressed.{ext.lower()}")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        shutil.rmtree(work, ignore_errors=True)


TEXT_DIFF_HTML = """
<div class="card">
<h2>Text Diff</h2>
<p style="color:#6a5d4a;font-size:13px;margin-bottom:14px">Paste two versions of text and see what changed.</p>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
<div>
<label>Original</label>
<textarea id="text_a" style="width:100%;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:10px;font-size:12px;font-family:monospace;min-height:200px;resize:vertical"></textarea>
</div>
<div>
<label>Changed</label>
<textarea id="text_b" style="width:100%;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:10px;font-size:12px;font-family:monospace;min-height:200px;resize:vertical"></textarea>
</div>
</div>
<button class="btn" id="go" onclick="diff()">Compare</button>
<div id="status" class="status"></div>
<div id="result" style="display:none;margin-top:14px;background:#0a0a12;border:1px solid #1c1c2a;border-radius:8px;padding:14px;font-family:monospace;font-size:12px;line-height:1.8;white-space:pre-wrap;overflow-x:auto"></div>
</div>
<script>
async function diff() {
  const a = document.getElementById('text_a').value;
  const b = document.getElementById('text_b').value;
  const status = document.getElementById('status');
  const result = document.getElementById('result');
  const btn = document.getElementById('go');
  if (!a && !b) { status.className='status err'; status.textContent='Paste text into at least one field.'; return; }
  status.className='status ok'; status.textContent='Comparing...';
  btn.disabled = true;
  try {
    const r = await fetch('/tools/text-diff', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a,b}) });
    if (!r.ok) { const e = await r.json(); throw new Error(e.error); }
    const data = await r.json();
    result.innerHTML = data.html;
    result.style.display = 'block';
    status.className='status ok'; status.textContent='Done. Green = added, Red = removed.';
  } catch(e) {
    status.className='status err'; status.textContent='Error: ' + e.message;
  } finally { btn.disabled = false; }
}
</script>
"""


@app.route("/tools/text-diff", methods=["GET", "POST"])
def text_diff():
    if request.method == "GET":
        return page("Text Diff", "Compare two texts and highlight differences", TEXT_DIFF_HTML, back=True)

    data = request.get_json()
    a = (data or {}).get("a", "")
    b = (data or {}).get("b", "")

    import difflib
    diff = difflib.unified_diff(a.splitlines(keepends=True), b.splitlines(keepends=True), n=0)
    lines = list(diff)
    # skip the first two metadata lines (---/+++)
    lines = lines[2:]

    html_parts = []
    for line in lines:
        if line.startswith("@"):
            html_parts.append(f'<div style="color:#6a5d4a;font-weight:700">{"&zwj;".join(list(line.rstrip()))}</div>')
        elif line.startswith("+"):
            html_parts.append(f'<div style="color:#6ab87a;background:#0f1a0f;padding:0 4px">{"&zwj;".join(list(line.rstrip()))}</div>')
        elif line.startswith("-"):
            html_parts.append(f'<div style="color:#b87a6a;background:#1a0f0f;padding:0 4px">{"&zwj;".join(list(line.rstrip()))}</div>')
        else:
            html_parts.append(f'<div style="color:#6a5d4a">{"&zwj;".join(list(line.rstrip()))}</div>')

    return jsonify({"html": "".join(html_parts) if html_parts else "<div style='color:#6a5d4a'>No differences found.</div>"})


QR_HTML = """
<div class="card">
<h2>QR Code Generator</h2>
<p style="color:#6a5d4a;font-size:13px;margin-bottom:14px">Generate a QR code from any text or URL. Download as PNG.</p>
<input type="text" id="qrtext" placeholder="https://example.com or any text" style="width:100%;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:9px 12px;font-size:13px;margin-bottom:12px">
<div style="display:flex;gap:12px;align-items:center;margin-bottom:12px">
<div style="flex:1">
<label>Size (px)</label>
<input type="number" id="qrsize" value="300" min="100" max="1000" style="width:100%;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:9px 12px;font-size:13px">
</div>
<div style="flex:1">
<label>Foreground color</label>
<input type="color" id="qrfg" value="#000000" style="width:100%;height:38px;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:2px;font-size:13px;cursor:pointer">
</div>
<div style="flex:1">
<label>Background color</label>
<input type="color" id="qrbg" value="#ffffff" style="width:100%;height:38px;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:2px;font-size:13px;cursor:pointer">
</div>
</div>
<button class="btn" id="goqr" onclick="genQR()">Generate QR Code</button>
<div id="qrresult" style="margin-top:14px;text-align:center;display:none">
<img id="qrimg" style="border-radius:8px;max-width:100%">
<p style="color:#6a5d4a;font-size:12px;margin-top:8px">Right-click > Save Image</p>
</div>
<div id="qrstatus" class="status"></div>
</div>
<script>
async function genQR(){
const text=document.getElementById('qrtext').value.trim();
const status=document.getElementById('qrstatus');
const result=document.getElementById('qrresult');
const btn=document.getElementById('goqr');
if(!text){status.className='status err';status.textContent='Enter text or URL.';return}
status.className='status ok';status.textContent='Generating...';btn.disabled=true;result.style.display='none';
try{
const r=await fetch('/tools/qr-code',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,size:document.getElementById('qrsize').value,fg:document.getElementById('qrfg').value,bg:document.getElementById('qrbg').value})});
if(!r.ok){const e=await r.json();throw new Error(e.error)}
const blob=await r.blob();const url=URL.createObjectURL(blob);
document.getElementById('qrimg').src=url;result.style.display='block';
status.className='status ok';status.textContent='Right-click to save the QR code.';
}catch(e){status.className='status err';status.textContent='Error: '+e.message}
finally{btn.disabled=false}
}
</script>
"""

JSON_HTML = """
<div class="card">
<h2>JSON Formatter</h2>
<p style="color:#6a5d4a;font-size:13px;margin-bottom:14px">Paste raw JSON, format or compress it. Validation shows errors inline.</p>
<div style="display:flex;gap:8px;margin-bottom:10px">
<button class="btn" id="gojfmt" onclick="fmtJSON(2)" style="flex:1">Format (2 spaces)</button>
<button class="btn" id="gojfmt4" onclick="fmtJSON(4)" style="flex:1">Format (4 spaces)</button>
<button class="btn" id="gojmin" onclick="minJSON()" style="background:#1c1c2a;color:#c8a87c;flex:1">Minify</button>
</div>
<textarea id="jsoninput" style="width:100%;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:10px;font-size:12px;font-family:monospace;min-height:200px;resize:vertical" placeholder='{"key": "value"}'></textarea>
<div style="margin-top:10px">
<button class="btn" onclick="copyJSON()">Copy to Clipboard</button>
</div>
<div id="jsonstatus" class="status"></div>
</div>
<script>
async function fmtJSON(n){
const input=document.getElementById('jsoninput');
const status=document.getElementById('jsonstatus');
if(!input.value.trim()){status.className='status err';status.textContent='Paste some JSON first.';return}
status.className='status ok';status.textContent='Formatting...';
try{
const r=await fetch('/tools/json-formatter',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({json:input.value,indent:n})});
if(!r.ok){const e=await r.json();throw new Error(e.error)}
const data=await r.json();input.value=data.result;
status.className='status ok';status.textContent='Formatted.';
}catch(e){status.className='status err';status.textContent='Error: '+e.message}
}
async function minJSON(){
const input=document.getElementById('jsoninput');
const status=document.getElementById('jsonstatus');
if(!input.value.trim()){status.className='status err';status.textContent='Paste some JSON first.';return}
status.className='status ok';status.textContent='Minifying...';
try{
const r=await fetch('/tools/json-formatter',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({json:input.value,indent:0})});
if(!r.ok){const e=await r.json();throw new Error(e.error)}
const data=await r.json();input.value=data.result;
status.className='status ok';status.textContent='Minified.';
}catch(e){status.className='status err';status.textContent='Error: '+e.message}
}
async function copyJSON(){
const input=document.getElementById('jsoninput');
const status=document.getElementById('jsonstatus');
if(!input.value.trim()){status.className='status err';status.textContent='Nothing to copy.';return}
try{await navigator.clipboard.writeText(input.value);status.className='status ok';status.textContent='Copied!'}
catch{status.className='status err';status.textContent='Copy failed. Select manually.'}
}
</script>
"""

PALETTE_HTML = """
<div class="card">
<h2>Color Palette from Image</h2>
<p style="color:#6a5d4a;font-size:13px;margin-bottom:14px">Upload an image and extract its dominant colors.</p>
<input type="file" id="palimg" accept=".jpg,.jpeg,.png,.webp,.gif">
<div style="display:flex;gap:12px;align-items:center;margin-top:10px;margin-bottom:12px">
<div style="flex:1">
<label>Number of colors</label>
<input type="number" id="palcount" value="5" min="3" max="12" style="width:100%;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:9px 12px;font-size:13px">
</div>
</div>
<button class="btn" id="gopal" onclick="extractPalette()">Extract Colors</button>
<div id="palresult" class="status"></div>
<div id="palswatches" style="display:none;margin-top:14px;display:grid;grid-template-columns:repeat(auto-fill,minmax(80px,1fr));gap:10px"></div>
</div>
<script>
async function extractPalette(){
const input=document.getElementById('palimg');
const status=document.getElementById('palresult');
const swatches=document.getElementById('palswatches');
const btn=document.getElementById('gopal');
if(!input.files.length){status.className='status err';status.textContent='Select an image.';return}
status.className='status ok';status.textContent='Extracting...';btn.disabled=true;swatches.innerHTML='';swatches.style.display='none';
const form=new FormData();
form.append('img',input.files[0]);
form.append('count',document.getElementById('palcount').value);
try{
const r=await fetch('/tools/color-palette',{method:'POST',body:form});
if(!r.ok){const e=await r.json();throw new Error(e.error)}
const data=await r.json();
swatches.innerHTML=data.colors.map(c=>'<div style="text-align:center"><div style="width:60px;height:60px;border-radius:8px;margin:0 auto;border:1px solid #2a2a3a;background:'+c.hex+'"></div><div style="color:#b8b8b0;font-size:11px;font-family:monospace;margin-top:4px">'+c.hex+'</div><div style="color:#6a5d4a;font-size:10px">'+c.pct+'%</div></div>').join('');
swatches.style.display='grid';
status.className='status ok';status.textContent='Done. Click a hex to copy.';
swatches.querySelectorAll('div div:nth-child(2)').forEach(el=>{
el.style.cursor='pointer';el.addEventListener('click',function(){navigator.clipboard.writeText(this.textContent).catch(function(){})});
});
}catch(e){status.className='status err';status.textContent='Error: '+e.message}
finally{btn.disabled=false}
}
</script>
"""

VIDEO_GIF_HTML = """
<div class="card">
<h2>Video to GIF</h2>
<p style="color:#6a5d4a;font-size:13px;margin-bottom:14px">Convert a video clip to an animated GIF. Max 30 seconds, max 50MB.</p>
<input type="file" id="vidinput" accept=".mp4,.mov,.avi,.webm,.mkv">
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px;margin-bottom:12px">
<div>
<label>Start time (seconds)</label>
<input type="number" id="vidss" value="0" min="0" style="width:100%;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:9px 12px;font-size:13px">
</div>
<div>
<label>Duration (seconds)</label>
<input type="number" id="viddur" value="3" min="1" max="30" style="width:100%;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:9px 12px;font-size:13px">
</div>
<div>
<label>FPS</label>
<input type="number" id="vidfps" value="10" min="5" max="30" style="width:100%;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:9px 12px;font-size:13px">
</div>
<div>
<label>Width (px)</label>
<input type="number" id="vidw" value="480" min="100" max="1920" style="width:100%;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:9px 12px;font-size:13px">
</div>
</div>
<button class="btn" id="govid" onclick="toGIF()">Convert to GIF</button>
<div id="vidstatus" class="status"></div>
</div>
<script>
async function toGIF(){
const input=document.getElementById('vidinput');
const status=document.getElementById('vidstatus');
const btn=document.getElementById('govid');
if(!input.files.length){status.className='status err';status.textContent='Select a video file.';return}
status.className='status ok';status.textContent='Converting... this may take a moment.';btn.disabled=true;
const form=new FormData();
form.append('video',input.files[0]);
form.append('ss',document.getElementById('vidss').value);
form.append('dur',document.getElementById('viddur').value);
form.append('fps',document.getElementById('vidfps').value);
form.append('w',document.getElementById('vidw').value);
try{
const r=await fetch('/tools/video-to-gif',{method:'POST',body:form});
if(!r.ok){const e=await r.json();throw new Error(e.error)}
const blob=await r.blob();const url=URL.createObjectURL(blob);
const a=document.createElement('a');a.href=url;a.download='output.gif';a.click();
status.className='status ok';status.textContent='Done! GIF downloaded.';
}catch(e){status.className='status err';status.textContent='Error: '+e.message}
finally{btn.disabled=false}
}
</script>
"""


@app.route("/tools/qr-code", methods=["GET", "POST"])
def qr_code():
    if request.method == "GET":
        return page("QR Code Generator", "Generate QR codes from text or URLs", QR_HTML, back=True)
    import qrcode
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    size = min(max(int(data.get("size", 300)), 100), 1000)
    fg = data.get("fg", "#000000")
    bg = data.get("bg", "#ffffff")
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fg, back_color=bg)
    img = img.resize((size, size))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png", as_attachment=True, download_name="qrcode.png")


@app.route("/tools/json-formatter", methods=["GET", "POST"])
def json_formatter():
    if request.method == "GET":
        return page("JSON Formatter", "Format, validate, and pretty-print JSON", JSON_HTML, back=True)
    data = request.get_json()
    raw = data.get("json", "").strip()
    indent = int(data.get("indent", 2))
    if not raw:
        return jsonify({"error": "No JSON provided"}), 400
    try:
        parsed = json.loads(raw)
        if indent == 0:
            result = json.dumps(parsed, separators=(",", ":"))
        else:
            result = json.dumps(parsed, indent=indent)
        return jsonify({"result": result})
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON: {e}"}), 400


@app.route("/tools/color-palette", methods=["GET", "POST"])
def color_palette():
    if request.method == "GET":
        return page("Color Palette", "Extract dominant colors from an image", PALETTE_HTML, back=True)
    f = request.files.get("img")
    if not f:
        return jsonify({"error": "No image uploaded"}), 400
    count = min(max(int(request.form.get("count", 5)), 3), 12)
    try:
        img = Image.open(f).convert("RGB")
        img = img.resize((150, 150))
        pixels = list(img.getdata())
        from collections import Counter
        common = Counter(pixels).most_common(count)
        total = sum(c for _, c in common)
        colors = []
        for color, cnt in common:
            hex_color = "#{:02x}{:02x}{:02x}".format(*color)
            pct = round(cnt / total * 100)
            colors.append({"hex": hex_color, "pct": pct})
        return jsonify({"colors": colors})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/tools/video-to-gif", methods=["GET", "POST"])
def video_to_gif():
    if request.method == "GET":
        return page("Video to GIF", "Convert video clips to animated GIFs", VIDEO_GIF_HTML, back=True)
    f = request.files.get("video")
    if not f:
        return jsonify({"error": "No video uploaded"}), 400
    uid = uuid.uuid4().hex
    work = OUTPUT_DIR / uid
    work.mkdir(exist_ok=True)
    try:
        inp = str(work / "input.mp4")
        f.save(inp)
        ss = request.form.get("ss", "0")
        dur = request.form.get("dur", "3")
        fps = request.form.get("fps", "10")
        w = request.form.get("w", "480")
        out = str(work / "output.gif")
        subprocess.run(
            ["ffmpeg", "-y", "-ss", ss, "-t", dur, "-i", inp,
             "-vf", f"fps={fps},scale={w}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
             "-loop", "0", out],
            check=True, capture_output=True, timeout=120
        )
        return send_file(out, as_attachment=True, download_name="output.gif")
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode()[-200:] if e.stderr else str(e)
        return jsonify({"error": f"FFmpeg error: {err}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        shutil.rmtree(work, ignore_errors=True)


SCRAPE_HTML = """
<div class="card">
<h2>Web Scraper</h2>
<p style="color:#6a5d4a;font-size:13px;margin-bottom:14px">Enter a URL and tell the AI what to extract. Works on any public webpage.</p>
<label>URL</label>
<input type="url" id="scrapeurl" placeholder="https://example.com/page" style="width:100%;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:9px 12px;font-size:13px;margin-bottom:12px">
<label>What to extract</label>
<textarea id="scrapeprompt" placeholder="e.g. extract all product names and prices, or get the main article text" style="width:100%;background:#0a0a12;border:1px solid #1c1c2a;border-radius:6px;color:#e0d8d0;padding:10px;font-size:13px;min-height:80px;resize:vertical;margin-bottom:12px"></textarea>
<button class="btn" id="goscrape" onclick="scrape()">Extract Data</button>
<div id="scrapestatus" class="status"></div>
<div id="scraperesult" style="display:none;margin-top:14px;background:#0a0a12;border:1px solid #1c1c2a;border-radius:8px;padding:14px;font-family:monospace;font-size:12px;line-height:1.6;white-space:pre-wrap;overflow-x:auto;max-height:500px;overflow-y:auto"></div>
</div>
<script>
async function scrape() {
  const url = document.getElementById('scrapeurl').value.trim();
  const prompt = document.getElementById('scrapeprompt').value.trim();
  const status = document.getElementById('scrapestatus');
  const result = document.getElementById('scraperesult');
  const btn = document.getElementById('goscrape');
  if (!url) { status.className='status err'; status.textContent='Enter a URL.'; return; }
  if (!prompt) { status.className='status err'; status.textContent='Tell me what to extract.'; return; }
  status.className='status ok'; status.textContent='Fetching page and extracting... this may take a moment.';
  btn.disabled = true; result.style.display = 'none';
  try {
    const r = await fetch('/tools/scrape', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url,prompt}) });
    if (!r.ok) { const e = await r.json(); throw new Error(e.error); }
    const data = await r.json();
    result.textContent = data.result;
    result.style.display = 'block';
    status.className='status ok'; status.textContent='Done.';
  } catch(e) {
    status.className='status err'; status.textContent='Error: ' + e.message;
  } finally { btn.disabled = false; }
}
</script>
"""


@app.route("/tools/scrape", methods=["GET", "POST"])
def web_scraper():
    if request.method == "GET":
        return page("Web Scraper", "Extract data from any webpage using AI", SCRAPE_HTML, back=True)

    data = request.get_json()
    url = (data or {}).get("url", "").strip()
    prompt = (data or {}).get("prompt", "").strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400
    if not prompt:
        return jsonify({"error": "No extraction prompt provided"}), 400

    try:
        import requests as req
        r = req.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; 45dgof8-Scraper/1.0)"
        })
        if r.status_code != 200:
            return jsonify({"error": f"HTTP {r.status_code} from {url}"}), 400

        from langchain.chat_models import init_chat_model
        llm = init_chat_model(
            model="gemma-3-4b-it",
            model_provider="openai",
            base_url="http://localhost:1234/v1",
            api_key="not-needed",
            temperature=0.1,
        )

        text = r.text[:15000]
        full_prompt = f"""You are a web data extractor. Given the HTML below, answer the user's extraction request.
Return ONLY the extracted information, nothing else.

User request: {prompt}

HTML content:
{text}"""

        result = llm.invoke(full_prompt)
        return jsonify({"result": result.content.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5006
    print(f"Tools server on :{port}")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
