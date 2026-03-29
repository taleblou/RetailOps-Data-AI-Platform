FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN pip install --no-cache-dir uv
COPY . .
RUN uv sync --frozen || uv sync
CMD ["uv", "run", "python", "-m", "modules.abc_xyz_intelligence.main"]
