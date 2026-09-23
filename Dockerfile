FROM debian:bookworm-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential ca-certificates curl git gzip libgmp10 python3 tar \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.elan/bin:${PATH}"
RUN set -eu; \
    test "$(uname -m)" = x86_64; \
    curl -fsSL --retry 3 \
      https://github.com/leanprover/elan/releases/download/v4.2.4/elan-x86_64-unknown-linux-gnu.tar.gz \
      -o /tmp/elan.tar.gz; \
    echo '42b94d4244e8353142c456ec0e4ca6528fd898a6c604d4059f494e706e431f63  /tmp/elan.tar.gz' | sha256sum -c -; \
    tar -xzf /tmp/elan.tar.gz -C /tmp; \
    /tmp/elan-init -y --default-toolchain none --no-modify-path; \
    elan toolchain install leanprover/lean4:v4.28.0; \
    elan default leanprover/lean4:v4.28.0; \
    lean --version

WORKDIR /src
COPY . .
ARG SOURCE_COMMIT
RUN test -n "$SOURCE_COMMIT" \
    && test "$(git rev-parse HEAD)" = "$SOURCE_COMMIT" \
    && test -z "$(git status --porcelain)" \
    && bash site/build.sh \
    && SOURCE_COMMIT="$SOURCE_COMMIT" python3 -c 'import json, os; from pathlib import Path; p=Path("site/_out/html-multi"); d=json.loads((p/"build-info.json").read_text()); assert d["source_revision"] == os.environ["SOURCE_COMMIT"] and d["source_tree_clean"] is True; assert len(list(p.rglob("*.html"))) == 16'

FROM nginx:1.28.1-alpine AS runtime
ARG SOURCE_COMMIT
LABEL org.opencontainers.image.revision="$SOURCE_COMMIT"
COPY --from=builder /src/site/_out/html-multi/ /usr/share/nginx/html/
EXPOSE 80
HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/ \
      && wget -q -O /dev/null http://127.0.0.1/en/ || exit 1
