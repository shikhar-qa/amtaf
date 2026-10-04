"""Simulated appliance: management console + REST API (the demo target).

State lives in /etc/device.conf (key=value) and /var/log/device.log, so the
SSH layer can verify what the GUI layer claims. A fault flag makes the UI say
"Saved" without persisting, to demonstrate cross-layer failure diagnosis.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()
STATE = {"fault": False}


def conf_path() -> Path:
    return Path(os.getenv("DEVICE_CONF", "/etc/device.conf"))


def log_path() -> Path:
    return Path(os.getenv("DEVICE_LOG", "/var/log/device.log"))


def log(level: str, message: str, request: Request) -> None:
    run_id = request.headers.get("x-run-id", "-")
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    with log_path().open("a") as fh:
        fh.write(f"{stamp} {level} {message} run_id={run_id}\n")


def read_conf() -> dict[str, str]:
    path = conf_path()
    if not path.exists():
        return {}
    pairs = (
        line.split("=", 1) for line in path.read_text().splitlines() if "=" in line
    )
    return {k.strip(): v.strip() for k, v in pairs}


def write_conf(conf: dict[str, str]) -> None:
    conf_path().write_text("".join(f"{k}={v}\n" for k, v in conf.items()))


def page(body: str) -> HTMLResponse:
    return HTMLResponse(f"<html><body><h1>Device Console</h1>{body}</body></html>")


@app.get("/login", response_class=HTMLResponse)
def login_form() -> HTMLResponse:
    return page(
        '<form method="post" action="/login">'
        '<input id="username" name="username">'
        '<input id="password" name="password" type="password">'
        '<button id="login" type="submit">Log in</button></form>'
    )


@app.post("/login")
def login(
    request: Request, username: str = Form(), password: str = Form()
):  # noqa: E501,ANN201
    if (username, password) != ("admin", "admin"):
        log("WARN", f"login failed user={username}", request)
        return page("<p id='status'>Invalid credentials</p>")
    response = RedirectResponse("/settings", status_code=303)
    response.set_cookie("session", "ok")
    log("INFO", "login ok", request)
    return response


@app.get("/settings", response_class=HTMLResponse)
def settings(request: Request, saved: int = 0):  # noqa: E501,ANN201
    if request.cookies.get("session") != "ok":
        return RedirectResponse("/login", status_code=303)
    value = read_conf().get("syslog_server", "")
    banner = '<div id="status">Saved</div>' if saved else ""
    return page(
        '<form method="post" action="/settings">'
        f'<input id="syslog_server" name="syslog_server" value="{value}">'
        '<button id="save" type="submit">Save</button></form>' + banner
    )


@app.post("/settings")
def save_settings(request: Request, syslog_server: str = Form()):  # noqa: E501,ANN201
    if request.cookies.get("session") != "ok":
        return RedirectResponse("/login", status_code=303)
    if STATE["fault"]:
        log("WARN", f"persist failed key=syslog_server value={syslog_server}", request)
    else:
        conf = read_conf()
        conf["syslog_server"] = syslog_server
        write_conf(conf)
        log("INFO", f"persisted key=syslog_server value={syslog_server}", request)
    return RedirectResponse("/settings?saved=1", status_code=303)


@app.get("/api/settings")
def api_settings() -> dict[str, str]:
    return read_conf()


@app.post("/api/fault")
def api_fault(body: dict[str, bool]) -> dict[str, bool]:
    STATE["fault"] = bool(body.get("enabled", False))
    return {"fault": STATE["fault"]}
