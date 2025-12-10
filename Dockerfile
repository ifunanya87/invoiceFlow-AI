FROM python:3.12-bookworm

# Install System Dependencies and Build Tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libfreetype6 \
    libjpeg62-turbo \
    libpng16-16 \
    libpoppler-cpp-dev \
    libxml2-dev \
    libxslt1-dev \
    pkg-config \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

# Install the 'uv' package installer
RUN pip install uv==0.9.16

# Copy configuration files
COPY pyproject.toml uv.lock ./

# Environment Variables
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Install Python Dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Copy Source Code
COPY src /app/src

# Final Configuration
EXPOSE 8000

# Set environment paths and command
ENV PATH="/app/.venv/bin:$PATH"
# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["bash"]
