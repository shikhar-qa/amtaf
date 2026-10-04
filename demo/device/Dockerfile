FROM python:3.12-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends openssh-server \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /run/sshd \
 && useradd -m tester && echo "tester:tester" | chpasswd \
 && touch /etc/device.conf /var/log/device.log \
 && chmod 666 /etc/device.conf /var/log/device.log
RUN pip install --no-cache-dir fastapi uvicorn python-multipart
COPY app.py entrypoint.sh /opt/device/
RUN chmod +x /opt/device/entrypoint.sh
EXPOSE 22 8080
CMD ["/opt/device/entrypoint.sh"]
