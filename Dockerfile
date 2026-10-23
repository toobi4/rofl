FROM python:3.13-slim
WORKDIR /opt/hwee
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
ENTRYPOINT ["hwee"]
