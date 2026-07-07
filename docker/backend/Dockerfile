FROM python:3.12-slim AS builder

WORKDIR /build
RUN pip install --no-cache-dir build

COPY backend/ backend/
COPY database/ database/
COPY simulation/ simulation/
COPY gis/ gis/

RUN pip install --no-cache-dir gis/ database/ simulation/ backend/

FROM python:3.12-slim

RUN groupadd -r dmdt && useradd -r -g dmdt dmdt
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /build/backend/app /app/app
COPY --from=builder /build/database /app/database
COPY --from=builder /build/backend/pyproject.toml /app/

EXPOSE 8000
USER dmdt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
