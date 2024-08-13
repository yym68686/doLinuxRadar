# doLinuxRadar

<!-- [![Build Status](https://travis-ci.com/yym68686/doLinuxRadar.svg?branch=main)](https://travis-ci.com/yym68686/doLinuxRadar) -->
[![Docker Pulls](https://img.shields.io/docker/pulls/yym68686/dolinuxradar)](https://hub.docker.com/r/yym68686/dolinuxradar)
[![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/yym68686/dolinuxradar)](https://hub.docker.com/r/yym68686/dolinuxradar)
[![Docker Image Version (latest by date)](https://img.shields.io/docker/v/yym68686/dolinuxradar)](https://hub.docker.com/r/yym68686/dolinuxradar)

<p align="center">
  <a href="https://t.me/+CKIMSpHhO2E5ZTc1">
    <img src="https://img.shields.io/badge/加入 Telegram 群-blue?&logo=telegram">
  </a>
</p>

doLinuxRadar 专门嗅探 linux.do 你感兴趣的话题。机器人使用地址：[@doLinuxRadar](https://t.me/doLinuxRadar)

## 使用指南

命令列表：

- `/tags`: 设置监控关键词（空格隔开）, 例如: `/tags 免费 linux`
- `/set`: 设置嗅探间隔(秒), 例如: `/set 60`
- `/unset`: 取消或者打开消息推送, 例如: `/unset`
- `/start`: linux.do 风向标使用简介, 例如: `/start`

## Docker Local Deployment

Start the container

```bash
docker run -p 8010:8080 --name dolinuxradar -dit \
    -e BOT_TOKEN=your_telegram_bot_token \
    -e ADMIN_LIST=your_telegram_id \
    -v ./user_configs:/app/user_configs \
    yym68686/dolinuxradar:latest
```

Package the Docker image in the repository and upload it to Docker Hub

```bash
docker build --no-cache -t dolinuxradar:latest -f Dockerfile.build --platform linux/amd64 .
docker tag dolinuxradar:latest yym68686/dolinuxradar:latest
docker push yym68686/dolinuxradar:latest
```

One-Click Restart Docker Image

```bash
set -eu
docker pull yym68686/dolinuxradar:latest
docker rm -f dolinuxradar
docker run -p 8010:8080 -dit --name dolinuxradar \
-e BOT_TOKEN= \
-e ADMIN_LIST=your_telegram_id \
-v ./user_configs:/app/user_configs \
yym68686/dolinuxradar:latest
docker logs -f dolinuxradar
```