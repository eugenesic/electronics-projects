# ==============================
# Базовый образ с micromamba
# ==============================
FROM mambaorg/micromamba:1.5.10-jammy

USER root
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    build-essential \
    libgtk-3-dev \
    python3-tk \
    gcc-arm-none-eabi \
    ngspice \
    libngspice0 \
    libngspice0-dev \
    ca-certificates \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

USER $MAMBA_USER

ARG MAMBA_DOCKERFILE_ACTIVATE=1  # активирует base для установки

RUN micromamba install -y -n base \
    -c pytorch -c conda-forge \
    python=3.11 numpy scipy pandas matplotlib sympy networkx pytorch torchvision torchaudio cpuonly \
    && pip install pyspice \
    && micromamba clean -a -y

# ==============================
# Фикс кэша Matplotlib и других библиотек
# ==============================
ENV MPLCONFIGDIR=/tmp/matplotlib \
    XDG_CACHE_HOME=/tmp \
    XDG_CONFIG_HOME=/tmp

# Создаём эти директории (на всякий случай)
RUN mkdir -p /tmp/matplotlib /tmp

# ==============================
# Рабочая директория
# ==============================
WORKDIR /workspace

# ==============================
# Официальный entrypoint + интерактивный bash
# ==============================
ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]
CMD ["bash", "-i"]
