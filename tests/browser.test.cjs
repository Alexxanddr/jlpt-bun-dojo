const {test} = require('node:test');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const {createServer} = require('node:http');
const {readFile} = require('node:fs/promises');
const {join} = require('node:path');

const settings = {language:'en',ui_language:'en',category:'',generation_provider:'openai',evaluation_provider:'openai',generation_model:'test',evaluation_model:'test',generation_temperature:0.2,evaluation_temperature:0.2,generation_max_tokens:2000,evaluation_max_tokens:2000,openai_base_url:'http://localhost:1234/v1',mcp_enabled:false};
const grammar = {id:'g',category:'basics',title_en:'Polite sentences',title_it:'Frasi cortesi',description_en:'End a polite sentence with です.',description_it:'Termina una frase cortese con です.'};
const exercise = {id:'first',prompt:'I am a student.',language:'en',difficulty:'standard',grammar,weaknesses:[],attribution:'Original / MIT'};
const result = {accepted:true,quality:4,ai:{scores:{grammar:95,vocabulary:90,register:90,intent:100},explanation:'The meaning is correct.',suggestions:[],corrections:[],valid_variants:['学生です。']},checks:{findings:[]},next_review:1800000000};

async function setup(t) {
  const server = createServer(async(req,res)=>{
    try {
      const path = req.url === '/' ? 'index.html' : req.url.replace(/^\/static\//,'');
      if (path.includes('..')) throw Error();
      const content = await readFile(join(__dirname,'../trainer/static',path));
      res.setHeader('Content-Type',path.endsWith('.js')?'text/javascript':path.endsWith('.css')?'text/css':path.endsWith('.json')?'application/json':'text/html');
      res.end(content);
    } catch {res.writeHead(404).end();}
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser = await chromium.launch(process.env.PLAYWRIGHT_CHANNEL ? {channel:process.env.PLAYWRIGHT_CHANNEL} : {});
  t.after(async()=>{await browser.close(); server.close();});
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror',error=>errors.push(error.message));
  t.after(()=>assert.deepEqual(errors,[]));
  await page.addInitScript(()=>localStorage.setItem('ui_language','en'));
  await page.route('**/api/**',route=>{
    const path = new URL(route.request().url()).pathname;
    const data = path.endsWith('/settings') ? {settings,providers:{},authentication_enabled:false,demo_mode:false} : path.endsWith('/grammar') ? [grammar] : path.endsWith('/exercises') ? exercise : path.endsWith('/answers') ? result : path.endsWith('/hint') ? {references:['学生です。']} : [];
    return route.fulfill({json:data});
  });
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  await page.locator('#practice').waitFor({state:'visible'});
  return page;
}

test('evaluation locks the exercise and hint until it completes',async t=>{
  const page = await setup(t);
  await page.locator('#exercise-form button').click();
  await page.locator('#answer').fill('学生です。');
  let release;
  const gate = new Promise(resolve=>release=resolve);
  await page.route('**/api/answers',async route=>{await gate; await route.fulfill({json:result});});
  await page.locator('#grade').click();
  try {
    assert.equal(await page.locator('#exercise-form button').isDisabled(),true);
    assert.equal(await page.locator('#hint').isDisabled(),true);
    assert.equal(await page.locator('#answer').isEditable(),false);
  } finally {release();}
  await page.locator('#feedback').waitFor({state:'visible'});
  assert.equal(await page.locator('#grade').isDisabled(),true);
  assert.equal(await page.locator('#answer').isEditable(),false);
});

test('provider proxy error is readable, preserves draft, and allows retry',async t=>{
  const page = await setup(t);
  await page.locator('#exercise-form button').click();
  await page.locator('#answer').fill('学生です。');
  await page.route('**/api/answers',route=>route.fulfill({status:502,contentType:'text/html',body:'<h1>Bad gateway</h1>'}));
  await page.locator('#grade').click();
  await page.waitForFunction(()=>!document.getElementById('grade').disabled);
  assert.match(await page.locator('#notice').textContent(),/server|connection|provider/i);
  assert.equal(await page.locator('#answer').inputValue(),'学生です。');
  await page.unroute('**/api/answers');
  await page.locator('#grade').click();
  await page.locator('#feedback').waitFor({state:'visible'});
});

test('mode transitions restore AI preference, preserve draft and explain locked controls',async t=>{
  const page = await setup(t);
  await page.locator('#generate').check();
  await page.locator('#exercise-form button').click();
  await page.locator('#answer').fill('私の文');
  for (const mode of ['targeted','review','cram','new','targeted','new']) {
    await page.locator('#mode').selectOption(mode);
    assert.equal(await page.locator('#generate').isDisabled(),mode !== 'new');
    assert.equal(await page.locator('#generate').isChecked(),['new','targeted'].includes(mode));
    assert.equal(await page.locator('#difficulty').isDisabled(),['review','cram'].includes(mode));
    assert.equal(await page.locator('#answer').inputValue(),'私の文');
    assert.ok((await page.locator('#mode-help').textContent()).length > 10);
  }
});

test('save and sync uses edited settings, clears keys and supports a partial source failure',async t=>{
  const page = await setup(t);
  await page.locator('[data-view=settings]').click();
  let saved;
  await page.route('**/api/settings',route=>{
    if (route.request().method() === 'PUT') {
      saved=route.request().postDataJSON();
      return route.fulfill({json:{ok:true}});
    }
    return route.fulfill({json:{settings:{...settings,...saved,openai_api_key:undefined},providers:{openai_key_configured:true},authentication_enabled:false,demo_mode:false}});
  });
  await page.route('**/api/mcp/sync',route=>{
    assert.equal(saved.mcp_enabled,true);
    return route.fulfill({json:{items:[{source:'wanikani',evidence:{characters:'本',slug:'本',subject_type:'kanji'}}],unavailable:['bunpro']}});
  });
  await page.locator('[name=mcp_enabled]').check();
  await page.locator('[name=openai_api_key]').fill('test-key');
  await page.locator('#sync').click();
  await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Some sources'));
  assert.equal(await page.locator('[name=openai_api_key]').inputValue(),'');
  assert.match(await page.locator('#sync-status').textContent(),/1.*bunpro/);
  assert.match(await page.locator('#sync-items').textContent(),/本/);
});

test('history, journal, progress and translated feedback render without errors',async t=>{
  const page = await setup(t);
  await page.route('**/api/history',route=>route.fulfill({json:[{prompt:exercise.prompt,answer:'学生です。',created_at:1800000000,result:JSON.stringify(result)}]}));
  await page.route('**/api/journal',route=>route.fulfill({json:[{grammar_id:'g',title_en:'Polite sentences',title_it:'Frasi cortesi',resolved:0,observations:JSON.stringify({...result,weaknesses:[]})}]}));
  await page.route('**/api/journal/g/resolve',route=>route.fulfill({json:{ok:true}}));
  await page.route('**/api/stats',route=>route.fulfill({json:{attempts:1,due:0,axes:{grammar:95,vocabulary:90,register:90,coverage:4,independence:100,recall:0},grammar:{g:{attempts:1,accepted:1}},sources:[],weaknesses:{items:[]}}}));
  await page.locator('#exercise-form button').click();
  await page.locator('#answer').fill('学生です。');
  await page.locator('#grade').click();
  await page.locator('#feedback').waitFor({state:'visible'});
  await page.setViewportSize({width:1440,height:900});
  await page.locator('[data-view=stats]').click();
  await page.locator('#stats-axes strong').first().waitFor();
  await page.screenshot({path:'test-results/progress.jpg',quality:85,fullPage:true});
  await page.locator('[data-view=practice]').click();
  await page.locator('#ui-language').selectOption('it');
  await page.waitForFunction(()=>document.getElementById('verdict').textContent.includes('Significato'));
  for (const view of ['history','journal','stats','practice']) {
    await page.locator(`[data-view=${view}]`).click();
    await page.locator(`#${view}`).waitFor({state:'visible'});
  }
  assert.equal(await page.locator('#grade').isDisabled(),true);
  assert.equal(await page.locator('#answer').inputValue(),'学生です。');
});

test('desktop and phone layouts stay within viewport and capture reviewable screens',async t=>{
  const page = await setup(t);
  await page.setViewportSize({width:1440,height:1000});
  await page.screenshot({path:'test-results/practice-empty.png',fullPage:true});
  await page.locator('#exercise-form button').click();
  await page.locator('#answer').fill('学生です。');
  await page.screenshot({path:'test-results/practice-desktop.png',fullPage:true});
  await page.screenshot({path:'test-results/practice.jpg',quality:85,fullPage:true});
  await page.setViewportSize({width:768,height:1024});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth),true);
  await page.screenshot({path:'test-results/practice-tablet.png',fullPage:true});
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('#grade').click();
  await page.locator('#feedback').waitFor({state:'visible'});
  await page.screenshot({path:'test-results/feedback-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.waitForFunction(()=>!document.getElementById('session-options').open);
  assert.ok((await page.locator('#prompt').boundingBox()).y < 500);
  await page.locator('#session-options summary').click();
  await page.locator('#mode').selectOption('targeted');
  assert.equal(await page.locator('#generate').isDisabled(),true);
  await page.locator('#session-options summary').click();
  await page.locator('#ui-language').selectOption('it');
  await page.waitForFunction(()=>document.documentElement.lang === 'it');
  for (const button of await page.locator('#nav button').all()) {
    const box = await button.boundingBox();
    assert.ok(box.x >= 12 && box.x + box.width <= 378);
  }
  await page.locator('#ui-language').selectOption('en');
  for (const view of ['practice','settings']) {
    await page.locator(`[data-view=${view}]`).click();
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth <= window.innerWidth),true);
    await page.screenshot({path:`test-results/${view}-mobile.png`,fullPage:true});
  }
});

test('failed generation preserves the current exercise and its answer',async t=>{
  const page = await setup(t);
  await page.locator('#exercise-form button').click();
  await page.locator('#answer').fill('学生です。');
  await page.route('**/api/exercises',route=>route.fulfill({status:502,json:{detail:'provider_incomplete'}}));
  await page.locator('#generate').check();
  await page.locator('#exercise-form button').click();
  await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('output limit'));
  assert.equal(await page.locator('#answer').inputValue(),'学生です。');
  assert.equal(await page.locator('#prompt').textContent(),exercise.prompt);
  assert.equal(await page.locator('#generate').isEnabled(),true);
  assert.equal(await page.locator('#difficulty').isEnabled(),true);
});

