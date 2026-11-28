# M6i Ingestion job
# Python 3.12.16
FROM python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b AS build
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b
RUN useradd --system --uid 10001 --no-create-home app && mkdir /data && chown 10001 /data
ENV DATA_DIR=/data
WORKDIR /app
COPY --from=build /install /usr/local
COPY src/ ./src/
COPY snapshot/ ./snapshot/
USER 10001
CMD ["python", "-m", "src.cli"]
