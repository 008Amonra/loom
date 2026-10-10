"""Module: email (extracted verbatim from the original tools-server.py)."""

MODULE = {
    "kind": "tool",
    "slug": 'email',
    "name": 'Email Starter',
    "icon": 'mail',
    "desc": 'Draft the opening of an email in seconds',
    "title": 'Email Starter',
    "subtitle": 'Draft the opening of an email',
    "meta_desc": 'Generate a clean opening paragraph for your email in seconds. Choose a purpose and tone - nothing is sent anywhere.',
}



def page():
    return r"""
<div class="card">
<h2>Email starter</h2>
<p class="mut">Fill the blanks and get a clean opening you can paste into any mail client. Nothing is sent anywhere - it all runs in your browser.</p>
<label>To (name)</label>
<input type="text" id="emTo" placeholder="e.g. Mr. Mueller">
<label>Purpose</label>
<select id="emPurpose">
<option>Request information</option>
<option>Apply for a job</option>
<option>Follow up</option>
<option>Apologise for a delay</option>
<option>Schedule a meeting</option>
<option>Ask for a quote</option>
<option>Cancel or reschedule</option>
</select>
<label>Tone</label>
<select id="emTone"><option>Formal</option><option>Friendly</option><option>Neutral</option></select>
<label>Your name</label>
<input type="text" id="emFrom" placeholder="e.g. Jace">
<button class="btn" id="emGo" type="button">Draft it</button>
<textarea id="emOut" placeholder="Your draft appears here..."></textarea>
<button class="btn" id="emCopy" type="button" style="background:#1c1c2a;color:#c8a87c">Copy</button>
</div>
<script>
var EMAP={
'Request information':{s:'Request for information',i:'I hope you are well. I am writing to ask for some details regarding',c:'Thank you in advance for your help. Please let me know if you need anything further from me.'},
'Apply for a job':{s:'Application',i:'I am writing to express my interest in the advertised position. I believe my background fits your requirements and I would welcome the chance to contribute to your team.',c:'Thank you for considering my application. I look forward to hearing from you.'},
'Follow up':{s:'Following up',i:'I am following up on my previous message. I wanted to check whether you have had a chance to look into',c:'Thank you for your time. I would appreciate a brief update when convenient.'},
'Apologise for a delay':{s:'Apologies for the delay',i:'I would like to apologise for the delay in my reply. I am writing regarding',c:'Thank you for your patience and understanding.'},
'Schedule a meeting':{s:'Meeting request',i:'I would like to arrange a short meeting to discuss',c:'Please let me know a time that suits you and I will make it work.'},
'Ask for a quote':{s:'Quote request',i:'I would like to request a quote for',c:'Please include your pricing and expected timeline. Thank you.'},
'Cancel or reschedule':{s:'Rescheduling',i:'I need to cancel or move our appointment regarding',c:'I am sorry for any inconvenience and would be glad to find a new time.'}
};
function emBuild(){
  var to=document.getElementById('emTo').value.trim()||'there';
  var from=document.getElementById('emFrom').value.trim()||'[Your name]';
  var p=document.getElementById('emPurpose').value;
  var tone=document.getElementById('emTone').value;
  var m=EMAP[p]||EMAP['Request information'];
  var hi=tone==='Friendly'?'Hi ':(tone==='Neutral'?'Hello ':'Dear ');
  var tail=tone==='Friendly'?'Best,':(tone==='Neutral'?'Regards,':'Kind regards,');
  var body=hi+to+',\n\n'+m.i+' the matter mentioned above.\n\n'+m.c+'\n\n'+tail+'\n'+from;
  document.getElementById('emOut').value='Subject: '+m.s+'\n\n'+body;
}
document.getElementById('emGo').addEventListener('click',emBuild);
document.getElementById('emCopy').addEventListener('click',function(){var b=this;var t=document.getElementById('emOut');t.select();if(navigator.clipboard)navigator.clipboard.writeText(t.value);else document.execCommand('copy');b.textContent='Copied';setTimeout(function(){b.textContent='Copy'},1200)});
</script>
"""
