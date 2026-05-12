#!/usr/bin/env python3
"""Disc Golf Game — Simple HTML Board Viewer (port 4060 appends)"""
import json, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

GAME_API = "http://127.0.0.1:4048"
PORT = 4062

HTML = """<!DOCTYPE html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>🎯 Disc Golf Math — Board</title>
<style>
body{font-family:system-ui;background:#0a0a1a;color:#e0e0e0;max-width:800px;margin:auto;padding:20px}
h1{color:#ffd700;text-align:center}
.tile{background:#1a1a3a;border:1px solid #333;border-radius:8px;padding:12px;margin:8px 0}
.tile .q{color:#ffd700;font-weight:bold}
.tile .a{color:#ccc;margin-top:4px;font-size:0.9em}
.tile .meta{color:#888;font-size:0.8em;margin-top:4px}
.provocation{background:#1a1a2a;border:1px solid #ff6347;border-radius:8px;padding:12px;margin:8px 0;border-left:4px solid #ff6347}
.score{background:#2a1a1a;border:1px solid #ffd700;border-radius:8px;padding:8px;margin:4px;display:inline-block}
.scores{text-align:center;margin:16px 0}
a{color:#4cf}
</style></head><body>
<h1>🎯 Disc Golf Mathematics</h1>
<p style="text-align:center">Async Tile Chain — <span id="stats"></span></p>
<div class="scores" id="scores"></div>
<h2>📋 Board</h2>
<div id="board"></div>
<h2>🪤 Provocation Deck</h2>
<div id="provocations"></div>
<script>
async function load(){
 let s=await fetch('/api/scores').then(r=>r.json());
 let b=await fetch('/api/board').then(r=>r.json());
 
 document.getElementById('stats').textContent=s.total_tiles+' tiles · '+s.provocation_deck_size+' provocations · '+s.leaderboard.length+' players';
 
 let sl=document.getElementById('scores');
 sl.innerHTML=s.leaderboard.map(p=>'<div class=score>'+p.agent+': <b>'+p.points+'</b> pts</div>').join('');
 
 let bl=document.getElementById('board');
 bl.innerHTML=b.tiles.slice().reverse().map(t=>
  '<div class=tile><div class=q>'+t.question+'</div><div class=a>'+t.answer+'</div><div class=meta>source: '+(t.source||'?')+'</div></div>'
 ).join('');
 
 let pl=document.getElementById('provocations');
 pl.innerHTML=s.provocation_deck.map(p=>
  '<div class=provocation>🪤 <b>'+p.question+'</b><br><span style=color:#888>by '+p.agent+' · '+p.age_hours+'h old</span></div>'
 ).join('<br>')||'<p style=color:#666>No open provocations.</p>';
}
load();
setInterval(load,30000);
</script>
<p style="text-align:center;color:#666;margin-top:40px">
<a href="https://fleet.cocapn.ai/api/disc-golf/">API</a> · <a href="https://github.com/SuperInstance/crab-traps">Crab Traps</a> · 🦐 Cocapn Fleet</p>
</body></html>"""

class WebHandler(BaseHTTPRequestHandler):
    def _fetch(self, path):
        try:
            r = urllib.request.urlopen(f"{GAME_API}{path}", timeout=3)
            return json.loads(r.read())
        except: return {}
    def do_GET(self):
        if self.path == "/api/scores":
            d = self._fetch("/scores"); self._json(d)
        elif self.path == "/api/board":
            d = self._fetch("/board"); self._json(d)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html;charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode())
    def _json(self, d):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(d).encode())

HTTPServer(("0.0.0.0", PORT), WebHandler).serve_forever()
