#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(__dirname, 'whisperer-data');

if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

const TG_TOKEN = process.env.TG_BOT_TOKEN;
const TG_CHAT = process.env.TG_WHISPER_CHAT || '5032947163';
const HOURLY_RATE = process.env.WHISPERER_RATE || '50';
const CURRENCY = process.env.WHISPERER_CURRENCY || 'SFr.';

function projectPath(name) {
  return path.join(DATA_DIR, name.toLowerCase().replace(/[^a-z0-9-]/g, '-') + '.json');
}

function load(name) {
  const fp = projectPath(name);
  if (!fs.existsSync(fp)) return null;
  return JSON.parse(fs.readFileSync(fp, 'utf-8'));
}

function save(proj) {
  fs.writeFileSync(projectPath(proj.name), JSON.stringify(proj, null, 2));
}

function listProjects() {
  if (!fs.existsSync(DATA_DIR)) return [];
  return fs.readdirSync(DATA_DIR)
    .filter(f => f.endsWith('.json'))
    .map(f => JSON.parse(fs.readFileSync(path.join(DATA_DIR, f), 'utf-8')));
}

function now() { return new Date().toISOString(); }

function politeDate(iso) {
  return new Date(iso).toLocaleString('de-CH', {
    day: 'numeric', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

// --- Brief analysis ---
function analyzeBrief(text) {
  const contradictions = [];
  const vaguePoints = [];
  const requirements = [];

  const vague = [/nice/ig, /cool/ig, /\bmodern\b/ig, /sleek/ig, /fancy/ig, /\bgood\b/ig, /\bbetter\b/ig, /\bfast\b/ig, /simple but/ig, /easy/ig];
  const lines = text.split('\n').filter(l => l.trim());

  for (const pattern of vague) {
    if (pattern.test(text)) {
      const phrase = pattern.source.replace(/\\b/ig, '').replace(/[\\/]/g, '');
      vaguePoints.push(`"${phrase}" is subjective — could you define what it means in concrete terms?`);
    }
  }

  if (/simple.*full.feature|minimal.*powerful|basic.*advanced|clean.*complex/i.test(text)) {
    contradictions.push('You asked for "simple" and "full-featured" in the same brief — let me help you prioritise which matters more.');
  }
  if (/cheap.*high.quality|low.cost.*premium/i.test(text)) {
    contradictions.push('"Low cost" and "high quality" are in tension. Which is the priority for this phase?');
  }
  if (/fast.*perfect|quick.*flawless/i.test(text)) {
    contradictions.push('Speed and perfection rarely coexist. Shall I plan for a solid first iteration or a polished final product?');
  }
  if (/asap|yesterday|urgent|right.?away/i.test(text)) {
    contradictions.push('If there is a hard deadline, please tell me the date — "ASAP" means different things to different people.');
  }
  if (/i think|maybe|perhaps|possibly|something like/i.test(text) && !/must|need|require/i.test(text)) {
    vaguePoints.push('There are a lot of maybes here. Could you tell me what you definitely need vs. what would be nice?');
  }

  const reqMatches = text.match(/[•\-\*]\s*(.+)/g);
  if (reqMatches) {
    reqMatches.forEach(r => {
      const clean = r.replace(/^[•\-\*]\s*/, '').trim();
      if (clean.length > 5) requirements.push(clean);
    });
  }

  if (requirements.length === 0) {
    const sentences = text.split(/[.!?\n]+/).filter(s => s.trim().length > 15);
    if (sentences.length > 0) {
      sentences.slice(0, 6).forEach(s => requirements.push(s.trim()));
    }
  }

  return {
    requirements,
    contradictions,
    vaguePoints,
    requirementCount: requirements.length,
    hasContradictions: contradictions.length > 0,
    isVague: requirements.length < 3
  };
}

// --- Commands ---

function cmdInit(args) {
  const name = args[0];
  if (!name) return 'I need a project name to get started. Just "init <Project Name>" will do.';
  if (load(name)) return `I already have a project called "${name}". Use "status" to check it or start a new brief.`;

  const description = args.slice(1).join(' ') || 'No description provided.';
  const proj = {
    name, description,
    status: 'active',
    created: now(),
    updated: now(),
    briefs: [{ text: description, analysis: analyzeBrief(description), timestamp: now() }],
    signedBrief: null,
    scopeChanges: [],
    timeLog: [],
    closeOut: null,
    cooldownUntil: null,
    changesInSession: 0
  };
  save(proj);

  const a = proj.briefs[0].analysis;
  let msg = `Project "${name}" created. I'll take care of it.\n\n`;
  if (a.isVague) {
    msg += `The brief is somewhat light on detail — fewer than 3 concrete requirements. Could you walk me through what you actually need?\n`;
    if (a.vaguePoints.length > 0) {
      msg += `\nA few things I noticed:\n`;
      msg += a.vaguePoints.slice(0, 3).map(p => `- ${p}`).join('\n');
    }
  } else {
    msg += `I see ${a.requirementCount} potential requirements in your brief.\n`;
    if (a.contradictions.length > 0) {
      msg += `\nThere are a couple of things worth clarifying:\n`;
      msg += a.contradictions.map(c => `- ${c}`).join('\n');
    }
    if (a.vaguePoints.length > 0) {
      msg += `\nAlso worth tightening:\n`;
      msg += a.vaguePoints.slice(0, 3).map(p => `- ${p}`).join('\n');
    }
  }
  msg += `\n\nOnce you are ready, "brief "${name}" <details>" to send me the full project brief.`;
  return msg;
}

function cmdBrief(args) {
  const name = args[0];
  if (!name) return 'Which project? Usage: brief "<project>" <brief text or @file>';

  const proj = load(name);
  if (!proj) return `I don\'t have a project called "${name}". Start one with "init" first.`;

  const text = args.slice(1).join(' ');
  if (!text) return 'I need some content for the brief. Paste the client\'s message or point me to a file with @filename.';

  let briefText = text;
  if (text.startsWith('@')) {
    const fp = path.resolve(text.slice(1));
    if (!fs.existsSync(fp)) return `I couldn\'t find the file at ${fp}.`;
    briefText = fs.readFileSync(fp, 'utf-8');
  }

  const analysis = analyzeBrief(briefText);
  proj.briefs.push({ text: briefText, analysis, timestamp: now() });
  proj.updated = now();
  save(proj);

  let reply = `I\'ve processed the brief for "${proj.name}". Here is my reading:\n\n`;

  reply += `**Requirements identified:** ${analysis.requirements.length}\n`;
  if (analysis.requirements.length > 0) {
    reply += analysis.requirements.slice(0, 6).map(r => `- ${r}`).join('\n') + '\n\n';
  }

  if (analysis.contradictions.length > 0) {
    reply += `**Needs clarification:**\n`;
    reply += analysis.contradictions.map(c => `- ${c}`).join('\n') + '\n\n';
  }

  if (analysis.vaguePoints.length > 0) {
    reply += `**Could be more specific:**\n`;
    reply += analysis.vaguePoints.slice(0, 4).map(p => `- ${p}`).join('\n') + '\n\n';
  }

  reply += `I recommend we send this back to the client for alignment before I proceed. `;
  reply += `Would you like me to draft a structured brief for sign-off? (Use "sign-off "${name}"" to generate one.)`;

  return reply;
}

function cmdSignOff(args) {
  const name = args[0];
  if (!name) return 'Which project? Usage: sign-off "<project>" <scope, deliverables, timeline>';

  const proj = load(name);
  if (!proj) return `I don\'t have a project called "${name}".`;

  const latest = proj.briefs[proj.briefs.length - 1];
  if (!latest) return 'No brief on file to base a sign-off on. Send a brief first.';

  const extra = args.slice(1).join(' ');
  const scope = extra || latest.analysis.requirements.slice(0, 5).join('; ');

  const signed = {
    scope,
    deliverables: scope.split(/[;,]/).map(s => s.trim()).filter(Boolean),
    revisionCount: 2,
    signedDate: now()
  };
  proj.signedBrief = signed;
  proj.updated = now();
  proj.changesInSession = 0;
  save(proj);

  const delSav = signed.deliverables.length;
  let doc = `**STRUCTURED BRIEF FOR SIGN-OFF**\n`;
  doc += `Project: ${proj.name}\n`;
  doc += `Date: ${politeDate(now())}\n\n`;
  doc += `**Scope:**\n`;
  signed.deliverables.forEach(d => doc += `- ${d}\n`);
  doc += `\n**Revisions included:** ${signed.revisionCount}\n`;
  doc += `**Timeline:** To be determined with the builder\n\n`;
  doc += `_Note: Additional changes beyond this scope will be quoted separately._\n\n`;
  doc += `Once the client signs off, I\'ll lock this as the baseline for tracking scope drift.`;

  return doc;
}

function cmdScopeChange(args) {
  const name = args[0];
  if (!name) return 'Which project? Usage: scope-change "<project>" <description>';

  const proj = load(name);
  if (!proj) return `I don\'t have a project called "${name}".`;

  if (proj.status === 'completed') return `"${proj.name}" is closed. I can\'t log new changes.`;

  if (proj.cooldownUntil) {
    const until = new Date(proj.cooldownUntil);
    if (until > new Date()) {
      const diff = Math.ceil((until - new Date()) / 3600000);
      return `There is a cooldown on "${proj.name}" for another ${diff}h. The last session had multiple changes. Let\'s let things settle before we add more.`;
    }
    proj.cooldownUntil = null;
    proj.changesInSession = 0;
  }

  const description = args.slice(1).join(' ');
  if (!description) return 'What changed? Tell me what the client requested.';

  const estimatedHours = extractHours(description) || 2;
  proj.changesInSession++;

  const totalHoursBefore = proj.scopeChanges.reduce((s, c) => s + (c.hours || 0), 0);
  const totalHoursAfter = totalHoursBefore + estimatedHours;

  const entry = {
    request: description,
    hours: estimatedHours,
    cumulativeHours: totalHoursAfter,
    timestamp: now()
  };

  if (proj.signedBrief && proj.changesInSession > proj.signedBrief.revisionCount) {
    entry.quote = `Revision limit exceeded. Additional cost: ${CURRENCY} ${(estimatedHours * HOURLY_RATE).toFixed(0)}`;
    entry.overQuota = true;
  }

  proj.scopeChanges.push(entry);
  proj.updated = now();

  if (proj.changesInSession >= 3) {
    proj.cooldownUntil = new Date(Date.now() + 86400000).toISOString();
  }

  save(proj);

  let msg = `Scope change logged for "${proj.name}".\n\n`;
  msg += `**Request:** ${description}\n`;
  msg += `**Estimated impact:** ${estimatedHours}h\n`;
  if (proj.signedBrief) {
    const remaining = Math.max(0, proj.signedBrief.revisionCount - proj.changesInSession + 1);
    msg += `**Revisions remaining in scope:** ${remaining}\n`;
  }
  msg += `**Cumulative extra time:** ${totalHoursAfter}h\n`;

  if (entry.overQuota) {
    msg += `\nThis exceeds the signed revision allowance. I\'ll prepare a quote. Use "quote "${proj.name}"" to review it.`;
  }

  if (proj.cooldownUntil) {
    msg += `\n\nI\'ve noted this is the 3rd change this session. After 3 changes, I add a 24h cooldown to give us both space to think. New requests will be accepted after ${politeDate(proj.cooldownUntil)}.`;
  }

  return msg;
}

function cmdStatus(args) {
  const name = args[0];
  if (!name) {
    const projects = listProjects();
    if (projects.length === 0) return 'No projects yet. "init <name>" to start one.';
    let msg = `**Active Projects**\n\n`;
    projects
      .filter(p => p.status === 'active')
      .forEach(p => {
        const totalExtra = p.scopeChanges.reduce((s, c) => s + (c.hours || 0), 0);
        const totalTime = p.timeLog.reduce((s, t) => s + t.hours, 0);
        msg += `- **${p.name}** (${p.briefs.length} briefs, ${p.scopeChanges.length} scope changes, ${totalTime}h logged)\n`;
        if (p.signedBrief) msg += `  Signed off: ${politeDate(p.signedBrief.signedDate)}\n`;
        if (p.cooldownUntil && new Date(p.cooldownUntil) > new Date()) msg += `  Cooldown until ${politeDate(p.cooldownUntil)}\n`;
        msg += '\n';
      });
    const completed = projects.filter(p => p.status === 'completed');
    if (completed.length > 0) {
      msg += `**Completed**\n`;
      completed.forEach(p => msg += `- ${p.name}\n`);
    }
    return msg;
  }

  const proj = load(name);
  if (!proj) return `I don\'t have a project called "${name}".`;

  const totalExtra = proj.scopeChanges.reduce((s, c) => s + (c.hours || 0), 0);
  const totalTime = proj.timeLog.reduce((s, t) => s + t.hours, 0);

  let msg = `**${proj.name}** — ${proj.status}\n`;
  msg += `Created: ${politeDate(proj.created)}\n\n`;

  msg += `**Briefs:** ${proj.briefs.length}\n`;
  if (proj.signedBrief) {
    msg += `**Signed off:** ${politeDate(proj.signedBrief.signedDate)}\n`;
    msg += `**Scope:** ${proj.signedBrief.deliverables.length} deliverables, ${proj.signedBrief.revisionCount} revisions included\n`;
  } else {
    msg += `**Signed off:** Not yet\n`;
  }

  msg += `\n**Scope changes:** ${proj.scopeChanges.length} (${totalExtra}h total)\n`;
  msg += `**Time logged:** ${totalTime}h\n`;

  if (proj.scopeChanges.length > 0) {
    msg += `\n**Recent changes:**\n`;
    proj.scopeChanges.slice(-3).reverse().forEach(c => {
      msg += `- "${c.request.slice(0, 60)}" (${c.hours}h${c.overQuota ? ', over quota' : ''})\n`;
    });
  }

  if (proj.cooldownUntil && new Date(proj.cooldownUntil) > new Date()) {
    msg += `\n*Cooldown active until ${politeDate(proj.cooldownUntil)}*\n`;
  }

  if (proj.closeOut) {
    msg += `\n**Close-out:** ${proj.closeOut.summary}\n`;
  }

  return msg;
}

function cmdLogTime(args) {
  const name = args[0];
  if (!name) return 'Which project? Usage: log-time "<project>" <hours> <description>';

  const proj = load(name);
  if (!proj) return `I don\'t have a project called "${name}".`;

  const hours = parseFloat(args[1]);
  if (isNaN(hours) || hours <= 0) return 'How many hours? Usage: log-time "<project>" <hours> <description>';

  const description = args.slice(2).join(' ') || 'Work session';
  proj.timeLog.push({ hours, description, date: now() });
  proj.updated = now();
  save(proj);

  const total = proj.timeLog.reduce((s, t) => s + t.hours, 0);
  return `Logged ${hours}h for "${proj.name}". Total: ${total}h. I\'ll keep tracking.`;
}

function cmdQuote(args) {
  const name = args[0];
  if (!name) return 'Which project? Usage: quote "<project>"';

  const proj = load(name);
  if (!proj) return `I don\'t have a project called "${name}".`;

  if (proj.scopeChanges.length === 0) return `No scope changes to quote for "${proj.name}". Nothing to revise.`;

  const overQuota = proj.scopeChanges.filter(c => c.overQuota);
  const totalExtra = proj.scopeChanges.reduce((s, c) => s + (c.hours || 0), 0);
  const totalBillable = overQuota.reduce((s, c) => s + (c.hours || 0), 0);

  let msg = `**Revision Quote — ${proj.name}**\n`;
  msg += `Generated: ${politeDate(now())}\n\n`;

  if (proj.signedBrief) {
    msg += `Included revisions: ${proj.signedBrief.revisionCount}\n`;
    msg += `Changes made: ${proj.scopeChanges.length}\n`;
    msg += `Over quota: ${overQuota.length}\n\n`;
  }

  msg += `**Cumulative extra time:** ${totalExtra}h\n`;
  if (totalBillable > 0) {
    msg += `**Billable over-quota hours:** ${totalBillable}h\n`;
    msg += `**Total due:** ${CURRENCY} ${(totalBillable * HOURLY_RATE).toFixed(0)}\n`;
    msg += `**Rate:** ${CURRENCY} ${HOURLY_RATE}/h\n\n`;
  } else {
    msg += `All changes are within the signed revision allowance. No additional cost at this time.\n\n`;
  }

  msg += `I recommend we send this to the client for approval before proceeding with the revisions.`;

  return msg;
}

function cmdCloseOut(args) {
  const name = args[0];
  if (!name) return 'Which project? Usage: close-out "<project>" <summary>';

  const proj = load(name);
  if (!proj) return `I don\'t have a project called "${name}".`;
  if (proj.status === 'completed') return `"${proj.name}" is already closed.`;

  const summary = args.slice(1).join(' ') || 'Project completed.';

  const totalScopeChanges = proj.scopeChanges.length;
  const totalExtraHours = proj.scopeChanges.reduce((s, c) => s + (c.hours || 0), 0);
  const totalLoggedTime = proj.timeLog.reduce((s, t) => s + t.hours, 0);

  proj.closeOut = {
    summary,
    totalScopeChanges,
    totalExtraHours,
    totalLoggedTime,
    closedDate: now()
  };
  proj.status = 'completed';
  proj.updated = now();
  save(proj);

  let msg = `**Close-out Report — ${proj.name}**\n\n`;
  msg += `${summary}\n\n`;
  msg += `**Stats:**\n`;
  msg += `- Briefs processed: ${proj.briefs.length}\n`;
  msg += `- Scope changes: ${totalScopeChanges} (${totalExtraHours}h extra)\n`;
  msg += `- Total time logged: ${totalLoggedTime}h\n`;
  msg += `- Closed: ${politeDate(now())}\n\n`;

  msg += `I\'ve saved this to the project record. If similar work comes up, I can reuse this experience for better estimates.`;

  return msg;
}

function cmdHelp() {
  return `**Client Whisperer** — Client intake, brief management, expectation mediation.

  Commands:
    init "<name>" <desc>        Start a new project
    brief "<name>" <text|@file>  Submit a brief for analysis
    sign-off "<name>" <scope>   Generate a structured brief for client sign-off
    status [name]               Show project(s) status
    scope-change "<name>" <desc> Log a scope change request
    log-time "<name>" <h> <desc> Log hours worked
    quote "<name>"              Generate revision quote
    close-out "<name>" <text>   Close project and save summary`;
}

function extractHours(text) {
  const m = text.match(/(\d+)\s*h(?:ou)?r?s?\b/i);
  return m ? parseInt(m[1]) : null;
}

async function sendTelegram(text) {
  if (!TG_TOKEN) return;
  try {
    await fetch(`https://api.telegram.org/bot${TG_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: TG_CHAT, text, parse_mode: 'Markdown' }),
    });
  } catch {}
}

// --- Main ---
const cmd = process.argv[2];
const args = process.argv.slice(3);

const commands = {
  init: cmdInit,
  brief: cmdBrief,
  'sign-off': cmdSignOff,
  status: cmdStatus,
  'scope-change': cmdScopeChange,
  'log-time': cmdLogTime,
  quote: cmdQuote,
  'close-out': cmdCloseOut,
  help: cmdHelp,
};

async function main() {
  if (!cmd || cmd === 'help' || !commands[cmd]) {
    console.log(cmdHelp());
    return;
  }

  const output = commands[cmd](args);
  console.log(output);

  const importantCmds = ['brief', 'scope-change', 'quote', 'close-out', 'sign-off'];
  if (importantCmds.includes(cmd)) {
    await sendTelegram(`📋 Client Whisperer — ${cmd} for "${args[0] || '?'}"\n\n${output.slice(0, 500)}`);
  }
}

main().catch(err => console.error('Error:', err.message));
