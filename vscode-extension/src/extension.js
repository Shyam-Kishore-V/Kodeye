'use strict';
const vscode = require('vscode');
const http = require('http');
const https = require('https');

let panel = null;
let diagCol = null;
let statusBar = null;

// ── HTTP POST ─────────────────────────────────────────────────
function post(urlStr, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    let parsed;
    try { parsed = new URL(urlStr); } catch(e) { reject(new Error('Invalid URL: ' + urlStr)); return; }
    const lib = parsed.protocol === 'https:' ? https : http;
    const req = lib.request({
      hostname: parsed.hostname,
      port: parsed.port,
      path: parsed.pathname + (parsed.search||''),
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }
    }, res => {
      let body = '';
      res.on('data', c => body += c);
      res.on('end', () => { try { resolve(JSON.parse(body)); } catch(e) { reject(new Error('Bad response')); } });
    });
    req.on('error', e => reject(new Error('Cannot reach backend: ' + e.message)));
    req.setTimeout(60000, () => { req.destroy(); reject(new Error('Timeout — is uvicorn running?')); });
    req.write(data);
    req.end();
  });
}

// ── Config ────────────────────────────────────────────────────
function cfg() {
  const c = vscode.workspace.getConfiguration('kodeye');
  return {
    url:      c.get('backendUrl', 'http://localhost:8000'),
    provider: c.get('provider',   'groq'),
    model:    c.get('model',      'llama-3.3-70b-versatile')
  };
}

// ── Get code and lang ─────────────────────────────────────────
function getEditor() {
  const ed = vscode.window.activeTextEditor;
  if (!ed) { vscode.window.showWarningMessage('Kodeye: Open a file first.'); return null; }
  return ed;
}
function getCode(ed) {
  const sel = ed.selection;
  return sel.isEmpty ? ed.document.getText() : ed.document.getText(sel);
}
function getLang(ed) {
  const id = ed.document.languageId;
  return id === 'javascript' || id === 'typescript' ? 'javascript' : id;
}
function getFileName(ed) {
  return ed.document.fileName.split(/[/\\]/).pop();
}

