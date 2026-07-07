FROM python:3.12-slim AS builder

WORKDIR /build
RUN pip install --no-cache-dir build

COPY simulation/ simulation/
COPY gis/ gis/
COPY database/ database/

RUN pip install --no-cache-dir gis/ database/ simulation/

FROM python:3.12-slim

RUN groupadd -r dmdt && useradd -r -g dmdt dmdt
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /build/simulation/dmdt_sim /app/dmdt_sim
COPY --from=builder /build/simulation/pyproject.toml /app/

RUN mkdir -p /app/data /app/output && chmod 755 /app/data /app/output

VOLUME ["/app/data", "/app/output"]
USER dmdt

ENTRYPOINT ["python", "-m", "dmdt_sim.main"]
CMD ["--duration", "86400", "--seed", "42"]
