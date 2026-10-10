"""Module: generator (extracted verbatim from the original tools-server.py)."""

MODULE = {
    "kind": "tool",
    "slug": 'generator',
    "name": 'Generator',
    "icon": 'gen',
    "desc": 'Passwords and random numbers, generated locally',
    "title": 'Generator',
    "subtitle": 'Password and random number generator',
    "meta_desc": 'Generate strong passwords and random numbers locally in your browser. Free, no sign-up, nothing stored.',
}



def page():
    return r"""
<div class="card">
<h2>Password generator</h2>
<label>Length: <span id="plenL">16</span></label>
<input type="range" id="plen" min="6" max="64" value="16" style="width:100%" oninput="document.getElementById('plenL').textContent=this.value">
<div style="margin:12px 0;font-size:13px;color:#9a8d7a">
<label style="display:inline;color:inherit"><input type="checkbox" id="pu" checked> A-Z</label>
<label style="display:inline;color:inherit;margin-left:12px"><input type="checkbox" id="pl" checked> a-z</label>
<label style="display:inline;color:inherit;margin-left:12px"><input type="checkbox" id="pd" checked> 0-9</label>
<label style="display:inline;color:inherit;margin-left:12px"><input type="checkbox" id="ps" checked> !@#</label>
</div>
<div id="pout" class="calc-out mono" style="font-size:16px;text-align:left;word-break:break-all">click generate</div>
<button class="btn" id="pgen" type="button">Generate</button>
<button class="btn" id="pcopy" type="button" style="background:#1c1c2a;color:#c8a87c">Copy</button>
</div>
<div class="card">
<h2>Random number</h2>
<div class="row2">
<input type="text" id="rmin" value="1"><span class="mut">to</span><input type="text" id="rmax" value="100">
<button class="btn" id="rgo" type="button">Roll</button>
</div>
<div id="rout" class="calc-out" style="font-size:28px">-</div>
</div>
<script>
function randInt(max){var a=new Uint32Array(1);crypto.getRandomValues(a);return a[0]%max}
document.getElementById('pgen').addEventListener('click',function(){
  var L=parseInt(document.getElementById('plen').value,10);
  var sets='';
  if(document.getElementById('pu').checked)sets+='ABCDEFGHJKLMNPQRTUVWXYZ';
  if(document.getElementById('pl').checked)sets+='abcdefghijkmnopqrstuvwxyz';
  if(document.getElementById('pd').checked)sets+='23456789';
  if(document.getElementById('ps').checked)sets+='!@#$%^&*-_=+?';
  if(!sets)sets='abcdefghijkmnopqrstuvwxyz';
  var out='';
  for(var i=0;i<L;i++)out+=sets[randInt(sets.length)];
  document.getElementById('pout').textContent=out;
});
document.getElementById('pcopy').addEventListener('click',function(){var b=this;var t=document.getElementById('pout').textContent;if(navigator.clipboard)navigator.clipboard.writeText(t);b.textContent='Copied';setTimeout(function(){b.textContent='Copy'},1200)});
document.getElementById('rgo').addEventListener('click',function(){var mn=parseInt(document.getElementById('rmin').value,10);var mx=parseInt(document.getElementById('rmax').value,10);if(isNaN(mn))mn=0;if(isNaN(mx))mx=100;if(mx<mn){var t=mn;mn=mx;mx=t}document.getElementById('rout').textContent=mn+randInt(mx-mn+1)});
</script>
"""