// ── Markdown → HTML ───────────────────────────────────────────
function mdHtml(raw) {
  if (!raw) return '';
  return raw
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/```[\w]*\n([\s\S]*?)```/g,'<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/g,'<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/^### (.+)$/gm,'<h3>$1</h3>')
    .replace(/^## (.+)$/gm,'<h2>$1</h2>')
    .replace(/^# (.+)$/gm,'<h2>$1</h2>')
    .replace(/^\- (.+)$/gm,'<li>$1</li>')
    .replace(/^\d+\. (.+)$/gm,'<li>$1</li>')
    .replace(/(<li>[\s\S]*?<\/li>\n?)+/g, m => `<ul>${m}</ul>`)
    .replace(/^([^<\n].+)$/gm,'<p>$1</p>');
}

function esc(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

// ── Show webview ──────────────────────────────────────────────
function showPanel(title, html) {
  if (!panel) {
    panel = vscode.window.createWebviewPanel('kodeye', title,
      { viewColumn: vscode.ViewColumn.Beside, preserveFocus: true },
      { enableScripts: true, retainContextWhenHidden: true }
    );
    panel.onDidDispose(() => { panel = null; });
  } else {
    panel.title = title;
    panel.reveal(vscode.ViewColumn.Beside, true);
  }
  panel.webview.html = `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<style>
  body{margin:0;padding:20px;font-family:'Segoe UI',system-ui,sans-serif;font-size:13px;
    background:var(--vscode-editor-background);color:var(--vscode-editor-foreground);line-height:1.7}
  h1{font-size:17px;color:#00d4ff;margin:0 0 16px;padding-bottom:8px;border-bottom:2px solid #00d4ff}
  h2{font-size:14px;color:#00d4ff;margin:18px 0 8px;padding-bottom:4px;border-bottom:1px solid #1e3050}
  h3{font-size:13px;margin:10px 0 4px;color:#c8d8ea}
  p{margin:6px 0}ul,ol{margin:6px 0 6px 20px}li{margin:3px 0}
  strong{color:#e2eaf5}em{opacity:.8}
  code{background:rgba(255,255,255,.08);padding:1px 5px;border-radius:4px;font-family:'Fira Code',monospace;font-size:12px;color:#00d4ff}
  pre{background:rgba(255,255,255,.05);border:1px solid #1e3050;border-radius:6px;padding:12px;overflow-x:auto;margin:10px 0}
  pre code{background:none;padding:0;color:#abb2bf}
  .issue{padding:9px 12px;margin:5px 0;border-radius:6px;border:1px solid #1e3050;border-left:3px solid #00d4ff;background:rgba(255,255,255,.03)}
  .issue.error{border-left-color:#ef4444}.issue.warning{border-left-color:#f59e0b}
  .msg{font-size:12px;color:#c8d8ea}.meta{font-size:11px;opacity:.5;font-family:monospace;margin-top:2px}
  .sev{font-size:10px;padding:1px 6px;border-radius:3px;font-weight:600;text-transform:uppercase;float:right}
  .sev.error{background:rgba(239,68,68,.2);color:#ef4444}.sev.warning{background:rgba(245,158,11,.2);color:#f59e0b}.sev.info{background:rgba(0,212,255,.1);color:#00d4ff}
  .score{display:flex;align-items:center;gap:16px;background:rgba(0,212,255,.06);border:1px solid rgba(0,212,255,.2);border-radius:10px;padding:18px;margin:12px 0}
  .snum{font-size:36px;font-weight:800;color:#00d4ff}.sgrade{font-size:22px;font-weight:700}
  .sinfo{font-size:12px;opacity:.6;margin-top:4px}
  .bd{display:inline-flex;gap:16px;margin-top:8px;font-size:12px}
  .metrics{display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:8px;margin:12px 0}
  .mc{background:rgba(255,255,255,.04);border:1px solid #1e3050;border-radius:6px;padding:10px;text-align:center}
  .mv{font-size:20px;font-weight:700;color:#00d4ff}.ml{font-size:10px;opacity:.6;text-transform:uppercase;margin-top:2px}
  .ok{color:#39d98a;text-align:center;padding:20px;font-size:13px}
  .btn{background:transparent;border:1px solid #1e3050;color:#5a7290;padding:3px 10px;border-radius:4px;font-size:11px;cursor:pointer;margin-left:auto;display:block}
  .btn:hover{color:#00d4ff;border-color:#00d4ff}
</style></head><body>
<h1>&#x1F441;&#xFE0F; Kodeye &mdash; ${esc(title)} <button class="btn" onclick="navigator.clipboard.writeText(document.body.innerText)">Copy</button></h1>
${html}
</body></html>`;
}

// ── Push diagnostics ──────────────────────────────────────────
function pushDiags(ed, issues) {
  const diags = (issues||[]).map(i => {
    const line = Math.min(Math.max(0,(i.line||1)-1), ed.document.lineCount-1);
    const range = ed.document.lineAt(line).range;
    const sev = i.severity==='error' ? vscode.DiagnosticSeverity.Error
              : i.severity==='warning' ? vscode.DiagnosticSeverity.Warning
              : vscode.DiagnosticSeverity.Information;
    const d = new vscode.Diagnostic(range, '[Kodeye] '+i.message, sev);
    d.source = 'Kodeye'; return d;
  });
  diagCol.set(ed.document.uri, diags);
}

// ── Main: Analyze ─────────────────────────────────────────────
async function analyze(mode) {
  const ed = getEditor(); if (!ed) return;
  const code = getCode(ed);
  if (!code.trim()) { vscode.window.showWarningMessage('Kodeye: No code to analyse.'); return; }

  const lang = getLang(ed);
  const fname = getFileName(ed);
  const { url, provider, model } = cfg();

  if (mode === 'docs') {
    const pick = await vscode.window.showQuickPick(
      [{label:'Docstrings',value:'docstring'},{label:'README.md',value:'readme'},{label:'API Docs',value:'api'}],
      { title: 'Kodeye: What to generate?' }
    );
    if (!pick) return;
    statusBar.text = '$(sync~spin) Kodeye';
    try {
      const r = await post(url+'/api/docs?doc_type='+pick.value, {code,language:lang,provider,model});
      showPanel('Docs — '+fname, '<h2>'+pick.label+'</h2>'+mdHtml(r.documentation));
    } catch(e) { vscode.window.showErrorMessage('Kodeye: '+e.message); }
    finally { statusBar.text = '$(eye) Kodeye'; }
    return;
  }

  statusBar.text = '$(sync~spin) Kodeye';
  await vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: 'Kodeye: Analysing '+fname, cancellable: false },
    async () => {
      try {
        // 1. Static analysis
        const sr = await post(url+'/api/static', {code, language:lang});
        const issues = sr.issues||[];
        const metrics = sr.metrics||{};

        // Metrics HTML
        const mEntries = Object.entries(metrics).filter(([,v])=>typeof v==='number'||typeof v==='string');
        const mHtml = mEntries.length ? '<div class="metrics">'+mEntries.map(([k,v])=>{
          const val = (typeof v==='number'&&!Number.isInteger(v))?v.toFixed(1):v;
          return `<div class="mc"><div class="mv">${val}</div><div class="ml">${k.replace(/_/g,' ')}</div></div>`;
        }).join('')+'</div>' : '';

        // Issues HTML
        const iHtml = !issues.length
          ? '<div class="ok">&#x2705; No static issues found!</div>'
          : issues.map(i=>`<div class="issue ${i.severity}"><span class="sev ${i.severity}">${i.severity}</span><div class="msg">${esc(i.message)}</div><div class="meta">Line ${i.line||'-'} &middot; ${esc(i.tool||'')}</div></div>`).join('');

        // Show static results immediately
        showPanel('Analysis — '+fname,
          '<h2>&#x1F4CA; Static Analysis</h2>'+mHtml+iHtml+
          '<h2>&#x1F916; LLM + Ensemble</h2><p style="opacity:.4">Loading from backend...</p>'
        );
        pushDiags(ed, issues);

        // 2. Ensemble (LLM + scoring)
        const er = await post(url+'/api/ensemble', {code,language:lang,provider,model});
        const gc = {A:'#39d98a',B:'#00d4ff',C:'#f59e0b',D:'#ff6b35',F:'#ef4444'};
        const col = gc[er.grade]||'#00d4ff';
        const bd = er.breakdown||{};

        const ensHtml =
          `<div class="score">
            <div class="snum" style="color:${col}">${er.ensemble_score}<span style="font-size:14px;opacity:.5">/100</span></div>
            <div>
              <div class="sgrade" style="color:${col}">Grade ${er.grade} &mdash; ${er.label}</div>
              <div class="sinfo">60% static &middot; 40% LLM</div>
              <div class="bd">
                <span>Security <strong style="color:#ef4444">${bd.security||0}</strong></span>
                <span>Style <strong style="color:#f59e0b">${bd.style||0}</strong></span>
                <span>Logic <strong style="color:#00d4ff">${bd.logic||0}</strong></span>
                <span>Total <strong style="color:#39d98a">${bd.total||0}</strong></span>
              </div>
            </div>
          </div>
          ${er.llm_summary?'<h2>LLM Review</h2>'+mdHtml(er.llm_summary):''}`;

        showPanel('Analysis — '+fname,
          '<h2>&#x1F4CA; Static Analysis</h2>'+mHtml+iHtml+
          '<h2>&#x1F916; Ensemble Score</h2>'+ensHtml
        );

        vscode.window.showInformationMessage(`Kodeye: Grade ${er.grade} (${er.ensemble_score}/100) — ${er.label}`);

      } catch(e) {
        vscode.window.showErrorMessage('Kodeye: '+e.message);
      } finally {
        statusBar.text = '$(eye) Kodeye';
      }
    }
  );
}

// ── Activate ──────────────────────────────────────────────────
function activate(context) {
  // Diagnostic collection
  diagCol = vscode.languages.createDiagnosticCollection('kodeye');
  context.subscriptions.push(diagCol);

  // Status bar
  statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBar.text = '$(eye) Kodeye';
  statusBar.tooltip = 'Click to analyse file';
  statusBar.command = 'kodeye.analyzeFile';
  statusBar.show();
  context.subscriptions.push(statusBar);

  // Commands
  context.subscriptions.push(
    vscode.commands.registerCommand('kodeye.analyzeFile',      () => analyze('file')),
    vscode.commands.registerCommand('kodeye.analyzeSelection', () => analyze('selection')),
    vscode.commands.registerCommand('kodeye.generateDocs',     () => analyze('docs')),
    vscode.commands.registerCommand('kodeye.clearDiagnostics', () => {
      diagCol.clear();
      vscode.window.showInformationMessage('Kodeye: Diagnostics cleared.');
    })
  );

  // Confirm activation with notification + status bar
  vscode.window.showInformationMessage('👁️ Kodeye loaded! Right-click any file → Kodeye options.');
}

function deactivate() {
  if (panel)   panel.dispose();
  if (diagCol) diagCol.dispose();
  if (statusBar) statusBar.dispose();
}

module.exports = { activate, deactivate };
