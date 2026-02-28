// Auto-detect: use same origin on Railway, localhost for local dev
const API = (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost")
  ? "http://127.0.0.1:5000/api"
  : window.location.origin + "/api";

let activeTimer = null;
let currentJobId = null;

function setStatus(msg, type = "info") {
  const el = document.getElementById("statusMsg");
  el.textContent = msg;
  el.className = "status-msg " + type;
}

function startCountdown() {
  const eventName = document.getElementById("eventName").value.trim();
  const dateVal   = document.getElementById("eventDate").value;
  const email     = document.getElementById("email").value.trim();

  if (!eventName || !dateVal || !email) {
    alert("Please fill in all fields.");
    return;
  }

  const eventDate = new Date(dateVal + "T00:00:00");

  if (isNaN(eventDate.getTime())) {
    alert("Invalid date selected.");
    return;
  }

  if (eventDate <= new Date()) {
    alert("Please choose a future date.");
    return;
  }

  if (activeTimer) {
    clearInterval(activeTimer);
    activeTimer = null;
  }

  document.getElementById("countdownDisplay").style.display = "block";
  document.getElementById("startedBanner").style.display    = "none";
  document.getElementById("eventTitleDisplay").textContent  = eventName;
  document.getElementById("cancelBtn").style.display        = "inline-flex";

  runLocalTimer(eventDate, eventName);

  setStatus("Connecting to server…", "info");

  fetch(`${API}/start-countdown`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event_name: eventName,
      event_date: eventDate.toISOString(),
      email: email,
    }),
  })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        setStatus("Backend: " + data.error, "err");
      } else {
        currentJobId = data.job_id;
        const r = data.reminders_scheduled;
        const parts = [];
        if (r.one_day_before)  parts.push("1 day before");
        if (r.one_hour_before) parts.push("1 hour before");
        if (r.at_event)        parts.push("at start");
        setStatus("✓ Email reminders set: " + parts.join(", "), "ok");
      }
    })
    .catch(() => {
      setStatus("⚠ Backend offline — countdown running, no emails.", "err");
    });
}

function runLocalTimer(eventDate, eventName) {
  activeTimer = setInterval(function () {
    const distance = eventDate.getTime() - Date.now();

    if (distance <= 0) {
      clearInterval(activeTimer);
      activeTimer = null;
      document.getElementById("countdownDisplay").style.display = "none";
      document.getElementById("startedBanner").style.display    = "block";
      document.getElementById("startedEventName").textContent   = eventName;
      document.getElementById("cancelBtn").style.display        = "none";
      setStatus("", "");
      return;
    }

    const days    = Math.floor(distance / 86400000);
    const hours   = Math.floor((distance % 86400000) / 3600000);
    const minutes = Math.floor((distance % 3600000)  / 60000);
    const seconds = Math.floor((distance % 60000)    / 1000);

    document.getElementById("cntDays").textContent  = pad(days);
    document.getElementById("cntHours").textContent = pad(hours);
    document.getElementById("cntMins").textContent  = pad(minutes);
    document.getElementById("cntSecs").textContent  = pad(seconds);

  }, 1000);
}

function pad(n) {
  return n < 10 ? "0" + n : String(n);
}

function cancelCountdown() {
  if (activeTimer) {
    clearInterval(activeTimer);
    activeTimer = null;
  }
  document.getElementById("countdownDisplay").style.display = "none";
  document.getElementById("cancelBtn").style.display        = "none";
  setStatus("Countdown cancelled.", "info");

  if (!currentJobId) return;

  fetch(`${API}/cancel-countdown`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: currentJobId }),
  })
    .then(res => res.json())
    .then(data => console.log("Cancelled:", data.message))
    .catch(() => {});

  currentJobId = null;
}

// Starfield
(function () {
  const container = document.getElementById("stars");
  for (let i = 0; i < 90; i++) {
    const s = document.createElement("div");
    s.className = "star";
    const size = Math.random() * 2.2 + 0.5;
    s.style.cssText = `width:${size}px;height:${size}px;left:${Math.random()*100}%;top:${Math.random()*100}%;--d:${3+Math.random()*6}s;--delay:${Math.random()*6}s;--op:${0.3+Math.random()*0.6}`;
    container.appendChild(s);
  }
})();
