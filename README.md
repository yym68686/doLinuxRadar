# doLinuxRadar

## Docker Local Deployment

Start the container

```bash
docker run -p 8010:8080 --name dolinuxradar -dit \
    -e BOT_TOKEN=your_telegram_bot_token \
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
yym68686/dolinuxradar:latest
docker logs -f dolinuxradar
```