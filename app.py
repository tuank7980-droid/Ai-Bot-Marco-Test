"""Local visual agent lab. The browser scans a synthetic canvas; the agent moves only in that toy world."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import mimetypes
from math import hypot, isfinite
from urllib.parse import urlparse, parse_qs

from .agent import Agent
from .navigation import cell_at, center_of, find_path, move_toward
from .simulation import SCENARIOS, OBSTACLES, make_world, MAP_WIDTH, MAP_HEIGHT
from .telemetry import Recorder

PAGE = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agent Lab</title>
<style>

:root{color-scheme:dark;--bg:#080b12;--panel:#111722;--line:#202b39;--text:#edf3fa;--muted:#8291a5;--mint:#78efc5;--blue:#79baff}*{box-sizing:border-box;cursor:none!important}body{margin:0;background:radial-gradient(ellipse at 82% -18%,#17334a 0,transparent 40%),var(--bg);color:var(--text);font:14px 'Segoe UI',system-ui,sans-serif}header{height:68px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 max(calc((100vw - 1240px)/2),22px);background:#080b12dd}.brand{font-size:15px;font-weight:800;letter-spacing:-.4px}.mark{display:inline-grid;place-items:center;width:32px;height:32px;margin-right:10px;border-radius:10px;background:linear-gradient(135deg,#a4ffd9,#57c4d1);color:#07130f}.badge,.eyebrow,.label,.mono{font:inherit;letter-spacing:0}.badge{border:1px solid #24433d;color:var(--mint);background:#10221e;padding:8px 11px;border-radius:99px}main{max-width:1240px;margin:auto;padding:29px 22px}.top{display:flex;justify-content:space-between;align-items:end;gap:18px;margin-bottom:20px}.eyebrow{color:var(--mint);text-transform:uppercase;letter-spacing:1.4px}.top h1{font-size:27px;letter-spacing:-1.1px;margin:8px 0 4px}.sub,.muted{color:var(--muted);font-size:12px}.controls{display:flex;gap:8px;align-items:center}button,select{font:600 12px 'Segoe UI',system-ui,sans-serif;color:var(--text);background:#192332;border:1px solid #2b394a;border-radius:8px;padding:10px 13px;cursor:pointer}button:hover{border-color:#69d9b5}.primary{background:var(--mint);border-color:var(--mint);color:#07130f}.layout{display:grid;grid-template-columns:1.65fr .85fr;gap:15px}.panel{background:linear-gradient(150deg,#131a25,#0f141d 75%);border:1px solid var(--line);border-radius:13px;overflow:hidden}.head{height:48px;border-bottom:1px solid var(--line);padding:0 15px;display:flex;align-items:center;justify-content:space-between;font-weight:700;font-size:11px}.head small{font:12px 'Segoe UI',system-ui,sans-serif;color:var(--muted)}.mapbox{padding:12px}.map{display:block;width:100%;height:auto;border:1px solid #273749;border-radius:9px;background:#0a111b}.mapnote{display:flex;justify-content:space-between;padding:8px 3px 0;color:var(--muted);font:10px 'Segoe UI',system-ui,sans-serif;letter-spacing:0}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:11px}.metric{background:#0d131c;border:1px solid var(--line);border-radius:10px;padding:12px}.label{color:var(--muted);text-transform:uppercase}.metric strong{display:block;font-size:20px;margin-top:5px;letter-spacing:-.7px}.side{display:flex;flex-direction:column;gap:13px}.pad{padding:15px}.decision{font-size:22px;font-weight:800;letter-spacing:-.7px;margin:8px 0 3px}.progress{height:5px;background:#25303d;border-radius:8px;margin-top:15px;overflow:hidden}.progress i{display:block;height:100%;width:5%;background:var(--mint);transition:width .2s}.trace{padding:12px 15px;display:grid;gap:9px}.node{display:flex;justify-content:space-between;font-size:11px}.status{font:11px 'Segoe UI',system-ui,sans-serif;color:var(--mint)}.vision{padding:13px 15px;line-height:1.9;font-size:11px;color:#b9c7d8}.events{padding:11px 15px;max-height:145px;overflow:auto;font:11px/1.75 'Segoe UI',system-ui,sans-serif;color:#aab6c6}.event{border-bottom:1px solid #1b2430}.telemetry{margin-top:15px}.foot{text-align:right;color:#6d7c8e;font-size:10px;margin-top:16px}@media(max-width:800px){main{padding:20px 13px}.top{align-items:flex-start;flex-direction:column}.controls{flex-wrap:wrap}.layout{grid-template-columns:1fr}header{padding:0 14px}}
</style></head><body><header><div class="brand"><span class="mark">✳</span>Agent Lab <span style="font-weight:500;color:#738198">/ SIMULATION</span></div><span class="badge">● LOCAL</span></header>
<main><div class="top"><div><div class="eyebrow">GPO · SPOOKSVILLE</div><h1>Map & Simulation</h1><div class="sub">Choose a map marker or run a simulation.</div></div><div class="controls"><select id="scenario"></select><button onclick="start()">↻ Reset</button><button onclick="step()">Step</button><button class="primary" onclick="run()">▶ Run</button></div></div>
<div class="layout"><section><details class="panel preview-fold"><summary class="head"><span>Simulation</span><small id="frame">FRAME 0</small></summary><div class="mapbox"><canvas id="map" class="map" width="640" height="360"></canvas><div class="mapnote"><span>FRAME SCAN</span><span>640 x 360</span></div></div></details><div class="metrics"><div class="metric"><span class="label">Player health</span><strong id="hp">—</strong></div><div class="metric"><span class="label">Target health</span><strong id="thp">—</strong></div><div class="metric"><span class="label">Position</span><strong id="pos">—</strong></div><div class="metric"><span class="label">Distance per step</span><strong id="stride">35 px / step</strong></div></div></section>
<aside class="side"><div class="panel"><div class="head"><span>Decision</span><small id="tick">STEP 0</small></div><div class="pad"><div class="label">Action</div><div class="decision" id="decision">Observe</div><div class="muted" id="reason">Choose a scenario, then press Run.</div><div class="progress"><i id="bar"></i></div></div></div><div class="panel"><div class="head"><span>Status</span><small id="safe">SAFE</small></div><div class="trace" id="trace"><div class="node">Detection <span class="status">READY</span></div></div></div><div class="panel"><div class="head"><span>NAVIGATION MAP</span><small id="facing">Facing East</small></div><div class="mapbox"><canvas id="mini" class="map" width="320" height="176"></canvas></div></div><div class="panel"><div class="head"><span>Detection</span><small>Frame</small></div><div class="vision" id="vision">Waiting for frame...</div></div></aside></div>
<div class="panel telemetry"><div class="head"><span>Action history</span><small>TIMESTAMP &#xb7; LOCAL</small></div><div id="events" class="events">No activity yet</div></div><div class="foot">LOCAL</div></main>
<script>
const canvas=document.getElementById('map'),ctx=canvas.getContext('2d',{willReadFrequently:true}),mini=document.getElementById('mini'),mctx=mini.getContext('2d');let running=false,mapData=[];
async function api(path,opts={}){const r=await fetch(path,{headers:{'Content-Type':'application/json'},...opts});return r.json()}
function draw(w,path=[]){ctx.clearRect(0,0,640,360);ctx.fillStyle='#0b1420';ctx.fillRect(0,0,640,360);ctx.strokeStyle='#182637';for(let x=0;x<640;x+=32){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,360);ctx.stroke()}for(let y=0;y<360;y+=32){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(640,y);ctx.stroke()}for(const [x,y] of mapData){ctx.fillStyle='#41596b';ctx.fillRect(x*32,y*32,32,32);ctx.strokeStyle='#587185';ctx.strokeRect(x*32+.5,y*32+.5,31,31)}ctx.fillStyle='#12241f';ctx.beginPath();ctx.roundRect(25,22,590,316,18);ctx.fill();for(const [x,y] of mapData){ctx.fillStyle='#41596b';ctx.fillRect(x*32,y*32,32,32)}if(path.length){ctx.beginPath();path.forEach(([x,y],i)=>i?ctx.lineTo((x+.5)*32,(y+.5)*32):ctx.moveTo((x+.5)*32,(y+.5)*32));ctx.strokeStyle='#78efc5';ctx.lineWidth=3;ctx.setLineDash([7,5]);ctx.stroke();ctx.setLineDash([])}if(w.target_visible&&w.target_health>0){ctx.beginPath();ctx.arc(w.target_x,w.target_y,17,0,Math.PI*2);ctx.fillStyle='#ff806f';ctx.fill();ctx.strokeStyle='#ffd5cd';ctx.lineWidth=2;ctx.stroke()}ctx.beginPath();ctx.arc(w.player_x,w.player_y,14,0,Math.PI*2);ctx.fillStyle='#79baff';ctx.fill();ctx.strokeStyle='#d9eeff';ctx.lineWidth=2;ctx.stroke();ctx.fillStyle='#a8d4ff';ctx.font='11px monospace';ctx.fillText('AGENT',w.player_x-18,w.player_y+31);if(w.targets>1)for(let i=1;i<w.targets;i++){ctx.beginPath();ctx.arc(405+i*36,78+i*38,10,0,Math.PI*2);ctx.fillStyle='#9b87ff';ctx.fill()}}
function scan(){const {data}=ctx.getImageData(0,0,640,360);let ps=[0,0,0],ts=[0,0,0],obstacles=[];for(let y=0;y<360;y++)for(let x=0;x<640;x++){let i=(y*640+x)*4,r=data[i],g=data[i+1],b=data[i+2];if(b>220&&b>g*1.2&&r<170){ps[0]+=x;ps[1]+=y;ps[2]++}if(r>210&&g>80&&g<180&&b>70&&b<165){ts[0]+=x;ts[1]+=y;ts[2]++}}for(let cy=0;cy<11;cy++)for(let cx=0;cx<20;cx++){let i=((cy*32+16)*640+(cx*32+16))*4;if(data[i]>55&&data[i]<90&&data[i+1]>70&&data[i+1]<110&&data[i+2]>90&&data[i+2]<130)obstacles.push([cx,cy])}let center=q=>q[2]?[Math.round(q[0]/q[2]),Math.round(q[1]/q[2])]:null;return {player:center(ps),target:center(ts),obstacles,source:'canvas_rgb_scan'}}
async function refresh(){let d=await api('/api/state'),w=d.world||{};mapData=d.map||mapData;let sampleCount=d.demo_count||0,recordStart=document.getElementById('recordStart'),recordStop=document.getElementById('recordStop'),recordSave=document.getElementById('recordSave'),demoReplay=document.getElementById('demoReplay'),recordStatus=document.getElementById('recordStatus');if(recordStart)recordStart.disabled=!!d.recording;if(recordStop)recordStop.disabled=!d.recording;if(recordSave)recordSave.disabled=!sampleCount;if(demoReplay)demoReplay.disabled=!sampleCount||!!d.recording||!!d.replay?.active;if(recordStatus)recordStatus.textContent=d.recording?'Recording...':sampleCount?`${sampleCount} samples ready`:'Select a scenario, use WASD, and drag to move the camera.';draw(w,d.last?.path||[]);let o=scan();document.getElementById('hp').textContent=`${w.player_health??'—'} / 100`;document.getElementById('thp').textContent=`${w.target_health??'—'} / 73`;document.getElementById('pos').textContent=o.player?`${o.player[0]}, ${o.player[1]} px`:'unknown';document.getElementById('stride').textContent=`${d.learned_stride??20} px / step`;document.getElementById('tick').textContent=`Step ${w.tick??0}`;document.getElementById('decision').textContent=(d.last?.action||'Observe').replace(/_/g,' ');document.getElementById('reason').textContent=(d.last?.reason||'Choose a scenario, then press Run.').replace(/_/g,' ');document.getElementById('bar').style.width=`${Math.max(5,100-(w.target_health||0)/73*100)}%`;document.getElementById('safe').textContent=d.stopped?'STOPPED':'SAFE';document.getElementById('trace').innerHTML=(d.trace||[]).map(x=>`<div class="node">${x[0]}<span class="status">${x[1]}</span></div>`).join('')||'Waiting';document.getElementById('vision').innerHTML=`Source: <b>${o.source}</b><br>Player: ${o.player||'not detected'}<br>Target: ${o.target||'not detected'}<br>Obstacles: ${o.obstacles.length}<br>Confidence: ${Math.round((w.vision_confidence||0)*100)}%`;document.getElementById('frame').textContent=`FRAME ${w.tick||0}`;document.getElementById('facing').textContent=`${{N:'North',E:'East',S:'South',W:'West'}[w.facing||'E']}`;drawMini(w,d.last?.path||[]);document.getElementById('events').innerHTML=(d.events||[]).slice(-10).reverse().map(e=>`<div class="event">${e.timestamp.slice(11,23)} · ${e.event} ${e.action||e.reason||''}</div>`).join('')||'No activity yet'}
function drawMini(w,path){mctx.fillStyle='#0b1420';mctx.fillRect(0,0,320,176);for(let [x,y] of mapData){mctx.fillStyle='#41596b';mctx.fillRect(x*16,y*16,16,16)}if(path.length){mctx.beginPath();path.forEach(([x,y],i)=>i?mctx.lineTo((x+.5)*16,(y+.5)*16):mctx.moveTo((x+.5)*16,(y+.5)*16));mctx.strokeStyle='#78efc5';mctx.lineWidth=2;mctx.stroke()}if(w.target_health>0){mctx.fillStyle='#ff806f';mctx.beginPath();mctx.arc(w.target_x/2,w.target_y/2,5,0,Math.PI*2);mctx.fill()}mctx.fillStyle='#79baff';mctx.beginPath();mctx.arc(w.player_x/2,w.player_y/2,5,0,Math.PI*2);mctx.fill()}
async function start(){running=false;await api('/api/start?scenario='+encodeURIComponent(document.getElementById('scenario').value),{method:'POST'});await refresh()}
async function step(){await refresh();let o=scan();let d=await api('/api/step',{method:'POST',body:JSON.stringify(o)});await refresh();return d}
async function run(){if(running)return;running=true;for(let i=0;i<50&&running;i++){let d=await step();if(d.terminal)break;await new Promise(r=>setTimeout(r,220))}running=false}
async function init(){let [s,d]=await Promise.all([api('/api/scenarios'),api('/api/state')]);const scenarioNames={NORMAL_COMBAT:'Normal',LOW_HEALTH:'Low health',TARGET_LOST:'Target lost',VISION_LOW_CONFIDENCE:'Low vision confidence',PLAYER_STUCK:'Player stuck',ACTION_TIMEOUT:'Action timeout',UNKNOWN_STATE:'Unknown state',MULTIPLE_TARGETS:'Multiple targets'};document.getElementById('scenario').innerHTML=s.map(x=>`<option value="${x}">${scenarioNames[x]||x}</option>`).join('');mapData=d.map||[];await refresh()}init();
</script></body></html>'''

# Add camera controls without coupling localization to the viewport transform:
# the agent reads world coordinates from the stable minimap while this viewport
# is free to rotate, zoom, and tilt like a third-person camera.
PAGE = PAGE.replace(
    '<div class="layout">',
    '<div class="camera-row" style="display:flex;gap:18px;align-items:center;flex-wrap:wrap;padding:11px 14px;margin:-7px 0 15px;background:#101722;border:1px solid #202b39;border-radius:10px;color:#9baabd;font:11px \'Segoe UI\',system-ui,sans-serif"><b>CAMERA</b><label>YAW <input id="yaw" type="range" min="-180" max="180" value="0" oninput="syncCamera()"><span id="yawv">0 deg</span></label><label>ZOOM <input id="zoom" type="range" min="60" max="160" value="100" oninput="syncCamera()"><span id="zoomv">1.0x</span></label><label>PITCH <input id="pitch" type="range" min="45" max="100" value="72" oninput="syncCamera()"><span id="pitchv">0.72</span></label><button onclick="recoverCamera()">&#x27f3; Reset</button><span id="camstatus">TRACKING</span></div><div class="layout">'
)
PAGE = PAGE.replace(
    "let running=false,mapData=[];",
    "let running=false,mapData=[],camera={yaw:0,zoom:1,pitch:.72};"
)
PAGE = PAGE.replace(
    "ctx.fillRect(0,0,640,360);ctx.strokeStyle='#182637';",
    "ctx.fillRect(0,0,640,360);ctx.save();ctx.translate(320,180);ctx.scale(camera.zoom,camera.zoom*camera.pitch);ctx.rotate(camera.yaw*Math.PI/180);ctx.translate(-w.player_x,-w.player_y);ctx.strokeStyle='#182637';"
)
PAGE = PAGE.replace(
    "ctx.fillStyle='#9b87ff';ctx.fill()}}\nfunction scan()",
    "ctx.fillStyle='#9b87ff';ctx.fill()}ctx.restore()}\nfunction scan()"
)
PAGE = PAGE.replace(
    "draw(w,d.last?.path||[]);let o=scan();",
    "draw(w,d.last?.path||[]);drawMini(w,d.last?.path||[]);let o=scan();"
)
PAGE = PAGE.replace(
    "async function init(){let [s,d]=await Promise.all([api('/api/scenarios'),api('/api/state')]);",
    "function syncCamera(){camera.yaw=+document.getElementById('yaw').value;camera.zoom=+document.getElementById('zoom').value/100;camera.pitch=+document.getElementById('pitch').value/100;document.getElementById('yawv').textContent=camera.yaw+' deg';document.getElementById('zoomv').textContent=camera.zoom.toFixed(1)+'x';document.getElementById('pitchv').textContent=camera.pitch.toFixed(2);refresh()}function recoverCamera(){camera={yaw:0,zoom:1,pitch:.72};document.getElementById('yaw').value=0;document.getElementById('zoom').value=100;document.getElementById('pitch').value=72;syncCamera();document.getElementById('camstatus').textContent='CAMERA RESET'}\nfunction scan(){const {data}=mctx.getImageData(0,0,320,176);let ps=[0,0,0],ts=[0,0,0],obstacles=[];for(let y=0;y<176;y++)for(let x=0;x<320;x++){let i=(y*320+x)*4,r=data[i],g=data[i+1],b=data[i+2];if(b>220&&b>g*1.2&&r<170){ps[0]+=x;ps[1]+=y;ps[2]++}if(r>210&&g>80&&g<180&&b>70&&b<165){ts[0]+=x;ts[1]+=y;ts[2]++}}for(let cy=0;cy<11;cy++)for(let cx=0;cx<20;cx++){let i=((cy*16+8)*320+(cx*16+8))*4;if(data[i]>55&&data[i]<90&&data[i+1]>70&&data[i+1]<110&&data[i+2]>90&&data[i+2]<130)obstacles.push([cx,cy])}let center=q=>q[2]?[Math.round(q[0]/q[2]*2),Math.round(q[1]/q[2]*2)]:null;return {player:center(ps),target:center(ts),obstacles,source:'minimap_rgb_scan'}}\nasync function init(){let [s,d]=await Promise.all([api('/api/scenarios'),api('/api/state')]);"
)
PAGE = PAGE.replace(
    '<div class="layout">',
    '<div class="camera-row" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:10px 14px;margin:-7px 0 15px;background:#101722;border:1px solid #202b39;border-radius:10px;color:#9baabd;font:11px \'Segoe UI\',system-ui,sans-serif"><b>RECORDING</b><button id="recordStart" onclick="startRecording()">● Start recording</button><button id="recordStop" onclick="stopRecording()" disabled>■ Stop</button><button id="recordSave" onclick="saveDemo()" disabled>↓ Save recording</button><span id="recordStatus">Select a scenario, use WASD, and drag to move the camera.</span></div><div class="layout">'
)
PAGE = PAGE.replace('<canvas id="map" class="map"', '<canvas id="map" tabindex="0" class="map"')
PAGE = PAGE.replace(
    'async function init(){let [s,d]=await Promise.all([api(\'/api/scenarios\'),api(\'/api/state\')]);',
    '''let heldKeys=new Set(),moveTimer=null,dragPoint=null,lastMouseRecord=0;
async function startRecording(){await api('/api/record/start',{method:'POST'});document.getElementById('recordStart').disabled=true;document.getElementById('recordStop').disabled=false;document.getElementById('recordSave').disabled=true;document.getElementById('recordStatus').textContent='Recording app-window input only…';await refresh()}
async function stopRecording(){heldKeys.clear();clearInterval(moveTimer);moveTimer=null;let d=await api('/api/record/stop',{method:'POST'});document.getElementById('recordStart').disabled=false;document.getElementById('recordStop').disabled=true;document.getElementById('recordSave').disabled=!d.count;document.getElementById('recordStatus').textContent=`Saved ${d.count} keyboard/mouse samples in this session.`;await refresh()}
async function saveDemo(){let d=await api('/api/state');let blob=new Blob([JSON.stringify({format:'agent-lab-demo-v1',samples:d.demo},null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='agent-lab-demo.json';a.click();URL.revokeObjectURL(a.href)}
function pointerPos(e){let r=canvas.getBoundingClientRect();return [Math.round((e.clientX-r.left)*640/r.width),Math.round((e.clientY-r.top)*360/r.height)]}
async function sendDemo(type,move=[0,0],cursor=null){let a=camera.yaw*Math.PI/180,sx=move[0],sy=move[1],dx=Math.cos(a)*sx+Math.sin(a)*sy,dy=-Math.sin(a)*sx+Math.cos(a)*sy;await api('/api/manual',{method:'POST',body:JSON.stringify({type,dx,dy,cursor,camera:{yaw:camera.yaw,zoom:camera.zoom,pitch:camera.pitch}})});await refresh()}
canvas.tabIndex=0;canvas.addEventListener('keydown',e=>{if(!['w','a','s','d','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();if(!document.getElementById('recordStop').disabled)return;let k=e.key.toLowerCase();heldKeys.add(k);if(!moveTimer)moveTimer=setInterval(()=>{if(!heldKeys.size)return;let x=0,y=0;if(heldKeys.has('w')||heldKeys.has('arrowup'))y-=1;if(heldKeys.has('s')||heldKeys.has('arrowdown'))y+=1;if(heldKeys.has('a')||heldKeys.has('arrowleft'))x-=1;if(heldKeys.has('d')||heldKeys.has('arrowright'))x+=1;sendDemo('keyboard',[x,y],pointerPos({clientX:lastPointerX,clientY:lastPointerY}))},180)});
let lastPointerX=0,lastPointerY=0;window.addEventListener('keyup',e=>heldKeys.delete(e.key.toLowerCase()));canvas.addEventListener('pointerdown',e=>{canvas.focus();dragPoint=[e.clientX,e.clientY];lastPointerX=e.clientX;lastPointerY=e.clientY;canvas.setPointerCapture(e.pointerId)});canvas.addEventListener('pointermove',e=>{lastPointerX=e.clientX;lastPointerY=e.clientY;if(dragPoint&&e.buttons){let dx=e.clientX-dragPoint[0],dy=e.clientY-dragPoint[1];camera.yaw=((camera.yaw+dx*.55+180)%360+360)%360-180;camera.pitch=Math.max(.45,Math.min(1,camera.pitch-dy*.004));document.getElementById('yaw').value=camera.yaw;document.getElementById('pitch').value=Math.round(camera.pitch*100);syncCamera();dragPoint=[e.clientX,e.clientY];let now=performance.now();if(!document.getElementById('recordStop').disabled&&now-lastMouseRecord>100){lastMouseRecord=now;sendDemo('mouse_drag',[0,0],pointerPos(e))}}});canvas.addEventListener('pointerup',()=>dragPoint=null);canvas.addEventListener('wheel',e=>{e.preventDefault();camera.zoom=Math.max(.6,Math.min(1.6,camera.zoom-e.deltaY*.001));document.getElementById('zoom').value=Math.round(camera.zoom*100);syncCamera();if(!document.getElementById('recordStop').disabled)sendDemo('mouse_zoom',[0,0],pointerPos(e))},{passive:false});
async function init(){let [s,d]=await Promise.all([api('/api/scenarios'),api('/api/state')]);'''
)
PAGE = PAGE.replace(
    '<button id="recordSave" onclick="saveDemo()" disabled>↓ Save recording</button>',
    '<button id="recordSave" onclick="saveDemo()" disabled>↓ Save recording</button><input id="demoFile" type="file" accept="application/json,.json" hidden onchange="loadDemo(event)"><button onclick="document.getElementById(\'demoFile\').click()">↑ Load recording</button><button id="demoReplay" onclick="runReplay()" disabled>▶ Replay</button>'
)
PAGE = PAGE.replace(
    "await api('/api/record/start',{method:'POST'});",
    "await api('/api/record/start',{method:'POST',body:JSON.stringify({obstacles:scan().obstacles})});"
)
PAGE = PAGE.replace(
    "document.getElementById('recordSave').disabled=!d.count;",
    "document.getElementById('recordSave').disabled=!d.count;document.getElementById('demoReplay').disabled=!d.count;"
)
PAGE = PAGE.replace(
    "async function saveDemo(){let d=await api('/api/state');let blob=new Blob([JSON.stringify({format:'agent-lab-demo-v1',samples:d.demo},null,2)],{type:'application/json'}),a=document.createElement('a');",
    "async function saveDemo(){let d=await api('/api/state');let blob=new Blob([JSON.stringify({format:'agent-lab-demo-v1',header:d.demo_header,samples:d.demo},null,2)],{type:'application/json'}),a=document.createElement('a');"
)
PAGE = PAGE.replace(
    "function pointerPos(e){",
    "async function loadDemo(e){try{let file=e.target.files[0];if(!file)return;let data=JSON.parse(await file.text()),r=await api('/api/demo/load',{method:'POST',body:JSON.stringify(data)});document.getElementById('demoReplay').disabled=!r.count;document.getElementById('recordSave').disabled=!r.count;document.getElementById('recordStatus').textContent=`Loaded ${r.count} samples and saved map.`;await refresh()}catch(err){document.getElementById('recordStatus').textContent='Could not load demo JSON.'}finally{e.target.value=''}}async function runReplay(){document.getElementById('demoReplay').disabled=true;let initial=await api('/api/replay/start',{method:'POST'});let maxTicks=Math.min(100000,Math.max(500,(initial.replay?.total||1)*4));for(let i=0;i<maxTicks;i++){let d=await api('/api/replay/step',{method:'POST'});if(d.last?.camera){camera={yaw:d.last.camera.yaw,zoom:d.last.camera.zoom,pitch:d.last.camera.pitch};document.getElementById('yaw').value=camera.yaw;document.getElementById('zoom').value=Math.round(camera.zoom*100);document.getElementById('pitch').value=Math.round(camera.pitch*100);document.getElementById('yawv').textContent=camera.yaw+' deg';document.getElementById('zoomv').textContent=camera.zoom.toFixed(1)+'x';document.getElementById('pitchv').textContent=camera.pitch.toFixed(2)}await refresh();if(d.terminal)break;await new Promise(r=>setTimeout(r,120))}document.getElementById('demoReplay').disabled=false}\nfunction pointerPos(e){"
)
PAGE = PAGE.replace(
    "canvas.tabIndex=0;canvas.addEventListener('keydown'",
    "async function moveKeys(){if(!heldKeys.size)return;let x=0,y=0;if(heldKeys.has('w')||heldKeys.has('arrowup'))y-=1;if(heldKeys.has('s')||heldKeys.has('arrowdown'))y+=1;if(heldKeys.has('a')||heldKeys.has('arrowleft'))x-=1;if(heldKeys.has('d')||heldKeys.has('arrowright'))x+=1;await sendDemo('keyboard',[x,y],pointerPos({clientX:lastPointerX,clientY:lastPointerY}))}\ncanvas.tabIndex=0;canvas.addEventListener('keydown'"
)
PAGE = PAGE.replace(
    "if(!moveTimer)moveTimer=setInterval(()=>{if(!heldKeys.size)return;let x=0,y=0;if(heldKeys.has('w')||heldKeys.has('arrowup'))y-=1;if(heldKeys.has('s')||heldKeys.has('arrowdown'))y+=1;if(heldKeys.has('a')||heldKeys.has('arrowleft'))x-=1;if(heldKeys.has('d')||heldKeys.has('arrowright'))x+=1;sendDemo('keyboard',[x,y],pointerPos({clientX:lastPointerX,clientY:lastPointerY}))},180)",
    "moveKeys();if(!moveTimer)moveTimer=setInterval(moveKeys,180)"
)
PAGE = PAGE.replace(
    "if(!document.getElementById('recordStop').disabled)return;let k=e.key.toLowerCase();",
    "if(document.getElementById('recordStop').disabled)return;let k=e.key.toLowerCase();"
)

# Offline reference-map panel. The manually placed player pin is visual only;
# this panel does not inspect or control another application or game.
MAP_STYLE = r'''<style>
.reference{margin:0 0 16px}.reference>.head{gap:12px}.ref-tools{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.filter-wrap{position:relative}.filter-menu{position:absolute;z-index:5;top:42px;left:0;min-width:230px;padding:8px;background:#111722;border:1px solid #2a3747;border-radius:11px;box-shadow:0 16px 44px #0009;display:none}.filter-menu.open{display:grid;gap:2px}.filter-menu label{display:flex;align-items:center;gap:9px;padding:9px 8px;border-radius:7px;color:#dce7f4;font-size:12px;cursor:pointer}.filter-menu label:hover{background:#1a2533}.filter-menu input{accent-color:#68b9ff;width:15px;height:15px}.ref-button{padding:9px 12px;background:#62aaff;color:#061324;border:0;border-radius:99px;font-size:11px}.ref-stage{position:relative;overflow:hidden;width:min(100%,120vh);margin:0 auto;border:1px solid #283546;border-radius:9px;background:#0b111a;padding:8px}.ref-svg{display:block;width:100%;height:auto;max-height:none;aspect-ratio:1299 / 1292;background:#2076c9;touch-action:none;user-select:none;cursor:grab}.ref-svg:active{cursor:grabbing}.ref-hud{position:absolute;right:17px;bottom:17px;display:grid;gap:4px}.ref-hud button{width:36px;height:34px;padding:0;background:#62aaff;color:#061324;border:0;border-radius:7px;font-size:18px}.ref-hud .tool-row{display:flex;gap:4px}.ref-hud .tool-row button{width:32px;height:30px;font-size:14px}.ref-hud .tool-row button.active{background:#b8dcff;color:#07182c}.ref-hud .facing{display:grid;place-items:center;width:34px;height:30px;border-radius:7px;background:#111a27;color:#e5f2ff;font-size:10px;font-weight:700}.ref-info{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:9px 2px 0;color:#98a9bc;font:11px 'Segoe UI',system-ui,sans-serif}.pin-mode{color:#90d0ff!important}.pin-tip{display:none;color:#bcd8f2;font-size:11px}.pin-tip.show{display:inline}.ref-legend{display:flex;flex-wrap:wrap;gap:7px}.ref-tooltip{position:absolute;z-index:6;display:none;pointer-events:none;max-width:260px;padding:8px 10px;background:#0b111af2;border:1px solid #3b4b60;border-radius:8px;box-shadow:0 10px 28px #0008;color:#f1f5fa;font:12px 'Segoe UI',system-ui,sans-serif;line-height:1.35}.ref-tooltip strong{display:block;font-weight:700}.ref-tooltip small{display:block;margin-top:2px;color:#9eafc2;font-size:10px}.ref-chip{border:1px solid #2a3747;background:#101722;border-radius:99px;padding:6px 9px;color:#b9c7d8}.ref-chip b{color:#eef5fd;font-weight:700}.ref-loading{padding:40px;text-align:center;color:#b9c7d8}.ref-preview-link{padding:7px 10px;border-radius:7px;background:#121c29;border:1px solid #2a3747;color:#b8d9f3;font-size:11px}.preview-fold>summary{cursor:pointer;list-style:none}.preview-fold>summary::-webkit-details-marker{display:none}.preview-fold>summary:after{content:'Open';color:var(--mint);font:11px 'Segoe UI',system-ui,sans-serif}.preview-fold[open]>summary:after{content:'Close'}
@media(max-width:700px){.ref-info{align-items:flex-start;flex-direction:column}.ref-stage{padding:5px}.ref-hud{right:10px;bottom:10px}.reference>.head{height:auto;min-height:48px;align-items:flex-start;padding:10px 12px}.ref-tools{justify-content:flex-end}}
</style>'''
MAP_PANEL = r'''<section class="panel reference"><div class="head"><span>Spooksville</span><div class="ref-tools"><small id="mapCount">Loading...</small><div class="filter-wrap"><button id="filterToggle" class="ref-button" onclick="toggleMapFilters()">Filters &#x2304;</button><div id="filterMenu" class="filter-menu"></div></div><button id="placePin" onclick="togglePinMode()">Set player location</button><button onclick="clearPin()">Reset location</button></div></div><div class="mapbox"><div class="ref-stage"><div id="mapLoading" class="ref-loading">Loading map...</div><svg id="referenceMap" class="ref-svg" viewBox="0 0 1299 1292" role="img" aria-label="Spooksville map" title="Drag to rotate and tilt; Shift-drag to pan" style="display:none"></svg><div id="mapTooltip" class="ref-tooltip" role="tooltip"></div><div class="ref-hud"><button title="Zoom in (2x)" onclick="zoomReference(0.5)">+</button><button title="Zoom out (0.5x)" onclick="zoomReference(2)">&#x2212;</button><button title="Fit map and reset orientation" onclick="fitReference()">&#x26f6;</button></div></div><div class="ref-info"><span id="mapStatus">Drag to rotate and tilt · Shift-drag to pan</span><span class="pin-tip" id="pinTip">Click the map to set the player location</span><div id="mapLegend" class="ref-legend"></div><button class="ref-preview-link" onclick="openSimulatorPreview()">Simulation</button></div></div></section>'''
MAP_SCRIPT = r'''<script>
const MAP_W=1299,MAP_H=1292,MIN_MAP_VIEW=MAP_W/12,refSvg=document.getElementById('referenceMap');
let referenceData=null,visibleCats=new Set(),playerLocation=null,spawnLocation=null,pinMode=false,mapWorld=null,mapRotation=0,mapPitch=1,playerHeading=90,rotateDrag=null,
viewBox={x:(MAP_W-MAP_W/1.12)/2,y:(MAP_H-(MAP_W/1.12)*MAP_H/MAP_W)/2,w:MAP_W/1.12,h:(MAP_W/1.12)*MAP_H/MAP_W},pan=null;
const PLAYER_LOCATION_KEY='spooksville.playerLocation';
const svgEl=(tag,attrs={})=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);return n};
function loadPlayerLocation(){const spawn=referenceData.markers.find(m=>m.category==='player');if(!spawn)return;spawnLocation={x:spawn.x,y:spawn.y};try{let saved=JSON.parse(localStorage.getItem(PLAYER_LOCATION_KEY)||'null');const oldDefaults=[[580.5346673541554,403.4044186669253],[580.5346673541554,888.5955813330747],[644,548],[0,0]],stale=saved&&oldDefaults.some(([x,y])=>Math.abs(saved.x-x)<2&&Math.abs(saved.y-y)<2);if(stale){localStorage.removeItem(PLAYER_LOCATION_KEY);saved=null}playerLocation=saved&&Number.isFinite(saved.x)&&Number.isFinite(saved.y)&&saved.x>=0&&saved.x<=MAP_W&&saved.y>=0&&saved.y<=MAP_H?saved:{...spawnLocation}}catch{playerLocation={...spawnLocation}}}
async function initReferenceMap(){try{const r=await fetch('/assets/spooksville-data.json');if(!r.ok)throw Error('Map data unavailable');referenceData=await r.json();loadPlayerLocation();visibleCats=new Set(referenceData.categories.map(c=>c.id));document.getElementById('mapLoading').style.display='none';refSvg.style.display='block';mapWorld=svgEl('g',{id:'referenceWorld'});mapWorld.append(svgEl('image',{href:referenceData.image,x:0,y:0,width:MAP_W,height:MAP_H,'preserveAspectRatio':'none'}));refSvg.append(mapWorld);buildMapFilters();drawReferenceMarkers();updateReferenceView();refSvg.addEventListener('pointerdown',mapPointerDown);refSvg.addEventListener('pointermove',mapPointerMove);refSvg.addEventListener('pointerup',mapPointerUp);refSvg.addEventListener('pointercancel',mapPointerUp);refSvg.addEventListener('wheel',mapWheel,{passive:false});refSvg.addEventListener('contextmenu',e=>e.preventDefault());refSvg.addEventListener('pointerleave',hideMapTooltip);window.addEventListener('resize',updateReferenceView);document.getElementById('mapStatus').textContent='Drag to rotate/tilt · Shift-drag to pan · Wheel to zoom';document.getElementById('mapCount').textContent=`${referenceData.markers.length} points`}catch(e){document.getElementById('mapLoading').textContent='Map assets could not be loaded.';document.getElementById('mapStatus').textContent='Check local static map files.'}}
function buildMapFilters(){const menu=document.getElementById('filterMenu'),all=document.createElement('label');all.innerHTML='<input id="allCats" type="checkbox" checked><span>Select all</span>';menu.replaceChildren(all);all.querySelector('input').addEventListener('change',e=>{visibleCats=e.target.checked?new Set(referenceData.categories.map(c=>c.id)):new Set();menu.querySelectorAll('[data-cat]').forEach(x=>x.checked=e.target.checked);drawReferenceMarkers()});for(const cat of referenceData.categories){const label=document.createElement('label'),icon=cat.icon?`<img src="${cat.icon}" style="width:18px;height:18px;object-fit:contain">`:'<span style="width:18px;text-align:center">&#x25c9;</span>';label.innerHTML=`<input data-cat="${cat.id}" type="checkbox" checked><span>${icon} ${cat.label}</span><span style="margin-left:auto;color:#8d9db0">${cat.count}</span>`;label.querySelector('input').addEventListener('change',e=>{e.target.checked?visibleCats.add(cat.id):visibleCats.delete(cat.id);document.getElementById('allCats').checked=visibleCats.size===referenceData.categories.length;drawReferenceMarkers()});menu.append(label)}document.addEventListener('click',e=>{if(!e.target.closest('.filter-wrap'))menu.classList.remove('open')})}
function toggleMapFilters(){document.getElementById('filterMenu').classList.toggle('open')}
function showMapTooltip(e,name,kind){const tip=document.getElementById('mapTooltip');tip.replaceChildren();const strong=document.createElement('strong');strong.textContent=name;tip.append(strong);if(kind&&kind!==name){const small=document.createElement('small');small.textContent=kind;tip.append(small)}tip.style.display='block';moveMapTooltip(e)}
function moveMapTooltip(e){const tip=document.getElementById('mapTooltip'),stage=document.querySelector('.ref-stage');if(!tip||!stage)return;const box=stage.getBoundingClientRect(),x=e.clientX-box.left,y=e.clientY-box.top,left=x>tip.offsetWidth+24?x-tip.offsetWidth-14:x+14,top=y>tip.offsetHeight+24?y-tip.offsetHeight-14:y+14;tip.style.left=Math.max(8,Math.min(box.width-tip.offsetWidth-8,left))+'px';tip.style.top=Math.max(8,Math.min(box.height-tip.offsetHeight-8,top))+'px'}
function hideMapTooltip(){const tip=document.getElementById('mapTooltip');if(tip)tip.style.display='none'}
function bindMapTooltip(node,name,kind){node.addEventListener('pointerenter',e=>showMapTooltip(e,name,kind));node.addEventListener('pointermove',moveMapTooltip);node.addEventListener('pointerleave',hideMapTooltip);node.addEventListener('focus',()=>{const r=node.getBoundingClientRect();showMapTooltip({clientX:r.left+r.width/2,clientY:r.top+r.height/2},name,kind)});node.addEventListener('blur',hideMapTooltip)}
function facingName(){const dirs=['E','SE','S','SW','W','NW','N','NE'],heading=((playerHeading%360)+360)%360;return dirs[Math.round(heading/45)%8]}
function headingSectorPath(x,y,r){const span=130,start=(playerHeading-span/2)*Math.PI/180,end=(playerHeading+span/2)*Math.PI/180,sx=x+r*Math.cos(start),sy=y+r*Math.sin(start),ex=x+r*Math.cos(end),ey=y+r*Math.sin(end);return`M ${x} ${y} L ${sx} ${sy} A ${r} ${r} 0 0 1 ${ex} ${ey} Z`}
function drawReferenceMarkers(){if(!referenceData||!mapWorld)return;mapWorld.querySelectorAll('[data-marker-layer]').forEach(n=>n.remove());const layer=svgEl('g',{'data-marker-layer':'1'}),markers=[...referenceData.markers.filter(m=>m.category==='player'),...referenceData.markers.filter(m=>m.category!=='player')],mapScale=viewBox.w/MAP_W;for(const marker of markers){if(!visibleCats.has(marker.category))continue;const cat=referenceData.categories.find(c=>c.id===marker.category),icon=marker.icon||cat?.icon;if(!icon)continue;const name=marker.name||cat.label,g=svgEl('g',{class:'map-marker',tabindex:'0',role:'img','aria-label':name});let x=marker.x,y=marker.y;
if(marker.category==='player'){x=playerLocation?.x??marker.x;y=playerLocation?.y??marker.y;const size=48*mapScale,radius=80*mapScale;g.append(svgEl('path',{d:headingSectorPath(x,y,radius),fill:'#70b9ff','fill-opacity':'.2',stroke:'#a9d9ff','stroke-opacity':'.42','stroke-width':1.2*mapScale}));g.append(svgEl('image',{href:icon,x:x-size*127/256,y:y-size*209/256,width:size,height:size,preserveAspectRatio:'xMidYMid meet'}))}
else{const baseSize=marker.category==='enemy'?13:marker.category==='safezone'?12.5:marker.category==='logpose'?12.5:marker.category==='shop'?(marker.id==='shop-1'?54:46):23,size=baseSize*mapScale;g.append(svgEl('image',{href:icon,x:x-size/2,y:y-size/2,width:size,height:size,preserveAspectRatio:'xMidYMid meet'}))}
bindMapTooltip(g,name,cat.label);layer.append(g)}mapWorld.append(layer);document.getElementById('mapCount').textContent=`${referenceData.markers.length} points`;document.getElementById('mapLegend').innerHTML=`<span class="ref-chip">Player <b>${Math.round(playerLocation?.x??0)}, ${Math.round(playerLocation?.y??0)}</b></span><span class="ref-chip">Facing <b>${facingName()}</b></span>`}
function updateReferenceTransform(){if(!mapWorld)return;const cx=viewBox.x+viewBox.w/2,cy=viewBox.y+viewBox.h/2;mapWorld.setAttribute('transform',`translate(${cx} ${cy}) rotate(${mapRotation}) scale(1 ${mapPitch}) translate(${-cx} ${-cy})`)}
function updateReferenceView(){refSvg.setAttribute('viewBox',`${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`);updateReferenceTransform();drawReferenceMarkers()}
function zoomReference(factor){const w=Math.max(MIN_MAP_VIEW,Math.min(MAP_W,viewBox.w*factor)),h=w*MAP_H/MAP_W,cx=viewBox.x+viewBox.w/2,cy=viewBox.y+viewBox.h/2;viewBox={x:Math.max(0,Math.min(MAP_W-w,cx-w/2)),y:Math.max(0,Math.min(MAP_H-h,cy-h/2)),w,h};updateReferenceView()}
function fitReference(){viewBox={x:0,y:0,w:MAP_W,h:MAP_H};mapRotation=0;mapPitch=1;updateReferenceView()}
function zoomAt(factor,p){const w=Math.max(MIN_MAP_VIEW,Math.min(MAP_W,viewBox.w*factor)),h=w*MAP_H/MAP_W,rx=(p.x-viewBox.x)/viewBox.w,ry=(p.y-viewBox.y)/viewBox.h;viewBox={x:Math.max(0,Math.min(MAP_W-w,p.x-rx*w)),y:Math.max(0,Math.min(MAP_H-h,p.y-ry*h)),w,h};updateReferenceView()}
function mapPoint(e){const r=refSvg.getBoundingClientRect(),sx=viewBox.x+(e.clientX-r.left)/r.width*viewBox.w,sy=viewBox.y+(e.clientY-r.top)/r.height*viewBox.h,cx=viewBox.x+viewBox.w/2,cy=viewBox.y+viewBox.h/2,dx=sx-cx,dy=sy-cy,rad=mapRotation*Math.PI/180,rx=dx*Math.cos(rad)+dy*Math.sin(rad),ry=(-dx*Math.sin(rad)+dy*Math.cos(rad))/mapPitch;return{x:cx+rx,y:cy+ry}}
function togglePinMode(){pinMode=!pinMode;document.getElementById('placePin').classList.toggle('pin-mode',pinMode);document.getElementById('pinTip').classList.toggle('show',pinMode);refSvg.style.cursor=pinMode?'crosshair':'default'}
function clearPin(){playerLocation={...spawnLocation};localStorage.removeItem(PLAYER_LOCATION_KEY);drawReferenceMarkers()}
function mapPointerDown(e){if(e.button===2||(e.button===0&&e.shiftKey)){refSvg.setPointerCapture(e.pointerId);pan={x:e.clientX,y:e.clientY,view:{...viewBox},moved:false,canPlace:false};return}if(e.button!==0)return;refSvg.setPointerCapture(e.pointerId);if(pinMode){pan={x:e.clientX,y:e.clientY,view:{...viewBox},moved:false,canPlace:true,start:mapPoint(e)};return}rotateDrag={x:e.clientX,y:e.clientY,rotation:mapRotation,pitch:mapPitch}}
function mapPointerMove(e){if(rotateDrag){const dx=e.clientX-rotateDrag.x,dy=e.clientY-rotateDrag.y;mapRotation=rotateDrag.rotation+dx*.45;mapPitch=Math.max(.4,Math.min(1,rotateDrag.pitch-dy/400));updateReferenceView();return}if(!pan)return;const dx=e.clientX-pan.x,dy=e.clientY-pan.y;if(Math.abs(dx)+Math.abs(dy)>4)pan.moved=true;if(pan.moved&&!pinMode){const rect=refSvg.getBoundingClientRect(),sx=dx/rect.width*pan.view.w,sy=dy/rect.height*pan.view.h,rad=mapRotation*Math.PI/180,moveX=sx*Math.cos(rad)+sy*Math.sin(rad),moveY=(-sx*Math.sin(rad)+sy*Math.cos(rad))/mapPitch;viewBox.x=Math.max(0,Math.min(MAP_W-viewBox.w,pan.view.x-moveX));viewBox.y=Math.max(0,Math.min(MAP_H-viewBox.h,pan.view.y-moveY));updateReferenceView()}}
function mapPointerUp(e){if(rotateDrag){rotateDrag=null;return}if(!pan)return;if(pan.canPlace&&!pan.moved&&pinMode){const p=mapPoint(e);playerLocation={x:Math.max(0,Math.min(MAP_W,p.x)),y:Math.max(0,Math.min(MAP_H,p.y))};localStorage.setItem(PLAYER_LOCATION_KEY,JSON.stringify(playerLocation));pinMode=false;document.getElementById('placePin').classList.remove('pin-mode');document.getElementById('pinTip').classList.remove('show');refSvg.style.cursor='default';drawReferenceMarkers()}pan=null}
function openSimulatorPreview(){const preview=document.querySelector('.preview-fold');if(!preview)return;preview.open=true;preview.scrollIntoView({behavior:'smooth',block:'center'})}
function mapWheel(e){e.preventDefault();zoomAt(e.deltaY<0?.85:1.18,mapPoint(e))}
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&pinMode)togglePinMode()});initReferenceMap();
</script>'''
PAGE = PAGE.replace('</style>', MAP_STYLE.removeprefix('<style>').removesuffix('</style>') + '</style>')
PAGE = PAGE.replace('<div class="camera-row"', MAP_PANEL + '<div class="camera-row"', 1)
PAGE = PAGE.replace('</script>', MAP_SCRIPT.removeprefix('<script>').removesuffix('</script>') + '</script>')


class AppState:
    def reset(self, scenario):
        self.world = make_world(scenario)
        self.recorder = Recorder()
        self.agent = Agent(self.recorder)
        self.last = {}
        self.recording = False
        self.demo = []
        self.map_cells = set(OBSTACLES)
        self.demo_header = {}
        self.replay_samples = []
        self.replay_index = 0
        self.replay_active = False

    def __init__(self): self.reset("NORMAL_COMBAT")

    def json(self):
        return {"world": self.world.snapshot(), "last": self.last, "trace": self.agent.trace,
                "events": self.recorder.events, "learned_stride": round(self.agent.learned_stride, 1),
                "map": [list(p) for p in sorted(self.map_cells)],
                "stopped": self.agent.safety.stopped, "recording": self.recording,
                "demo_count": len(self.demo), "demo": self.demo,
                "demo_header": self.demo_header,
                "replay": {"active": self.replay_active, "index": self.replay_index,
                           "total": len(self.replay_samples)}}


APP = AppState()


class Handler(BaseHTTPRequestHandler):
    def read_json(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size > 2_000_000:
            raise ValueError("request too large")
        raw = self.rfile.read(size) if size else b"{}"
        value = json.loads(raw or b"{}")
        if not isinstance(value, dict):
            raise ValueError("expected JSON object")
        return value

    @staticmethod
    def valid_map(cells):
        return (isinstance(cells, list) and len(cells) <= MAP_WIDTH * MAP_HEIGHT and
                all(isinstance(p, list) and len(p) == 2 and
                    all(isinstance(v, int) and not isinstance(v, bool) for v in p) and
                    0 <= p[0] < MAP_WIDTH and 0 <= p[1] < MAP_HEIGHT for p in cells))

    def send_json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/":
            body = PAGE.encode(); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        elif route.startswith("/assets/"):
            name = route.removeprefix("/assets/")
            allowed = {"spooksville-map.png", "spooksville-data.json", "marker-enemy.png",
                       "marker-player.png", "marker-respawn.png", "marker-shop.png", "marker-logpose.svg",
                       "marker-shop-center.png", "marker-shop-outside.png", "marker-respawn-tight.png", "marker-logpose.png", "marker-player-location.png"}
            if name not in allowed or Path(name).name != name:
                return self.send_error(404)
            asset = Path(__file__).with_name("static") / name
            try:
                body = asset.read_bytes()
            except OSError:
                return self.send_error(404)
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif route == "/api/state": self.send_json(APP.json())
        elif route == "/api/scenarios": self.send_json(SCENARIOS)
        else: self.send_error(404)

    def do_POST(self):
        route = urlparse(self.path)
        if route.path in ("/api/record/start", "/api/record/stop"):
            if route.path.endswith("start"):
                try:
                    body = self.read_json()
                except (ValueError, json.JSONDecodeError):
                    return self.send_error(400)
                scanned = body.get("obstacles", [list(p) for p in sorted(OBSTACLES)])
                if not self.valid_map(scanned): return self.send_error(400)
                APP.demo = []
                APP.map_cells = {tuple(p) for p in scanned}
                APP.demo_header = {"scenario": APP.world.scenario,
                                   "world": APP.world.snapshot(),
                                   "map": [list(p) for p in sorted(APP.map_cells)],
                                   "source": "Agent Lab synthetic canvas"}
                APP.recording = True
                APP.replay_active = False
                APP.recorder.emit("demo_recording_started", scope="this_app_canvas_only")
            else:
                APP.recording = False
                APP.recorder.emit("demo_recording_stopped", samples=len(APP.demo))
            return self.send_json({"recording": APP.recording, "count": len(APP.demo)})
        if route.path == "/api/manual":
            try:
                sample = self.read_json()
            except (ValueError, json.JSONDecodeError):
                return self.send_error(400)
            if not APP.recording: return self.send_error(409)
            kind = sample.get("type")
            if kind not in ("keyboard", "mouse_drag", "mouse_zoom"): return self.send_error(400)
            camera = sample.get("camera", {})
            if not isinstance(camera, dict) or any(not isinstance(camera.get(k), (int, float)) or
                    not isfinite(camera[k]) for k in ("yaw", "zoom", "pitch")):
                return self.send_error(400)
            if not (-180 <= camera["yaw"] <= 180 and .6 <= camera["zoom"] <= 1.6 and .45 <= camera["pitch"] <= 1):
                return self.send_error(400)
            cursor = sample.get("cursor")
            if cursor is not None and (not isinstance(cursor, list) or len(cursor) != 2 or
                    any(not isinstance(v, int) for v in cursor) or not (0 <= cursor[0] < 640 and 0 <= cursor[1] < 360)):
                return self.send_error(400)
            dx, dy = sample.get("dx", 0), sample.get("dy", 0)
            if not isinstance(dx, (int, float)) or not isinstance(dy, (int, float)) or not isfinite(dx) or not isfinite(dy) or abs(dx) > 1.01 or abs(dy) > 1.01:
                return self.send_error(400)
            moved, collision = False, False
            if kind == "keyboard" and (dx or dy):
                length = (dx * dx + dy * dy) ** .5
                nx = max(24, min(616, APP.world.player_x + dx / length * 12))
                ny = max(24, min(336, APP.world.player_y + dy / length * 12))
                collision = cell_at((nx, ny)) in APP.map_cells
                APP.world.tick += 1
                if collision:
                    APP.world.idle_ticks += 1
                else:
                    APP.world.player_x, APP.world.player_y = nx, ny
                    APP.world.idle_ticks = 0
                    APP.world.facing = "E" if abs(dx) >= abs(dy) and dx >= 0 else "W" if abs(dx) >= abs(dy) else "S" if dy >= 0 else "N"
                    moved = True
                APP.agent.planned_path = []
            APP.last = {"action": kind, "reason": "manual_demo_recorded" if not collision else "collision_detected", "outcome": "SUCCESS" if not collision else "BLOCKED", "world": APP.world.snapshot(), "trace": [("InputCapture", "SUCCESS"), ("PixelLocalization", "SUCCESS"), ("ObstacleGuard", "BLOCKED" if collision else "CLEAR")]}
            row = APP.recorder.emit("demo_input", input=kind, dx=dx, dy=dy, moved=moved,
                                    collision=collision, cursor=cursor, camera=camera,
                                    player=[round(APP.world.player_x, 1), round(APP.world.player_y, 1)])
            APP.demo.append(row)
            return self.send_json({"moved": moved, "collision": collision, "count": len(APP.demo), **APP.json()})
        if route.path == "/api/demo/load":
            try:
                payload = self.read_json()
            except (ValueError, json.JSONDecodeError):
                return self.send_error(400)
            header, samples = payload.get("header"), payload.get("samples")
            if payload.get("format") != "agent-lab-demo-v1" or not isinstance(header, dict) or not isinstance(samples, list) or len(samples) > 10000:
                return self.send_error(400)
            saved_map = header.get("map")
            if not self.valid_map(saved_map): return self.send_error(400)
            scenario, saved_world = header.get("scenario"), header.get("world")
            if scenario not in SCENARIOS or not isinstance(saved_world, dict): return self.send_error(400)
            try:
                world = make_world(scenario)
                for key, lo, hi in (("player_x", 0, 640), ("player_y", 0, 360),
                                    ("target_x", 0, 640), ("target_y", 0, 360),
                                    ("player_health", 0, 100), ("target_health", 0, 100)):
                    value = saved_world.get(key, getattr(world, key))
                    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value) or not lo <= value <= hi:
                        return self.send_error(400)
                    setattr(world, key, value)
                clean = []
                for row in samples:
                    if not isinstance(row, dict) or row.get("event") != "demo_input" or row.get("input") not in ("keyboard", "mouse_drag", "mouse_zoom"):
                        return self.send_error(400)
                    for k in ("dx", "dy"):
                        v = row.get(k, 0)
                        if not isinstance(v, (int, float)) or not isfinite(v) or abs(v) > 1.01: return self.send_error(400)
                    player = row.get("player")
                    if not isinstance(player, list) or len(player) != 2 or any(not isinstance(v, (int, float)) or not isfinite(v) for v in player) or not (0 <= player[0] <= 640 and 0 <= player[1] <= 360):
                        return self.send_error(400)
                    camera = row.get("camera")
                    if camera is not None and (not isinstance(camera, dict) or
                            any(not isinstance(camera.get(k), (int, float)) or not isfinite(camera[k])
                                for k in ("yaw", "zoom", "pitch")) or
                            not (-180 <= camera["yaw"] <= 180 and .6 <= camera["zoom"] <= 1.6 and .45 <= camera["pitch"] <= 1)):
                        return self.send_error(400)
                    clean.append({"event": "demo_input", "input": row["input"], "dx": row.get("dx", 0),
                                  "dy": row.get("dy", 0), "player": player, "camera": camera})
            except (TypeError, ValueError):
                return self.send_error(400)
            APP.reset(scenario)
            APP.world = world
            APP.map_cells = {tuple(p) for p in saved_map}
            APP.demo_header = {"scenario": scenario, "world": world.snapshot(), "map": saved_map,
                               "source": "Agent Lab imported demo"}
            APP.demo = clean
            APP.recording = False
            APP.recorder.emit("demo_loaded", samples=len(clean), map_cells=len(APP.map_cells))
            return self.send_json({"count": len(clean), **APP.json()})
        if route.path == "/api/replay/start":
            if not APP.demo or not APP.demo_header:
                return self.send_error(409)
            header = APP.demo_header
            world_data = header.get("world", {})
            try:
                world = make_world(header["scenario"])
                for key in ("player_health", "target_health", "target_distance", "target_visible",
                            "vision_confidence", "player_stuck", "action_timeout", "unknown_state",
                            "targets", "player_x", "player_y", "target_x", "target_y", "combat_state",
                            "tick", "facing", "idle_ticks", "recovery_count"):
                    if key in world_data: setattr(world, key, world_data[key])
            except (KeyError, TypeError, ValueError):
                return self.send_error(400)
            APP.world = world
            APP.recorder = Recorder()
            APP.agent = Agent(APP.recorder)
            APP.map_cells = {tuple(p) for p in header["map"]}
            APP.replay_samples = list(APP.demo)
            APP.replay_index = 0
            APP.replay_active = bool(APP.replay_samples)
            APP.last = {"action": "replay_ready", "reason": "saved_map_and_demonstration_loaded",
                        "outcome": "RUNNING", "path": []}
            APP.recorder.emit("replay_started", keyboard_samples=len(APP.replay_samples), map_cells=len(APP.map_cells))
            if not APP.replay_active:
                return self.send_json({**APP.json(), "terminal": True})
            return self.send_json({**APP.json(), "terminal": False})
        if route.path == "/api/replay/step":
            if not APP.replay_active: return self.send_json({**APP.json(), "terminal": True})
            row = APP.replay_samples[APP.replay_index]
            if row.get("input") != "keyboard":
                APP.world.tick += 1
                APP.replay_index += 1
                done = APP.replay_index >= len(APP.replay_samples)
                APP.replay_active = not done
                APP.last = {"action": "replay_camera", "reason": "restore_recorded_camera_state",
                            "outcome": "SUCCESS" if done else "RUNNING", "path": [], "camera": row.get("camera"),
                            "trace": [("SavedMap", "SUCCESS"), ("CameraReplay", "SUCCESS")]}
                APP.recorder.emit("replay_camera", input=row["input"], camera=row.get("camera"))
                return self.send_json({**APP.json(), "terminal": done})
            target = tuple(float(v) for v in row["player"])
            here = (APP.world.player_x, APP.world.player_y)
            current_cell, target_cell = cell_at(here), cell_at(target)
            path = find_path(current_cell, target_cell, APP.map_cells, MAP_WIDTH, MAP_HEIGHT)
            if not path:
                APP.last = {"action": "safe_stop", "reason": "saved_route_blocked_and_no_astar_route",
                            "outcome": "SAFE_STOP", "path": []}
                APP.replay_active = False
                APP.recorder.emit("replay_stopped", reason=APP.last["reason"], sample=APP.replay_index)
                return self.send_json({**APP.json(), "terminal": True})
            aligned_last_step = (len(path) == 2 and
                                 ((path[1][0] != path[0][0] and target_cell[1] == current_cell[1]) or
                                  (path[1][1] != path[0][1] and target_cell[0] == current_cell[0])))
            waypoint = target if current_cell == target_cell or aligned_last_step else center_of(path[1] if len(path) > 1 else path[0])
            nxt = move_toward(here, waypoint, 14)
            if cell_at(nxt) in APP.map_cells and cell_at(nxt) != current_cell:
                APP.last = {"action": "safe_stop", "reason": "obstacle_guard_blocked_replay_step",
                            "outcome": "SAFE_STOP", "path": path}
                APP.replay_active = False
                return self.send_json({**APP.json(), "terminal": True})
            APP.world.player_x, APP.world.player_y = nxt
            dx, dy = nxt[0] - here[0], nxt[1] - here[1]
            if hypot(dx, dy) > .1:
                APP.world.facing = "E" if abs(dx) >= abs(dy) and dx >= 0 else "W" if abs(dx) >= abs(dy) else "S" if dy >= 0 else "N"
            APP.world.tick += 1
            reached = hypot(target[0] - nxt[0], target[1] - nxt[1]) <= 2
            if reached:
                APP.replay_index += 1
            done = APP.replay_index >= len(APP.replay_samples)
            APP.replay_active = not done
            APP.last = {"action": "replay_navigate", "reason": "astar_replan_around_saved_map",
                        "outcome": "SUCCESS" if done else "RUNNING", "path": path, "camera": row.get("camera"),
                        "trace": [("SavedMap", "SUCCESS"), ("AStarPlanner", "SUCCESS"),
                                  ("ObstacleGuard", "CLEAR"), ("ReplayWaypoint", "SUCCESS" if reached else "RUNNING")]}
            APP.recorder.emit("replay_step", sample=APP.replay_index, x=round(nxt[0], 1), y=round(nxt[1], 1),
                              waypoint_reached=reached, path_length=len(path))
            return self.send_json({**APP.json(), "terminal": done})
        if route.path == "/api/start":
            name = parse_qs(route.query).get("scenario", ["NORMAL_COMBAT"])[0]
            if name not in SCENARIOS: return self.send_error(400)
            APP.reset(name); APP.recorder.emit("simulation_started", scenario=name)
            return self.send_json(APP.json())
        if route.path == "/api/step":
            try:
                observation = self.read_json()
            except (ValueError, json.JSONDecodeError):
                return self.send_error(400)
            for key in ("player", "target"):
                point = observation.get(key)
                if point is not None and (not isinstance(point, list) or len(point) != 2 or
                        any(not isinstance(v, (int, float)) for v in point) or
                        not 0 <= point[0] < 640 or not 0 <= point[1] < 360):
                    return self.send_error(400)
            obstacles = observation.get("obstacles", [])
            if not isinstance(obstacles, list) or len(obstacles) > 220 or any(
                    not isinstance(p, list) or len(p) != 2 or any(not isinstance(v, int) for v in p) or
                    not (0 <= p[0] < 20 and 0 <= p[1] < 11) for p in obstacles):
                return self.send_error(400)
            APP.last = APP.agent.step(APP.world, observation)
            return self.send_json({**APP.json(), "terminal": APP.last["terminal"]})
        self.send_error(404)

    def log_message(self, fmt, *args): pass


def serve(host="127.0.0.1", port=8765):
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Agent Lab at http://{host}:{port} — local synthetic world only. Ctrl+C to stop.")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
