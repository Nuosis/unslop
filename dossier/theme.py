"""One token set. Elements draw only from these, so an agent cannot produce
off-brand output and cannot inject styling — it supplies values, never markup."""

CSS = """
:root{--bg:#F4F6F8;--surface:#fff;--surface2:#E9EEF3;--ink:#161D25;--soft:#57646F;
--faint:#8492A0;--rule:#D8E0E8;--accent:#96610F;--ok:#1F6157;--okbg:#E2EFEC;
--warn:#96610F;--warnbg:#F5EBD9;--bad:#8E4234;--badbg:#F7E7E3;
--display:"Bricolage Grotesque",ui-sans-serif,system-ui,sans-serif;
--body:"Source Serif 4",Georgia,serif;--mono:"JetBrains Mono",ui-monospace,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){
--bg:#101419;--surface:#181F26;--surface2:#212A33;--ink:#E6ECF2;--soft:#9DAAB7;
--faint:#77848F;--rule:#2B353F;--accent:#D9A445;--ok:#6FB6A7;--okbg:#152722;
--warn:#D9A445;--warnbg:#2E2717;--bad:#CE8272;--badbg:#2C1C18}}
:root[data-theme=dark]{--bg:#101419;--surface:#181F26;--surface2:#212A33;--ink:#E6ECF2;
--soft:#9DAAB7;--faint:#77848F;--rule:#2B353F;--accent:#D9A445;--ok:#6FB6A7;
--okbg:#152722;--warn:#D9A445;--warnbg:#2E2717;--bad:#CE8272;--badbg:#2C1C18}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);
font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:820px;margin:0 auto;padding:2.5rem 1.25rem 4rem}
h1{font-family:var(--display);font-size:1.9rem;line-height:1.15;font-weight:700;
letter-spacing:-.02em;margin:0 0 .4rem;text-wrap:balance}
.sum{color:var(--soft);margin:0 0 2rem;max-width:62ch}
.stamp{font-family:var(--mono);font-size:.72rem;color:var(--faint);
border-top:1px solid var(--rule);padding-top:.9rem;margin-top:2.5rem}
h2{font-family:var(--display);font-size:.74rem;font-weight:600;text-transform:uppercase;
letter-spacing:.1em;color:var(--faint);margin:0 0 .7rem}
.el{background:var(--surface);border:1px solid var(--rule);border-radius:9px;
padding:1.1rem 1.3rem;margin-bottom:1rem}
.list ul{margin:0;padding-left:1.15rem}.list li{margin-bottom:.4rem}
.list li:last-child{margin-bottom:0}
dl{margin:0;display:grid;gap:.5rem}
.f{display:grid;grid-template-columns:minmax(7rem,auto) 1fr;gap:.9rem;align-items:baseline}
@media(max-width:560px){.f{grid-template-columns:1fr;gap:.15rem}}
dt{font-family:var(--display);font-size:.8rem;font-weight:600;color:var(--faint)}
dd{margin:0}
.timeline ol{list-style:none;margin:0;padding:0;display:grid;gap:.7rem}
.timeline li{display:grid;grid-template-columns:auto 1fr;gap:.9rem;align-items:baseline;
padding-left:.9rem;border-left:2px solid var(--rule)}
.when{font-family:var(--mono);font-size:.78rem;color:var(--faint);white-space:nowrap}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.94rem}
th{font-family:var(--display);font-size:.7rem;text-transform:uppercase;letter-spacing:.07em;
color:var(--faint);text-align:left;padding:0 .7rem .5rem 0;border-bottom:1px solid var(--rule)}
td{padding:.55rem .7rem .55rem 0;border-bottom:1px solid var(--surface2);vertical-align:top}
tr:last-child td{border-bottom:0}
.pill{font-family:var(--display);font-size:.68rem;font-weight:600;text-transform:uppercase;
letter-spacing:.05em;padding:.16rem .48rem;border-radius:4px;white-space:nowrap}
.pill.ok{background:var(--okbg);color:var(--ok)}
.pill.warn{background:var(--warnbg);color:var(--warn)}
.pill.bad{background:var(--badbg);color:var(--bad)}
.pill.neutral{background:var(--surface2);color:var(--soft)}
.decision .q{margin:0 0 .8rem;font-weight:600}
.decision ul{list-style:none;margin:0;padding:0;display:grid;gap:.6rem}
.opt{border:1px solid var(--rule);border-radius:7px;padding:.7rem .9rem;display:grid;gap:.2rem}
.opt.rec{border-color:var(--accent);background:var(--warnbg)}
.name{font-family:var(--display);font-weight:600}
.tag{font-family:var(--display);font-size:.64rem;font-weight:600;text-transform:uppercase;
letter-spacing:.06em;color:var(--accent);justify-self:start}
.detail{color:var(--soft);font-size:.94rem}
.metrics .row{display:flex;flex-wrap:wrap;gap:1.6rem}
.m{display:grid;gap:.1rem}
.v{font-family:var(--display);font-size:1.7rem;font-weight:700;line-height:1;
font-variant-numeric:tabular-nums}
.l{font-size:.8rem;color:var(--faint);text-transform:uppercase;letter-spacing:.06em;
font-family:var(--display);font-weight:600}
.n{font-size:.85rem;color:var(--soft)}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""
