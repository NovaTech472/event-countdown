from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
import threading
import os

# static_folder="." serves index.html, script.js, style.css from same directory
app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# ── Email config ──────────────────────────────────────────────────────────────
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = os.getenv("SMTP_USER", "jishat5000@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "caaszodpaugjIdun")

active_jobs: dict = {}


# ── Serve frontend ────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)


# ── Email sender ──────────────────────────────────────────────────────────────
def send_notification_email(event_name: str, to_email: str, notify_type: str = "start"):
    try:
        msg = MIMEMultipart("alternative")

        if notify_type == "reminder_1day":
            subject   = f"⏰ 1 Day Until '{event_name}'!"
            heading   = "Tomorrow is the big day!"
            body_text = f"Your event <strong>{event_name}</strong> is happening <strong>tomorrow</strong>. Get ready!"
            icon      = "⏰"
        elif notify_type == "reminder_1hour":
            subject   = f"🔔 1 Hour Until '{event_name}'!"
            heading   = "Just 1 hour to go!"
            body_text = f"Your event <strong>{event_name}</strong> starts in <strong>1 hour</strong>. Almost there!"
            icon      = "🔔"
        else:
            subject   = f"🎉 '{event_name}' Has Started!"
            heading   = "Your event is live!"
            body_text = f"Your event <strong>{event_name}</strong> has just <strong>started</strong>. Enjoy every moment!"
            icon      = "🎉"

        msg["Subject"] = subject
        msg["From"]    = SMTP_USER
        msg["To"]      = to_email

        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#f0f4f8;margin:0;padding:40px 0}}
  .c{{max-width:520px;margin:0 auto;background:#fff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.10);overflow:hidden}}
  .h{{background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);padding:40px 32px 32px;text-align:center}}
  .ic{{font-size:48px;display:block;margin-bottom:12px}}
  .h h1{{color:#e0c97f;font-size:22px;margin:0;letter-spacing:1px;font-weight:700}}
  .b{{padding:36px 32px}}.b p{{color:#333;font-size:16px;line-height:1.7}}
  .eb{{background:#f7f3e8;border-left:4px solid #e0c97f;border-radius:8px;padding:16px 20px;margin:20px 0}}
  .eb span{{font-size:20px;font-weight:700;color:#1a1a2e}}
  .f{{background:#f7f7f7;padding:18px 32px;text-align:center;color:#aaa;font-size:12px;border-top:1px solid #eee}}
</style></head><body>
<div class="c">
  <div class="h"><span class="ic">{icon}</span><h1>{heading}</h1></div>
  <div class="b">
    <p>{body_text}</p>
    <div class="eb"><span>📌 {event_name}</span></div>
    <p style="color:#777;font-size:14px">This is an automated reminder from your Event Countdown app.</p>
  </div>
  <div class="f">Event Countdown &bull; You set this reminder yourself</div>
</div></body></html>"""

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        print(f"[Email OK] type={notify_type} to={to_email} event='{event_name}'")

    except smtplib.SMTPAuthenticationError:
        print("[Email ERROR] Authentication failed — check App Password")
    except Exception as e:
        print(f"[Email ERROR] {e}")


# ── Timer helper ──────────────────────────────────────────────────────────────
def schedule_timer(delay_seconds: float, job_id: str, fn, *args):
    if delay_seconds <= 0:
        return
    t = threading.Timer(delay_seconds, fn, args=args)
    t.daemon = True
    t.start()
    active_jobs[job_id] = t


# ── API: start countdown ──────────────────────────────────────────────────────
@app.route("/api/start-countdown", methods=["POST"])
def start_countdown():
    data           = request.get_json()
    event_name     = (data.get("event_name")  or "").strip()
    event_date_str = (data.get("event_date")  or "").strip()
    email          = (data.get("email")       or "").strip()

    if not event_name or not event_date_str or not email:
        return jsonify({"error": "event_name, event_date, and email are required"}), 400

    try:
        event_dt = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
    except ValueError:
        return jsonify({"error": "Invalid date format."}), 400

    if event_dt.tzinfo is None:
        event_dt = event_dt.replace(tzinfo=timezone.utc)

    now           = datetime.now(timezone.utc)
    total_seconds = (event_dt - now).total_seconds()

    if total_seconds <= 0:
        return jsonify({"error": "Event date must be in the future"}), 400

    base_id  = f"{email}|{event_name}"
    one_day  = 86400
    one_hour = 3600

    for suffix in ("_start", "_1day", "_1hour"):
        jid = base_id + suffix
        if jid in active_jobs:
            active_jobs[jid].cancel()
            del active_jobs[jid]

    schedule_timer(total_seconds, base_id + "_start",
                   send_notification_email, event_name, email, "start")
    if total_seconds > one_day:
        schedule_timer(total_seconds - one_day, base_id + "_1day",
                       send_notification_email, event_name, email, "reminder_1day")
    if total_seconds > one_hour:
        schedule_timer(total_seconds - one_hour, base_id + "_1hour",
                       send_notification_email, event_name, email, "reminder_1hour")

    print(f"[Countdown] Started '{event_name}' — {int(total_seconds)}s remaining")

    return jsonify({
        "message":           "Countdown started successfully",
        "job_id":            base_id,
        "seconds_remaining": int(total_seconds),
        "reminders_scheduled": {
            "at_event":        True,
            "one_day_before":  total_seconds > one_day,
            "one_hour_before": total_seconds > one_hour,
        }
    }), 200


# ── API: cancel countdown ─────────────────────────────────────────────────────
@app.route("/api/cancel-countdown", methods=["POST"])
def cancel_countdown():
    data   = request.get_json()
    job_id = (data.get("job_id") or "").strip()

    cancelled = []
    for suffix in ("_start", "_1day", "_1hour"):
        jid = job_id + suffix
        if jid in active_jobs:
            active_jobs[jid].cancel()
            del active_jobs[jid]
            cancelled.append(jid)

    if cancelled:
        return jsonify({"message": f"Cancelled {len(cancelled)} timer(s)", "cancelled": cancelled}), 200
    return jsonify({"error": "No active job found"}), 404


# ── API: status ───────────────────────────────────────────────────────────────
@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "status":        "running",
        "active_timers": len(active_jobs),
        "jobs":          list(active_jobs.keys())
    }), 200


# ── Local dev only — gunicorn ignores this on Railway ────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
