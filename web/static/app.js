/* DON v3.0 dashboard front-end */
(() => {
  "use strict";
  const $ = (s) => document.querySelector(s);

  // Clock
  function tick(){
    const n = new Date();
    $("#clock").textContent = n.toLocaleTimeString([], {hour12:false});
    $("#date").textContent = n.toLocaleDateString([], {weekday:"long", month:"short", day:"numeric"});
  }
  setInterval(tick, 1000); tick();

  // Conversation
  const convo = $("#convo");
  function add(role, text){
    const w = document.createElement("div");
    w.className = "msg " + role;
    const b = document.createElement("div");
    b.className = "b";
    b.textContent = text;
    w.appendChild(b);
    convo.appendChild(w);
    convo.scrollTop = convo.scrollHeight;
    return w;
  }
  function logActivity(t){
    const log = $("#log");
    const li = document.createElement("li");
    li.textContent = t;
    log.prepend(li);
    while (log.children.length > 30) log.lastChild.remove();
  }

  // Send message
  const form = $("#form"), input = $("#text"), sendBtn = $("#send");
  async function send(text){
    text = (text || "").trim();
    if (!text) return;
    add("user", text);
    input.value = "";
    sendBtn.disabled = true;
    const thinking = add("think", "DON is thinking…");
    try {
      const res = await fetch("/api/chat", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({text})
      });
      const data = await res.json();
      thinking.remove();
      add("don", data.reply || "…");
      logActivity("You: " + text.slice(0, 40));
      refreshReminders();
    } catch(e){
      thinking.remove();
      add("don", "Connection error: " + e.message + " (is the server still running?)");
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }
  form.addEventListener("submit", (e) => { e.preventDefault(); send(input.value); });

  // Example prompts
  $("#examples").addEventListener("click", (e) => {
    const li = e.target.closest("li[data-q]");
    if (li) send(li.dataset.q);
  });

  // Status
  async function refreshStatus(){
    try{
      const s = await (await fetch("/api/status")).json();
      $("#fmodel").textContent = s.model;
      $("#fup").textContent = s.uptime;
      const dot = $("#dot"), stat = $("#stat"), fb = $("#fbrain");
      if (s.brain_ready){
        dot.className = "dot on"; stat.textContent = "ONLINE";
        fb.textContent = "Brain: online"; fb.className = "ok";
      } else {
        dot.className = "dot off"; stat.textContent = "NO API KEY";
        fb.textContent = "Brain: offline (add GEMINI_API_KEY to .env)"; fb.className = "warn";
      }
    }catch(_){}
  }
  refreshStatus(); setInterval(refreshStatus, 5000);

  async function refreshReminders(){
    try{
      const data = await (await fetch("/api/reminders")).json();
      const ul = $("#reminders");
      const items = data.reminders || [];
      if (!items.length){ ul.innerHTML = '<li class="empty">None yet.</li>'; return; }
      ul.innerHTML = items.map(r =>
        `<li>${(r.message||"").replace(/</g,"&lt;")} <span style="color:#7c8aa5">@ ${r.due}</span></li>`
      ).join("");
    }catch(_){}
  }
  refreshReminders(); setInterval(refreshReminders, 10000);

  // WebSocket live stats
  function connectWS(){
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/ws`);
    ws.onmessage = (ev) => {
      let m; try{ m = JSON.parse(ev.data); }catch{ return; }
      setGauge("#cpu","#cpuv", m.cpu);
      setGauge("#mem","#memv", m.memory);
      if (m.uptime) $("#fup").textContent = m.uptime;
    };
    ws.onclose = () => setTimeout(connectWS, 2000);
    ws.onerror = () => { try{ ws.close(); }catch(_){} };
  }
  function setGauge(bar, val, pct){
    pct = Math.max(0, Math.min(100, Number(pct)||0));
    $(bar).style.width = pct + "%";
    $(val).textContent = pct.toFixed(0) + "%";
  }
  connectWS();

  // Animated grid background
  const bg = $("#bg"), g = bg.getContext("2d");
  function resize(){ bg.width = innerWidth; bg.height = innerHeight; }
  addEventListener("resize", resize); resize();
  let off = 0;
  (function draw(){
    g.clearRect(0,0,bg.width,bg.height);
    const sp = 44; off = (off + 0.25) % sp;
    for (let x=-sp+off; x<bg.width; x+=sp){ g.strokeStyle="rgba(0,212,255,.05)"; g.beginPath(); g.moveTo(x,0); g.lineTo(x,bg.height); g.stroke(); }
    for (let y=-sp+off; y<bg.height; y+=sp){ g.strokeStyle="rgba(255,59,59,.045)"; g.beginPath(); g.moveTo(0,y); g.lineTo(bg.width,y); g.stroke(); }
    requestAnimationFrame(draw);
  })();

  input.focus();
})();
