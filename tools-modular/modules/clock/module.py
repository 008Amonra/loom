"""Module: clock (extracted verbatim from the original tools-server.py)."""

MODULE = {
    "kind": "tool",
    "slug": 'clock',
    "name": 'Live Clock',
    "icon": 'clock',
    "desc": 'Current time and world clock, updating live',
    "title": 'Live Clock',
    "subtitle": 'Current time and world clock',
    "meta_desc": 'Live clock - current local time and a world clock (Zurich, London, New York, Tokyo and more), updating every second.',
}



def page():
    return r"""
<div class="card">
<h2>Current time</h2>
<p class="mut">Updates every second. Your timezone is detected automatically.</p>
<div id="clk" class="bigclock">--:--:--</div>
<div id="clkdate" class="mut2">&nbsp;</div>
</div>
<div class="card">
<h2>World clock</h2>
<div id="worldclk" class="wgrid"></div>
</div>
<script>
function ckP2(n){return String(n).padStart(2,'0')}
function ckTick(){
  var d=new Date();
  document.getElementById('clk').textContent=ckP2(d.getHours())+':'+ckP2(d.getMinutes())+':'+ckP2(d.getSeconds());
  document.getElementById('clkdate').textContent=d.toLocaleDateString(undefined,{weekday:'long',year:'numeric',month:'long',day:'numeric'});
  var zones=[['Zurich','Europe/Zurich'],['London','Europe/London'],['New York','America/New_York'],['Tokyo','Asia/Tokyo'],['Sydney','Australia/Sydney'],['Dubai','Asia/Dubai']];
  var html='';
  for(var i=0;i<zones.length;i++){
    var t=new Intl.DateTimeFormat(undefined,{timeZone:zones[i][1],hour:'2-digit',minute:'2-digit',hour12:false}).format(d);
    html+='<div class="wcell"><div class="w-label">'+zones[i][0]+'</div><div class="w-main mono">'+t+'</div></div>';
  }
  document.getElementById('worldclk').innerHTML=html;
}
ckTick();setInterval(ckTick,1000);
</script>
"""
