var e=document.querySelector(`#show-drafts`),t=document.querySelector(`#run-council`),n=document.querySelector(`#refresh-review`),r=document.querySelector(`#review-status`),i=document.querySelector(`#review-list`),a=document.querySelector(`#council-output`),o=`45dgof8ArticleSeed`,s=[];function c(e){return String(e||``).replace(/[&<>'"]/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,"'":`&#39;`,'"':`&quot;`})[e])}function l(){return s.filter(t=>e.checked||t.status!==`draft`)}async function u(e,t){r.textContent=`Setting ${e} to ${t}...`;let n=await fetch(`/api/local-publisher/set-article-status`,{method:`POST`,headers:{"content-type":`application/json`},body:JSON.stringify({slug:e,status:t})}),i=await n.json();if(!n.ok)throw Error(i.error||`Status update failed`);let a=s.find(t=>t.slug===e);a&&(a.status=t),r.textContent=`${e} is now ${t}. Refresh the newspaper page to see changes.`,m()}async function d(e){let t=e.status===`published`?`DELETE published article "${e.title}"? This removes it from the paper.`:`Delete draft "${e.title}"?`;if(confirm(t)&&!(e.status===`published`&&!confirm(`This article is already published. Really delete the file?`))){r.textContent=`Deleting ${e.slug}...`;try{let t=await fetch(`/api/local-publisher/delete-article`,{method:`POST`,headers:{"content-type":`application/json`},body:JSON.stringify({slug:e.slug,confirmPublished:e.status===`published`})}),n=await t.json();if(!t.ok)throw Error(n.error||`Delete failed`);s=s.filter(t=>t.slug!==e.slug),r.textContent=`Deleted ${e.filename}.`,m()}catch(e){r.textContent=`Could not delete article: ${e.message}.`}}}function f(e){localStorage.setItem(o,JSON.stringify({title:e.title,dek:e.dek,section:e.section,reporter:e.reporter,url:e.sources?.[0]||``,discussion:e.sources?.[1]||``,tags:e.tags||[],scores:e.scores||{},body:e.body||``})),window.location.href=`/pressroom/article-desk/`}function p(e){let t=document.createElement(`article`);return t.className=`lead-result panel status-${e.status}`,t.innerHTML=`
        <span class="label">${c(e.status)} / ${c(e.section)}</span>
        <h2>${c(e.title)}</h2>
        <p>${c(e.dek)}</p>
        <p class="meta">${c(e.filename)} | Reporter: ${c(e.reporter)} | Date: ${c(e.date)}</p>
        <div class="scoreboard mini-scoreboard">
          <div>Weirdness<br />${e.scores.weirdness}/5</div>
          <div>Usefulness<br />${e.scores.usefulness}/5</div>
          <div>Timeliness<br />${e.scores.timeliness}/5</div>
          <div>Confidence<br />${e.scores.confidence}/5</div>
        </div>
        <div class="button-row">
          <button data-action="draft" type="button">Send back to draft</button>
          <button data-action="approved" type="button">Approve preview</button>
          <button data-action="published" type="button">Publish</button>
          <button data-action="redo" type="button">Redo in Article Desk</button>
          <button data-action="delete" type="button" class="danger-button">Delete</button>
        </div>
      `,t.querySelector(`[data-action="draft"]`).addEventListener(`click`,()=>u(e.slug,`draft`)),t.querySelector(`[data-action="approved"]`).addEventListener(`click`,()=>u(e.slug,`approved`)),t.querySelector(`[data-action="published"]`).addEventListener(`click`,()=>u(e.slug,`published`)),t.querySelector(`[data-action="redo"]`).addEventListener(`click`,()=>f(e)),t.querySelector(`[data-action="delete"]`).addEventListener(`click`,()=>d(e)),t}function m(){i.innerHTML=``;let e=l();if(!e.length){i.innerHTML=`<p class="small-note">No articles match this review switch.</p>`;return}e.forEach(e=>i.appendChild(p(e)))}function h(e){if(a.hidden=!1,a.innerHTML=`
        <div class="panel">
          <span class="label">Automated Editorial Meeting</span>
          <h2>Council Recommendation</h2>
          <p><strong>Cadence:</strong> ${c(e.cadence)}</p>
          <p>${c(e.rationale)}</p>
          <p class="small-note">Backlog considered: ${e.backlogCount} unpublished article(s).</p>
        </div>
      `,!e.candidates.length){a.insertAdjacentHTML(`beforeend`,`<p class="small-note">No unpublished candidates yet. Send reporters or save drafts first.</p>`);return}e.candidates.forEach((e,t)=>{let n=document.createElement(`article`);n.className=`panel council-card`,n.innerHTML=`
          <span class="label">Pick ${t+1} / ${c(e.recommendation)}</span>
          <h2>${c(e.title)}</h2>
          <p class="meta">Council score ${e.score} | status: ${c(e.status)} | slug: ${c(e.slug)}</p>
          <div class="council-voices">
            ${e.voices.map(e=>`<p><strong>${c(e.voice)}:</strong> ${c(e.note)}</p>`).join(``)}
          </div>
          <div class="button-row">
            <button data-action="approved" type="button">Approve this pick</button>
            <button data-action="published" type="button">Publish this pick</button>
          </div>
        `,n.querySelector(`[data-action="approved"]`).addEventListener(`click`,()=>u(e.slug,`approved`)),n.querySelector(`[data-action="published"]`).addEventListener(`click`,()=>u(e.slug,`published`)),a.appendChild(n)})}async function g(){r.textContent=`The editorial council is meeting...`,t.disabled=!0;try{let e=await fetch(`/api/local-publisher/editorial-council`,{method:`POST`}),t=await e.json();if(!e.ok)throw Error(t.error||`Council failed`);h(t.meeting),r.textContent=`Editorial council returned a recommendation.`}catch(e){r.textContent=`Council could not meet: ${e.message}.`}finally{t.disabled=!1}}async function _(){r.textContent=`Loading article files...`;try{let e=await fetch(`/api/local-publisher/list-articles`,{method:`POST`}),t=await e.json();if(!e.ok)throw Error(t.error||`Could not list articles`);s=t.articles||[],r.textContent=`Loaded ${s.length} articles. Published items appear in the normal paper; approved items are review-ready.`,m()}catch(e){r.textContent=`Could not reach local publisher helper: ${e.message}. Start with start-newspaper.sh.`}}n.addEventListener(`click`,_),t.addEventListener(`click`,g),e.addEventListener(`change`,m),_();