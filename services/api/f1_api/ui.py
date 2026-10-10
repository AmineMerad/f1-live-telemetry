"""Single-page UI: session explorer + head-to-head + prediction panel."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>F1 Live Intelligence (local)</title>
<style>
body{font-family:system-ui,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem}
section{border:1px solid #ddd;border-radius:8px;padding:1rem;margin-bottom:1rem}
table{border-collapse:collapse;width:100%;font-size:.85rem}
td,th{border:1px solid #ddd;padding:.25rem .5rem;text-align:right}
th{background:#f5f5f5}td.lap,th.lap{text-align:left}
tr.pit{background:#fff7e6}tr.fast td{font-weight:bold}
img{max-width:100%}.row{display:flex;gap:.5rem;flex-wrap:wrap;align-items:end}
label{display:flex;flex-direction:column;font-size:.8rem}
.mut{color:#666;font-size:.8rem}
</style></head><body>
<h1>F1 Live Intelligence <span class="mut">local scaffold</span></h1>

<section><h2>1. Session</h2><div class="row">
<label>Year<input id="year" value="2024" size="6"></label>
<label>Location<input id="loc" value="Monza" size="12"></label>
<button onclick="findSessions()">Find</button>
<label>Session<select id="session"></select></label>
</div><div id="sessinfo" class="mut"></div></section>

<section><h2>2. Head-to-head laps</h2><div class="row">
<label>Driver A<select id="drvA"></select></label>
<label>Driver B<select id="drvB"></select></label>
<button onclick="loadLaps()">Load laps</button>
</div><div id="lapinfo" class="mut"></div>
<table id="laps"><thead><tr><th class="lap">Lap</th><th id="hA">A</th><th id="hB">B</th><th>&Delta; A&minus;B</th></tr></thead><tbody></tbody></table></section>

<section><h2>3. Telemetry &amp; plots</h2><div class="row">
<label>Driver<select id="drvT"></select></label>
<button onclick="loadTel()">Telemetry summary</button>
<button onclick="loadPlots()">Plots</button>
</div><div id="telinfo" class="mut"></div>
<div><img id="plotLaps" alt="lap progression"><img id="plotSpeed" alt="speed trace"></div></section>

<section><h2>4. Prediction workflows (Temporal)</h2><div class="row">
<label>SessionId<input id="sessid" value="monza-2024" size="16"></label>
<button onclick="loadWf()">List</button>
<label><input type="checkbox" id="autoref" checked> auto-refresh 10s</label>
</div><table id="wfs"><thead><tr><th class="lap">Workflow ID</th><th>Status</th><th>Start</th></tr></thead><tbody></tbody></table>
<div id="wfinfo" class="mut"></div></section>

<script>
const $=id=>document.getElementById(id);
const key=()=>$("session").value;
const pair=()=>$("drvA").value+"-"+$("drvB").value;
async function findSessions(){
  const r=await fetch(`/api/sessions?year=${$("year").value}&location=${$("loc").value}`);
  const ss=await r.json();
  $("session").innerHTML=ss.map(s=>`<option value="${s.session_key}">${s.location} ${s.session_name} (${s.date_start.slice(0,10)}) [${s.session_key}]</option>`).join("");
  $("sessinfo").textContent=ss.length?`${ss.length} session(s)`:"none found";
  if(ss.length)loadDrivers();
}
async function loadDrivers(){
  const r=await fetch(`/api/session/${key()}/drivers`);
  const ds=await r.json();
  const opts=ds.map(d=>`<option value="${d.acronym}" data-num="${d.driver_number}">${d.acronym} (#${d.driver_number}, ${d.team})</option>`).join("");
  for(const id of["drvA","drvB","drvT"]){$(id).innerHTML=opts;}
  $("drvA").selectedIndex=0;$("drvB").selectedIndex=1;$("drvT").selectedIndex=0;
}
async function loadLaps(){
  const [A,B]=pair().split("-");$("hA").textContent=A;$("hB").textContent=B;
  const r=await fetch(`/api/session/${key()}/laps?pair=${A}-${B}`);
  const {laps}=await r.json();
  const best={};for(const l of laps){for(const c of [A,B]){const v=l[c];
    if(v!==null&&v!==undefined&&(!best[c]||v<best[c]))best[c]=v;}}
  const tb=$("laps").querySelector("tbody");
  tb.innerHTML=laps.map(l=>{
    const f=(l[A]===best[A]||l[B]===best[B])?"fast":"";
    return `<tr class="${l.pit_out?"pit ":""}${f}"><td class="lap">${l.lap_number}${l.pit_out?" (pit)":""}</td><td>${l[A]??"—"}</td><td>${l[B]??"—"}</td><td>${l.delta??"—"}</td></tr>`;}).join("");
  $("lapinfo").textContent=`${laps.length} laps, ${laps.filter(l=>l.pit_out).length} pit-out`;
}
async function loadTel(){
  const num=$("drvT").selectedOptions[0].dataset.num;
  const r=await fetch(`/api/session/${key()}/telemetry?driver_number=${num}`);
  const t=await r.json();
  $("telinfo").textContent=`${t.samples} samples, top ${t.top_speed} km/h, full throttle ${(t.full_throttle_share*100).toFixed(0)}%, braking ${(t.braking_share*100).toFixed(0)}%`;
}
function loadPlots(){
  const p=pair();
  $("plotLaps").src=`/api/session/${key()}/plot?pair=${p}&kind=laps`;
  $("plotSpeed").src=`/api/session/${key()}/plot?pair=${p}&kind=speed`;
}
async function loadWf(){
  const sid=$("sessid").value;
  const url=sid?`/api/workflows?session_id=${sid}`:"/api/workflows";
  const r=await fetch(url);
  if(!r.ok){$("wfinfo").textContent=`Temporal unavailable (${r.status}) — is the stack up?`;return;}
  const {query,workflows}=await r.json();
  $("wfs").querySelector("tbody").innerHTML=workflows.map(w=>`<tr><td class="lap">${w.id}</td><td>${w.status}</td><td>${w.start_time||""}</td></tr>`).join("");
  $("wfinfo").textContent=`query: ${query} — ${workflows.length} run(s)`;
}
setInterval(()=>{if($("autoref").checked)loadWf();},10000);
findSessions();loadWf();
</script></body></html>
"""


@router.get("/ui", response_class=HTMLResponse)
def ui() -> str:
    return PAGE
