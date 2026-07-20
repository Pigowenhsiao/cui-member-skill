FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Create workspace
WORKDIR /workspace

# Install yt-dlp via uv
RUN uv tool install yt-dlp
ENV PATH="/root/.local/bin:${PATH}"

ENTRYPOINT ["tail", "-f", "/dev/null"]