test('expired session requires login and logout clears the previous exercise',async t=>{
  const page = await setup(t);
  await page.locator('#exercise-form button').click();
  await page.locator('#answer').fill('学生です。');
  let loggedIn=false;
  await page.route('**/api/settings',route=>route.fulfill({json:{settings,providers:{},authentication_enabled:true,demo_mode:false}}));
  await page.route('**/api/history',route=>route.fulfill(loggedIn ? {json:[]} : {status:401,json:{detail:'authentication_required'}}));
  await page.route('**/api/login',route=>{loggedIn=true; return route.fulfill({json:{ok:true}});});
  await page.locator('[data-view=history]').click();
  await page.locator('#login').waitFor({state:'visible'});
  assert.equal(await page.locator('#nav').isVisible(),false);
  await page.locator('#password').fill('test-password-long-enough');
  await page.locator('#login-form button').click();
  await page.locator('#practice').waitFor({state:'visible'});
  assert.equal(await page.locator('#answer').inputValue(),'学生です。');
  await page.locator('[data-view=settings]').click();
  await page.locator('#logout').click();
  await page.locator('#login').waitFor({state:'visible'});
  assert.equal(await page.locator('#answer').inputValue(),'');
});

 test('incorrect password displays the credentials error and can be retried',async t=>{
  const page = await setup(t);
  await page.route('**/api/history',route=>route.fulfill({status:401,json:{detail:'authentication_required'}}));
  await page.route('**/api/login',route=>route.fulfill({status:401,json:{detail:'invalid_credentials'}}));
  await page.locator('[data-view=history]').click();
  await page.locator('#password').fill('incorrect-password-long');
  await page.locator('#login-form button').click();
  await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Invalid password'));
  assert.equal(await page.locator('#login-form button').isEnabled(),true);
});
