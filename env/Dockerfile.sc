# v4 SC task image (no lock, no rule). Build with --build-arg TASK=safety|capabilities.
FROM python:3.13-slim
ARG TASK
RUN test "$TASK" = safety || test "$TASK" = capabilities
RUN pip install --no-cache-dir pytest==9.2.0 claude-agent-sdk==0.2.182 \
 && useradd --create-home --uid 1000 --shell /bin/bash agent
COPY sc/${TASK}/ /work/
RUN chown -R agent:agent /work && chown root:root /work && chmod 1777 /work \
 && mkdir -m 0700 /opt/harness \
 && echo "sc-$TASK" > /opt/harness/variant
ENV HTTPS_PROXY=http://egress-proxy:8888 \
    HTTP_PROXY=http://egress-proxy:8888 \
    NO_PROXY=localhost,127.0.0.1 \
    DISABLE_TELEMETRY=1 \
    DISABLE_ERROR_REPORTING=1 \
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
WORKDIR /work
USER agent
CMD ["sleep", "infinity"]
