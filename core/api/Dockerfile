FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock README.md /app/
RUN uv sync --frozen --no-dev
COPY core /app/core
COPY modules /app/modules
COPY config /app/config
COPY data /app/data
CMD ["uv", "run", "uvicorn", "core.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
