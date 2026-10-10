"""Module: weather (extracted verbatim from the original tools-server.py)."""

MODULE = {
    "kind": "tool",
    "slug": 'weather',
    "name": 'Weather',
    "icon": 'weather',
    "desc": 'Live temperature and conditions, powered by Open-Meteo',
    "title": 'Weather',
    "subtitle": 'Live temperature and conditions',
    "meta_desc": 'Live weather and temperature for any city, plus optional geolocation. Powered by Open-Meteo - no API key, no tracking.',
}



def page():
    return r"""
<div class="card">
<h2>Live weather</h2>
<p class="mut">Powered by Open-Meteo. No API key, no tracking, no cookies - the data never touches our servers.</p>
<label>City</label>
<input type="text" id="wcity" value="Zurich" placeholder="e.g. Zurich, Berlin, New York">
<button class="btn" id="wgo" type="button">Show weather</button>
<button class="btn" id="wloc" type="button" style="background:#1c1c2a;color:#c8a87c">Use my location</button>
<div id="wout" class="status"></div>
</div>
<script>
var WCODE={0:'Clear sky',1:'Mainly clear',2:'Partly cloudy',3:'Overcast',45:'Fog',48:'Rime fog',51:'Light drizzle',53:'Drizzle',55:'Dense drizzle',61:'Slight rain',63:'Rain',65:'Heavy rain',66:'Freezing rain',67:'Freezing rain',71:'Slight snow',73:'Snow',75:'Heavy snow',77:'Snow grains',80:'Rain showers',81:'Rain showers',82:'Violent showers',85:'Snow showers',86:'Snow showers',95:'Thunderstorm',96:'Thunderstorm with hail',99:'Thunderstorm with hail'};
function wshow(html,cls){var o=document.getElementById('wout');o.className='status '+(cls||'ok');o.innerHTML=html;o.style.display='block'}
async function wfetch(lat,lon,label){
  wshow('Loading...','ok');
  try{
    var u='https://api.open-meteo.com/v1/forecast?latitude='+lat+'&longitude='+lon+'&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code';
    var d=await (await fetch(u)).json();
    var c=d.current;
    var desc=WCODE[c.weather_code]||('Code '+c.weather_code);
    wshow('<div style="font-size:30px;font-weight:800;color:#e8d5b0">'+Math.round(c.temperature_2m)+'&deg;C</div>'
      +'<div style="font-size:14px;color:#c8a87c">'+desc+'</div>'
      +'<div style="color:#6a5d4a;font-size:12px;margin-top:6px">'+label+' &middot; feels '+Math.round(c.apparent_temperature)+'&deg;C &middot; humidity '+c.relative_humidity_2m+'% &middot; wind '+Math.round(c.wind_speed_10m)+' km/h</div>');
  }catch(e){wshow('Weather service unreachable.','err')}
}
document.getElementById('wgo').addEventListener('click',async function(){
  var name=document.getElementById('wcity').value.trim()||'Zurich';
  wshow('Searching...','ok');
  try{
    var g=await (await fetch('https://geocoding-api.open-meteo.com/v1/search?count=1&name='+encodeURIComponent(name))).json();
    if(!g.results||!g.results.length){wshow('City not found.','err');return}
    var r=g.results[0];
    wfetch(r.latitude,r.longitude,r.name+(r.country_code?', '+r.country_code:''));
  }catch(e){wshow('Search failed.','err')}
});
document.getElementById('wloc').addEventListener('click',function(){
  if(!navigator.geolocation){wshow('Geolocation not supported.','err');return}
  wshow('Getting your location...','ok');
  navigator.geolocation.getCurrentPosition(function(p){wfetch(p.coords.latitude,p.coords.longitude,'Your location')},function(){wshow('Location permission denied.','err')});
});
</script>
"""
