#!/bin/sh
/usr/sbin/sshd
exec uvicorn app:app --host 0.0.0.0 --port 8080 --app-dir /opt/device
