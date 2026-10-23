import {exerciseOptions} from './exercise-options.js';

const $ = (id) => document.getElementById(id);
let preferredUi = localStorage.getItem('ui_language');
if (!['it', 'en'].includes(preferredUi)) preferredUi = null;
let ui = preferredUi || 'it';
if (!['it', 'en'].includes(ui)) ui = 'it';
let messages = {}, grammar = [], config, current, hinted = false, view = 'practice';
let newGeneration = false, pending = false, lastResult = null;
const t = (key) => messages[key] || key;
const text = (tag, value, cls) => { const e = document.createElement(tag); e.textContent = value; if (cls) e.className = cls; return e; };
const date = (v) => new Date(v * 1000).toLocaleString(ui);
function notice(key, kind = 'info') {
  $('notice').textContent = t(key);
  $('notice').dataset.kind = kind;
}
async function api(path, body, method = 'POST') {
  let response;
  try {
    response = await fetch('/api/' + path, {method: body === undefined ? 'GET' : method,
      headers: {'Content-Type':'application/json', 'X-Trainer-Request':'1'},
      body: body === undefined ? undefined : JSON.stringify(body)});
  } catch { throw new Error('connection_failed'); }
  if (response.status === 401) {
    showLogin();
    throw new Error(path === 'login' ? 'invalid_credentials' : 'authentication_required');
  }
  let data;
  try { data = await response.json(); } catch { throw new Error('server_unavailable'); }
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'invalid_input');
  return data;
}
async function busy(button, fn) {
  if (pending) return false;
  pending = true;
  const controls = [...document.querySelectorAll('button, input, select, textarea')];
  const disabled = controls.map(control => control.disabled);
  controls.forEach(control => { control.disabled = true; });
  document.querySelector('main').setAttribute('aria-busy', 'true');
  notice('working');
  try {
    const message = await fn();
    notice(message || '', 'success');
    return true;
  } catch (error) {
    notice(messages[error.message] ? error.message : 'server_unavailable', 'error');
    return false;
  } finally {
    pending = false;
    controls.forEach((control, index) => { control.disabled = disabled[index]; });
    document.querySelector('main').setAttribute('aria-busy', 'false');
    syncExerciseOptions();
  }
}
function syncExerciseOptions() {
  if (pending) return;
  const state = exerciseOptions($('mode').value, newGeneration);
  $('generate').checked = state.generate;
  $('generate').disabled = state.generateDisabled;
  $('difficulty').disabled = state.difficultyDisabled;
  $('grade').disabled = !current || !!lastResult;
  $('answer').readOnly = !!lastResult;
  $('hint').disabled = !current || hinted || !!lastResult;
  $('mode-help').textContent = t('modeHelp_' + $('mode').value);
}
async function translate(lang) {
  ui = lang; messages = await (await fetch(`/static/locales/${ui}.json`)).json();
  document.documentElement.lang = ui; localStorage.setItem('ui_language', ui); $('ui-language').value = ui;
  document.querySelectorAll('[data-i18n]').forEach(e => { e.textContent = t(e.dataset.i18n); });
  categories();
  if (current) displayExercise();
  if (lastResult) renderResult(lastResult);
}
function categories() {
  for (const id of ['category','settings-category']) {
    const select = $(id), old = select.value;
    select.replaceChildren(new Option(t('allCategories'), ''));
    [...new Set(grammar.map(g => g.category))].forEach(c => select.add(new Option(t(c), c)));
    select.value = [...select.options].some(option => option.value === old) ? old : '';
  }
}
function showLogin() {
  $('nav').hidden = true;
  for (const id of ['practice','history','journal','stats','settings']) $(id).hidden = true;
  $('login').hidden = false;
}
async function bootstrap(next = 'practice') {
  const data = await api('settings'); config = data.settings;
  grammar = await api('grammar'); categories();
  await translate(preferredUi || config.ui_language);
  $('settings-form').reset();
  $('source-language').value = config.language; $('category').value = config.category;
  for (const [key, value] of Object.entries(config)) {
    const el = $('settings-form').elements.namedItem(key);
    if (el) { if (el.type === 'checkbox') el.checked = value; else el.value = value; }
  }
  $('settings-form').elements.ui_language.value = ui;
  $('provider-status').replaceChildren();
  for (const [key, value] of Object.entries(data.providers)) {
    $('provider-status').append(text('dt', t(key)), text('dd', typeof value === 'boolean' ? t(value ? 'configured' : 'notConfigured') : value));
  }
  document.querySelectorAll('[data-view]').forEach(e => { e.hidden = data.demo_mode && e.dataset.view !== 'practice'; });
  $('logout').hidden = !data.authentication_enabled;
  $('login').hidden = true; $('nav').hidden = false; await showView(next);
  syncExerciseOptions();
}
async function showView(next) {
  view = next;
  for (const id of ['practice','history','journal','stats','settings']) $(id).hidden = id !== next;
  document.querySelectorAll('[data-view]').forEach(e => e.setAttribute('aria-current', e.dataset.view === next ? 'page' : 'false'));
  if (next === 'history') await history();
  if (next === 'journal') await journal();
  if (next === 'stats') await stats();
}
function displayExercise() {
  $('exercise').hidden = false; $('exercise-empty').hidden = true;
  $('prompt').textContent = current.prompt; $('prompt').lang = current.language;
  $('grammar-label').textContent = current.grammar[`title_${ui}`];
  $('difficulty-label').textContent = current.attribution.startsWith('AI-generated') ? t(current.difficulty) : t('reviewedSentence');
  $('grammar-description').textContent = current.grammar[`description_${ui}`];
  let attribution = current.attribution;
  try {
    const a = JSON.parse(attribution);
    attribution = `${a.source} #${a.ja_id} (${a.ja_author}); ${Object.entries(a.translations).map(([lang,v]) => `${lang} #${v.id} (${v.author})`).join('; ')}; ${a.license}`;
  } catch { /* Original and AI-generated attribution is plain text. */ }
  $('attribution').textContent = attribution;
  renderWeaknesses($('weaknesses'), current.weaknesses);
}
function renderWeaknesses(target, values) {
  target.replaceChildren();
  if (!values.length) return;
  const details = text('details',''); details.append(text('summary',t('weaknesses')));
  for (const w of values) {
    const evidence = w.evidence || w;
    const meanings = Array.isArray(evidence.meanings) && evidence.meanings.length ? ` — ${evidence.meanings.join(', ')}` : '';
    const accuracy = typeof evidence.accuracy === 'number' ? ` · ${Math.round(evidence.accuracy)}%` : '';
    const target = evidence.target || evidence.characters || evidence.slug || evidence.grammar_point || evidence.title;
    if (typeof target !== 'string') continue;
    const row = text('p', `${w.source}: ${target}${meanings}${accuracy}`);
    const slug = evidence.slug || evidence.target;
    if (w.source === 'wanikani' && typeof slug === 'string' && slug.length <= 200) {
      const link = text('a', t('openStudyPoint'));
      const kind = evidence.subject_type || evidence.kind;
      const type = ['kanji','vocabulary','radical'].includes(kind) ? kind : 'vocabulary';
      link.href = 'https://www.wanikani.com/' + type + '/' + encodeURIComponent(slug);
      link.rel = 'noreferrer'; link.target = '_blank'; row.append(' ',link);
    }
    details.append(row);
  }
  target.append(details);
}
function renderResult(result) {
  lastResult = result;
  $('feedback').hidden = false;
  $('feedback').dataset.accepted = String(result.accepted);
  $('verdict').textContent = t(result.accepted ? 'accepted' : 'tryAgain');
  $('scores').replaceChildren();
  for (const [axis, score] of Object.entries(result.ai.scores)) {
    const item = text('div','', 'score'), meter = document.createElement('progress');
    meter.max = 100; meter.value = score; meter.setAttribute('aria-label',t(axis));
    item.append(text('span',t(axis)),text('strong',`${score}/100`),meter); $('scores').append(item);
  }
  $('findings').replaceChildren();
  if (!result.checks.findings.length) $('findings').append(text('li',t('noCertainErrors')));
  for (const f of result.checks.findings) $('findings').append(text('li',`${t(f.code)}: ${f.value}`));
  $('explanation').textContent = result.ai.explanation;
  $('suggestions').replaceChildren(...result.ai.suggestions.map(v => text('li',v)));
  $('corrections').replaceChildren(...result.ai.corrections.map(v => text('p',v)));
  $('corrections-section').hidden = !result.ai.corrections.length;
  $('variants').replaceChildren(...result.ai.valid_variants.map(v => text('p',v)));
  $('variants-section').hidden = !result.ai.valid_variants.length;
  $('next-review').textContent = result.next_review ? `${t('nextReview')}: ${date(result.next_review)}` : t('cramNoSchedule');
}
async function history() {
  const rows = await api('history'); $('history-list').replaceChildren();
  if (!rows.length) $('history-list').append(text('p',t('noHistory')));
  for (const row of rows) {
    const item = text('article','', 'entry');
    item.append(text('h2',row.prompt),text('p',row.answer,'japanese'),text('p',date(row.created_at)));
    const result = JSON.parse(row.result), details = text('details','');
    details.append(text('summary',t(result.accepted ? 'accepted' : 'tryAgain')),text('p',result.ai.explanation));
    result.ai.suggestions.forEach(s => details.append(text('p',s)));
    item.append(details); $('history-list').append(item);
  }
}
async function journal() {
  const rows = await api('journal'); $('journal-list').replaceChildren();
  if (!rows.length) $('journal-list').append(text('p',t('noJournal')));
  for (const row of rows) {
    const item = text('article','', 'entry'), result = JSON.parse(row.observations);
    item.append(text('h2',row[`title_${ui}`]),text('p',result.ai.explanation));
    result.ai.suggestions.forEach(s => item.append(text('p',s)));
    result.checks.findings.forEach(f => item.append(text('p',`${t(f.code)}: ${f.value}`)));
    renderWeaknesses(item.appendChild(document.createElement('div')), result.weaknesses);
    const button = text('button',t(row.resolved ? 'resolved' : 'resolve')); button.disabled = !!row.resolved;
    button.onclick = () => busy(button,async()=>{ await api(`journal/${encodeURIComponent(row.grammar_id)}/resolve`,{}); await journal(); });
    item.append(button); $('journal-list').append(item);
  }
}
function radar(axes) {
  const ns = 'http://www.w3.org/2000/svg', svg = document.createElementNS(ns,'svg');
  svg.setAttribute('viewBox','0 0 360 340'); svg.setAttribute('role','img'); svg.setAttribute('aria-label',t('stats'));
  const keys = Object.keys(axes), pt = (i,r) => [180+Math.sin(i*Math.PI/3)*r,165-Math.cos(i*Math.PI/3)*r];
  for (const r of [30,60,90,120]) {
    const p = document.createElementNS(ns,'polygon'); p.setAttribute('points',keys.map((_,i)=>pt(i,r).join(',')).join(' '));
    p.setAttribute('fill','none'); p.setAttribute('stroke','#c9d6e8'); svg.append(p);
  }
  const p = document.createElementNS(ns,'polygon'); p.setAttribute('points',keys.map((k,i)=>pt(i,axes[k]*1.2).join(',')).join(' '));
  p.setAttribute('fill','#14665f22'); p.setAttribute('stroke','#14665f'); p.setAttribute('stroke-width','2'); svg.append(p);
  keys.forEach((key,i)=>{ const label = document.createElementNS(ns,'text'), [x,y]=pt(i,148); label.setAttribute('x',x); label.setAttribute('y',y); label.setAttribute('text-anchor','middle'); label.setAttribute('font-size','12'); label.setAttribute('fill','#182d50'); label.textContent=t(key); svg.append(label); });
  $('radar').replaceChildren(svg);
}
async function stats() {
  const data = await api('stats');
  $('stats-summary').textContent = `${t('attempts')}: ${data.attempts} · ${t('due')}: ${data.due}`;
  radar(data.axes); $('stats-axes').replaceChildren();
  for (const [key,value] of Object.entries(data.axes)) { const r=text('div',''); r.append(text('span',t(key)),text('strong',`${Math.round(value)}%`)); $('stats-axes').append(r); }
  $('grammar-stats').replaceChildren();
  for (const [id,g] of Object.entries(data.grammar)) {
    const title=grammar.find(x=>x.id===id)?.[`title_${ui}`] || id;
    $('grammar-stats').append(text('p',`${title}: ${g.accepted}/${g.attempts}`));
  }
  $('sources').replaceChildren(text('p',t('starterData')));
  data.sources.forEach(s => {const m=JSON.parse(s.data); $('sources').append(text('p',`${s.name}: ${m.entries} ${t('entries')}; ${m.license}; ${date(s.imported_at)}`));});
  renderWeaknesses($('stats-weaknesses'),data.weaknesses.items);
  if (!data.weaknesses.items.length) $('stats-weaknesses').append(text('p',t('noWeaknesses')));
}
$('ui-language').onchange = e => {
  const language = e.target.value;
  preferredUi = language;
  busy(e.target, async () => {
    await translate(language);
    if (config) { $('settings-form').elements.ui_language.value = language; await showView(view); }
  });
};
$('login-form').onsubmit = e => {e.preventDefault(); busy(e.submitter,async()=>{
  await api('login',{password:$('password').value}); $('password').value=''; await bootstrap();
});};
document.querySelectorAll('[data-view]').forEach(e=> e.onclick=()=>busy(e,()=>showView(e.dataset.view)));
$('exercise-form').onsubmit = e => {e.preventDefault();
  const request={language:$('source-language').value,category:$('category').value,mode:$('mode').value,generate:$('generate').checked,difficulty:$('difficulty').value};
  busy(e.submitter,async()=>{
    const exercise = await api('exercises',request);
    current=exercise; lastResult=null; hinted=false;
    $('answer').value=''; $('hint-text').textContent=''; $('char-count').textContent='0 / 500';
    $('feedback').hidden=true; displayExercise();
  }).then(ok=>{if(ok) $('answer').focus();});
};
$('answer').oninput=()=>{$('char-count').textContent=`${$('answer').value.length} / 500`;};
$('answer-form').onsubmit=e=>{e.preventDefault();
  if (!current || lastResult || !$('answer').value.trim()) return;
  const request={exercise_id:current.id,answer:$('answer').value,hinted};
  busy(e.submitter,async()=>{renderResult(await api('answers',request));});
};
$('hint').onclick=()=>busy($('hint'),async()=>{
  const r=await api(`exercises/${current.id}/hint`); hinted=true; $('hint-text').textContent=r.references.join(' / ');
});
function settingsData() {
  const form = $('settings-form'), data = Object.fromEntries(new FormData(form));
  data.mcp_enabled = form.elements.mcp_enabled.checked;
  return data;
}
async function saveSettings(data) {
  await api('settings',data,'PUT');
  preferredUi = data.ui_language;
  await bootstrap('settings');
}
$('settings-form').onsubmit=e=>{e.preventDefault();
  const data=settingsData();
  busy(e.submitter,async()=>{await saveSettings(data); return 'settingsSaved';});
};
$('sync').onclick=()=>{
  if (!$('settings-form').reportValidity()) return;
  const data=settingsData();
  busy($('sync'),async()=>{
    await saveSettings(data);
    const r=await api('mcp/sync',{});
    $('sync-status').textContent = `${t('syncedItems')}: ${r.items.length}` +
      (r.unavailable.length ? ` — ${t('unavailableSources')}: ${r.unavailable.join(', ')}` : '');
    renderWeaknesses($('sync-items'), r.items);
    if (!r.items.length) throw new Error(r.unavailable.length ? 'mcp_unavailable' : 'noWeaknesses');
    return r.unavailable.length ? 'syncPartial' : 'syncComplete';
  });
};
$('logout').onclick=()=>busy($('logout'),async()=>{
  await api('logout',{}); config=null; current=null; lastResult=null; hinted=false;
  $('answer').value=''; $('feedback').hidden=true; $('exercise').hidden=true; $('exercise-empty').hidden=false;
  $('settings-form').reset(); $('sync-items').replaceChildren(); $('sync-status').textContent=''; showLogin();
});
$('generate').onchange=()=>{newGeneration=$('generate').checked; syncExerciseOptions();};
$('mode').onchange=syncExerciseOptions;
const compactLayout = matchMedia('(max-width: 850px)');
const foldOptions = () => { $('session-options').open = !compactLayout.matches; };
compactLayout.addEventListener('change', foldOptions);
foldOptions();
const themePreference = matchMedia('(prefers-color-scheme: dark)');
function applyTheme() {
  const theme = $('theme').value;
  document.documentElement.dataset.theme = theme === 'system' ? (themePreference.matches ? 'dark' : 'light') : theme;
}
$('theme').value = ['light', 'dark'].includes(localStorage.getItem('theme')) ? localStorage.getItem('theme') : 'system';
$('theme').onchange = () => { localStorage.setItem('theme', $('theme').value); applyTheme(); };
themePreference.addEventListener('change', applyTheme);
applyTheme();
await translate(ui);
syncExerciseOptions();
await busy(null, bootstrap);
