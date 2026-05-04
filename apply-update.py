#!/usr/bin/env python3
import json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path.cwd()
INDEX = ROOT / "index.html"
MANIFEST = ROOT / "task-manifests" / "buildforge.json"
ANIME = Path.home() / "Desktop/digital-twin-platform/web/public/videos/anime_hero"
JOHN_SRC = ANIME / "john_kim/hero_transformation.mp4"
PRAVEEN_SRC = ANIME / "praveen_hirsave/hero_transformation.mp4"

C_OK = "\033[32m✓\033[0m"; C_SKIP = "\033[33m·\033[0m"; C_ERR = "\033[31m✗\033[0m"
def die(m): print(f"{C_ERR} {m}", file=sys.stderr); sys.exit(1)

if not INDEX.exists(): die(f"index.html not found in {ROOT}")
if not MANIFEST.exists(): die("task-manifests/buildforge.json not found")
if not JOHN_SRC.exists(): die(f"John video not found at:\n  {JOHN_SRC}")
if not PRAVEEN_SRC.exists(): die(f"Praveen video not found at:\n  {PRAVEEN_SRC}")
if subprocess.call(["which","ffmpeg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
    die("ffmpeg not installed. Run:  brew install ffmpeg")

CSS_BLOCK = """
  /* === Twin slides + dynamic carousel patch === */
  .shatter { position: absolute; inset: 0; z-index: 2; pointer-events: none; overflow: hidden; }
  .shatter .shard { position: absolute; inset: 0; background-size: cover; background-position: center; transform: translate3d(0,0,0) rotate(0); opacity: 1; will-change: transform, opacity; }
  .screen.active .shatter .shard { animation: shard-shatter 2.0s cubic-bezier(.62,.04,.36,1) 0.45s forwards; }
  @keyframes shard-shatter {
    0% { transform: translate3d(0,0,0) rotate(0); opacity: 1; }
    55% { opacity: 1; }
    100% { transform: translate3d(calc(var(--tx,0) * 1px), calc(var(--ty,0) * 1px), 0) rotate(calc(var(--rot,0) * 1deg)); opacity: 0; }
  }
  .cta-row { margin-top: 22px; display: flex; gap: 14px; flex-wrap: wrap; align-items: center; }
  .cta { display: inline-flex; align-items: center; gap: 8px; padding: 12px 22px; font-size: 13px; font-weight: 600; letter-spacing: .02em; text-decoration: none; border-radius: 999px; transition: transform .2s, box-shadow .2s, background .2s; white-space: nowrap; cursor: pointer; border: 0; font-family: inherit; }
  .cta--primary { background: var(--gold); color: #1b1409; }
  .cta--primary:hover { transform: translateY(-1px); box-shadow: 0 12px 36px -10px rgba(244,184,74,.6); }
  .screen .twin-video { z-index: 1; }
  @media (prefers-reduced-motion: reduce) {
    .screen.active .shatter .shard { animation: shard-fade .5s .2s forwards; }
    @keyframes shard-fade { to { opacity: 0; } }
  }
"""

JS_BLOCK = r"""
// === Twin slides + dynamic carousel patch ===
(() => {
  const $ = (s, r=document) => r.querySelector(s);
  const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));
  const screens = () => $$('#stage .screen');
  const cards = () => $$('#frames .frame-card');
  const curIdx = () => Math.max(0, screens().findIndex(s => s.classList.contains('active')));
  function go(to) {
    const ss = screens(), cc = cards(), n = ss.length;
    if (!n) return;
    const i = ((to % n) + n) % n;
    ss.forEach((s, k) => s.classList.toggle('active', k === i));
    cc.forEach((c, k) => c.classList.toggle('active', k === i));
    const cE = $('#count'); if (cE) cE.textContent = (i+1) + '/' + n;
    ss.forEach((s, k) => { const v = s.querySelector('video'); if (!v) return;
      try { if (k === i) { v.currentTime = 0; v.play().catch(()=>{}); } else v.pause(); } catch(e){} });
  }
  function rebind() {
    const p = $('#prev'), nx = $('#next');
    if (p && !p.dataset.dynBound) { const np = p.cloneNode(true); np.dataset.dynBound='1'; p.replaceWith(np); np.addEventListener('click', ()=>go(curIdx()-1)); }
    if (nx && !nx.dataset.dynBound) { const nn = nx.cloneNode(true); nn.dataset.dynBound='1'; nx.replaceWith(nn); nn.addEventListener('click', ()=>go(curIdx()+1)); }
    cards().forEach(c => { if (c.dataset.dynBound) return;
      const nc = c.cloneNode(true); nc.dataset.dynBound='1';
      c.replaceWith(nc); nc.addEventListener('click', ()=>go(cards().indexOf(nc))); });
  }
  if (!window.__dynKey) { window.__dynKey = true;
    window.addEventListener('keydown', e => {
      if (e.target && /INPUT|TEXTAREA/.test(e.target.tagName)) return;
      if (e.key==='ArrowRight'){ go(curIdx()+1); e.stopImmediatePropagation(); }
      else if (e.key==='ArrowLeft'){ go(curIdx()-1); e.stopImmediatePropagation(); }
    }, true);
  }
  if (!window.__dynObs) { window.__dynObs = new MutationObserver(()=>rebind());
    if ($('#stage')) window.__dynObs.observe($('#stage'), {childList:true});
    if ($('#frames')) window.__dynObs.observe($('#frames'), {childList:true});
  }
  function init(){ rebind(); go(curIdx()); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else setTimeout(init, 50);
})();

(function bootShatter(){
  const SHARDS = [
    [[[0,0],[35,0],[30,18],[10,22],[0,15]],[-180,-180,-8]],
    [[[35,0],[62,0],[58,15],[42,22],[30,18]],[0,-200,5]],
    [[[62,0],[100,0],[100,12],[82,18],[58,15]],[180,-200,-6]],
    [[[100,12],[100,38],[78,32],[82,18]],[230,-110,9]],
    [[[0,15],[10,22],[18,38],[0,42]],[-230,-70,-10]],
    [[[30,18],[42,22],[48,40],[35,45],[18,38],[10,22]],[-110,-110,4]],
    [[[42,22],[58,15],[82,18],[78,32],[68,42],[48,40]],[80,-100,-7]],
    [[[100,38],[100,68],[82,62],[78,55],[78,32]],[230,0,8]],
    [[[0,42],[18,38],[35,45],[28,62],[12,68],[0,55]],[-230,0,-5]],
    [[[35,45],[48,40],[68,42],[62,58],[52,68],[28,62]],[0,55,6]],
    [[[68,42],[78,55],[82,62],[72,75],[62,58]],[150,55,-8]],
    [[[100,68],[100,100],[68,100],[62,82],[72,75],[82,62]],[200,200,7]],
    [[[0,55],[12,68],[28,62],[52,68],[48,90],[20,95],[0,80]],[-200,180,-9]],
    [[[28,62],[62,58],[62,82],[68,100],[48,90],[52,68]],[0,200,5]],
    [[[62,82],[72,75],[62,100],[48,90]],[70,230,-6]],
    [[[20,95],[48,90],[62,100],[20,100],[0,100],[0,80]],[-150,230,8]]
  ];
  function build(host){
    if (host.dataset.shatterBuilt) return;
    host.dataset.shatterBuilt = '1';
    const still = host.dataset.still; if (!still) return;
    const frag = document.createDocumentFragment();
    SHARDS.forEach(arr => {
      const poly = arr[0], tx = arr[1][0], ty = arr[1][1], rot = arr[1][2];
      const d = document.createElement('div');
      d.className = 'shard';
      const pts = poly.map(p => p[0]+'% '+p[1]+'%').join(',');
      d.style.cssText = 'background-image:url("'+still+'");clip-path:polygon('+pts+');-webkit-clip-path:polygon('+pts+');--tx:'+tx+';--ty:'+ty+';--rot:'+rot+';';
      frag.appendChild(d);
    });
    host.appendChild(frag);
  }
  function scan(r){ (r||document).querySelectorAll('.shatter[data-still]').forEach(build); }
  function init(){ scan();
    if (!window.__shatterObs) { window.__shatterObs = new MutationObserver(ms => ms.forEach(m => m.addedNodes.forEach(n => {
      if (n.nodeType !== 1) return;
      if (n.classList && n.classList.contains('shatter')) build(n);
      scan(n);
    })));
      window.__shatterObs.observe(document.body, {childList:true, subtree:true});
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();

document.addEventListener('click', e => {
  const t = e.target.closest('[data-cta="twin"]');
  if (!t) return;
  e.preventDefault();
  const live = t.dataset.href;
  if (live) { window.open(live, '_blank', 'noopener'); return; }
  const cb = document.querySelector('#contact');
  if (cb) cb.click();
  setTimeout(() => {
    const ta = document.querySelector('#contactMessage');
    if (ta && !ta.value) {
      ta.value = t.dataset.intent || 'I want to talk about a digital twin.';
      ta.dispatchEvent(new Event('input', { bubbles: true }));
      ta.focus();
    }
  }, 80);
});
"""

NEW_SCREENS = """
  <article class="screen john-twin" data-frame="7" data-task-id="john-twin">
    <video class="twin-video" src="videos/john/anime-hero.mp4" autoplay muted loop playsinline preload="auto" poster="images/john-twin-still.jpg"></video>
    <div class="shatter" data-still="images/john-twin-still.jpg" aria-hidden="true"></div>
    <div class="scrim"></div>
    <div class="hero">
      <div class="eyebrow">Digital Twin · John Kim</div>
      <h2>The version of you that doesn't sleep.</h2>
      <p>Trained on the way you think. Reviews PRDs, scores strategies, accelerates the decisions that used to wait on your calendar. One you, working in parallel.</p>
      <div class="cta-row">
        <button class="cta cta--primary" data-cta="twin" data-intent="I want to talk about John's digital twin — reviewing strategies and PRDs in parallel.">Meet your twin <span aria-hidden="true">→</span></button>
      </div>
    </div>
  </article>
  <article class="screen praveen-twin" data-frame="8" data-task-id="praveen-twin">
    <video class="twin-video" src="videos/praveen/anime-hero.mp4" autoplay muted loop playsinline preload="auto" poster="images/praveen-still.jpg"></video>
    <div class="shatter" data-still="images/praveen-still.jpg" aria-hidden="true"></div>
    <div class="scrim"></div>
    <div class="hero">
      <div class="eyebrow">Digital Twin · Praveen Hirsave</div>
      <h2>The CTO who never logs off.</h2>
      <p>Trained on how Praveen architects, codes, and ships. Reviews systems, audits diffs, accelerates builds — while the team sleeps.</p>
      <div class="cta-row">
        <button class="cta cta--primary" data-cta="twin" data-intent="I want to talk about Praveen's digital twin — auditing systems and reviewing diffs in parallel.">Meet Praveen's twin <span aria-hidden="true">→</span></button>
      </div>
    </div>
  </article>
"""

NEW_CARDS = """
  <button type="button" class="frame-card" data-task-id="john-twin"><small>Live now</small><b>7. John's Twin</b><span>The version of you that doesn't sleep — reviews PRDs, scores strategies, ships decisions while you sleep.</span></button>
  <button type="button" class="frame-card" data-task-id="praveen-twin"><small>Live now</small><b>8. Praveen's Twin</b><span>Praveen's anime hero shatters into the digital twin auditing systems and reviewing diffs while the team sleeps.</span></button>
"""

print("→ Patching index.html")
html_orig = INDEX.read_text()
html = html_orig
if 'data-task-id="praveen-twin"' in html:
    print(f"  {C_SKIP} Already patched. Skipping HTML edits.")
else:
    last_style = html.rfind("</style>")
    if last_style < 0: die("no </style> in index.html")
    html = html[:last_style] + CSS_BLOCK + html[last_style:]
    last_script = html.rfind("</script>")
    if last_script < 0: die("no </script> in index.html")
    html = html[:last_script] + JS_BLOCK + html[last_script:]
    stage_re = re.compile(r'(<section[^>]*\bid=["\']?stage["\']?[^>]*>)([\s\S]*?)(</section>)')
    if not stage_re.search(html): die('<section id="stage"> not found')
    html = stage_re.sub(lambda m: m.group(1)+m.group(2)+NEW_SCREENS+m.group(3), html, count=1)
    frames_re = re.compile(r'(<section[^>]*\bid=["\']?frames["\']?[^>]*>)([\s\S]*?)(</section>)')
    if not frames_re.search(html): die('<section id="frames"> not found')
    html = frames_re.sub(lambda m: m.group(1)+m.group(2)+NEW_CARDS+m.group(3), html, count=1)
    INDEX.with_suffix(".html.bak").write_text(html_orig)
    INDEX.write_text(html)
    print(f"  {C_OK} CSS+JS appended, 2 screens + 2 frame-cards inserted, backup at index.html.bak")

print("→ Updating manifest")
mfst_orig = MANIFEST.read_text()
mfst = json.loads(mfst_orig)
ids = {t.get("id") for t in mfst.get("tasks", [])}
if "praveen-twin" in ids:
    print(f"  {C_SKIP} Twin entries already present.")
else:
    mfst.setdefault("tasks", []).extend([
        {"frame":7,"title":"John's Twin","id":"john-twin","status":"SUCCEEDED","videoUrl":"videos/john/anime-hero.mp4","stillUrl":"images/john-twin-still.jpg"},
        {"frame":8,"title":"Praveen's Twin","id":"praveen-twin","status":"SUCCEEDED","videoUrl":"videos/praveen/anime-hero.mp4","stillUrl":"images/praveen-still.jpg"},
    ])
    MANIFEST.with_suffix(".json.bak").write_text(mfst_orig)
    MANIFEST.write_text(json.dumps(mfst, indent=2))
    print(f"  {C_OK} 2 entries appended (backup at buildforge.json.bak)")

print("→ Copying media")
(ROOT/"videos/john").mkdir(parents=True, exist_ok=True)
(ROOT/"videos/praveen").mkdir(parents=True, exist_ok=True)
(ROOT/"images").mkdir(parents=True, exist_ok=True)

for label, src, dst_rel in [("John", JOHN_SRC, "videos/john/anime-hero.mp4"),
                            ("Praveen", PRAVEEN_SRC, "videos/praveen/anime-hero.mp4")]:
    dst = ROOT / dst_rel
    if dst.exists() and dst.stat().st_size > 0:
        print(f"  {C_SKIP} {label} video already at {dst_rel}")
    else:
        shutil.copy(src, dst)
        print(f"  {C_OK} Copied {label} video → {dst_rel} ({dst.stat().st_size/(1024*1024):.1f} MB)")

print("→ Generating stills (frame 1 of each video)")
for label, vid_rel, still_rel in [("John", "videos/john/anime-hero.mp4", "images/john-twin-still.jpg"),
                                  ("Praveen", "videos/praveen/anime-hero.mp4", "images/praveen-still.jpg")]:
    still = ROOT / still_rel
    if still.exists() and still.stat().st_size > 0:
        print(f"  {C_SKIP} {still_rel} exists")
    else:
        subprocess.run(["ffmpeg","-y","-i",str(ROOT/vid_rel),"-frames:v","1","-q:v","2",str(still)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  {C_OK} {still_rel} generated")

print()
print("─"*60)
print(f"{C_OK} All edits applied. Verify, then push.")
print("─"*60)
