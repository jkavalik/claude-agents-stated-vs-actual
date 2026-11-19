# Egress proxy: CONNECT to api.anthropic.com:443 only, everything else denied and logged.
FROM alpine:3.20
RUN apk add --no-cache tinyproxy
COPY tinyproxy.conf filter /etc/tinyproxy/
EXPOSE 8888
CMD ["tinyproxy", "-d", "-c", "/etc/tinyproxy/tinyproxy.conf"]
