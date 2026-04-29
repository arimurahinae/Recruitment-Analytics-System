FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1. 替换 Debian 软件源为阿里云镜像（针对 Debian Trixie/13 版本）
# 这一步能解决你刚才遇到的 502 Bad Gateway 报错
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 2. 安装 mysqlclient 编译依赖
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential pkg-config default-libmysqlclient-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

# 3. 建议：pip 也使用国内镜像，防止下载 requirements.txt 时卡住
RUN pip install --no-cache-dir -r /app/requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/

COPY . /app

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]