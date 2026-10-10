"""Module: calculator (extracted verbatim from the original tools-server.py)."""

MODULE = {
    "kind": "tool",
    "slug": 'calculator',
    "name": 'Calculator',
    "icon": 'calc',
    "desc": 'Fast online calculator with a safe expression parser',
    "title": 'Calculator',
    "subtitle": 'Free online calculator',
    "meta_desc": 'Free online calculator with parentheses, percentages and decimals. Runs in your browser, nothing uploaded.',
}



def page():
    return r"""
<div class="card">
<h2>Calculator</h2>
<input type="text" id="cexpr" class="calc-in" inputmode="text" placeholder="e.g. (12+8)*3/4">
<div id="cout" class="calc-out">0</div>
<div class="calc-grid">
<button type="button" data-k="C" class="op">C</button>
<button type="button" data-k="(" class="op">(</button>
<button type="button" data-k=")" class="op">)</button>
<button type="button" data-k="back" class="op">&#9003;</button>
<button type="button" data-k="7">7</button>
<button type="button" data-k="8">8</button>
<button type="button" data-k="9">9</button>
<button type="button" data-k="/" class="op">/</button>
<button type="button" data-k="4">4</button>
<button type="button" data-k="5">5</button>
<button type="button" data-k="6">6</button>
<button type="button" data-k="*" class="op">&times;</button>
<button type="button" data-k="1">1</button>
<button type="button" data-k="2">2</button>
<button type="button" data-k="3">3</button>
<button type="button" data-k="-" class="op">&minus;</button>
<button type="button" data-k="0">0</button>
<button type="button" data-k=".">.</button>
<button type="button" data-k="%" class="op">%</button>
<button type="button" data-k="+" class="op">+</button>
</div>
<p class="mut" style="margin-top:12px">Safe parser - no eval. Press Enter to calculate.</p>
</div>
<script>
function evalExpr(s){
  s=String(s).replace(/\s+/g,'');
  var i=0;
  function peek(){return s[i]}
  function num(){var st=i;while(i<s.length&&/[0-9.]/.test(s[i]))i++;if(st===i)throw new Error('bad');return parseFloat(s.slice(st,i))}
  function factor(){if(peek()==='('){i++;var v=add();if(peek()===')')i++;else throw new Error('bad');return v}if(peek()==='-'){i++;return -factor()}if(peek()==='+'){i++;return factor()}return num()}
  function mul(){var v=factor();while(peek()==='*'||peek()==='/'||peek()==='%'){var op=s[i++];var r=factor();v=op==='*'?v*r:(op==='/'?v/r:v%r)}return v}
  function add(){var v=mul();while(peek()==='+'||peek()==='-'){var op=s[i++];var r=mul();v=op==='+'?v+r:v-r}return v}
  var out=add();
  if(i<s.length)throw new Error('bad');
  if(!isFinite(out))throw new Error('bad');
  return out;
}
var ci=document.getElementById('cexpr'),co=document.getElementById('cout');
function calcUpd(){var v=ci.value.trim();if(!v){co.textContent='0';return}try{co.textContent=evalExpr(v)}catch(e){co.textContent='\u2026'}}
ci.addEventListener('input',calcUpd);
ci.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();calcUpd()}});
document.querySelectorAll('.calc-grid button').forEach(function(b){
  b.addEventListener('click',function(){
    var k=b.getAttribute('data-k');
    if(k==='C')ci.value='';
    else if(k==='back')ci.value=ci.value.slice(0,-1);
    else ci.value+=k;
    ci.focus();calcUpd();
  });
});
</script>
"""
