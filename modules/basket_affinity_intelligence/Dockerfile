FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN pip install --no-cache-dir uv
COPY . .
RUN uv sync --no-dev
CMD ["uv", "run", "python", "-m", "modules.basket_affinity_intelligence.main"]
