# Deployment

Status: Not deployed yet (template).

- Planned URL: `https://neojustin.dothost.net/p/fandom-gui-scraper/`
- Planned docker-compose service name: `fandom-gui-scraper`
- Planned server checkout path: `/home/neojustin/justin-portfolio/projects/fandom-gui-scraper`

## Deploy (when dockerized)
1) Add Docker config to this repo (committed):
- `docker/Dockerfile`
- `docker/nginx.conf` (for SPA/static apps)
- `.dockerignore` (exclude `node_modules/`, `dist/`, etc.)

2) Add the service to the portfolio server compose file:
- Remote: `/home/neojustin/justin-portfolio/docker-compose.yml`

3) Build + start on the server:
```bash
cd /home/neojustin/justin-portfolio
docker-compose up -d --build fandom-gui-scraper
```

## Update after code changes (once deployed)
```bash
cd /home/neojustin/justin-portfolio
docker-compose up -d --build fandom-gui-scraper
```

Reference workflow:
- `/home/justin/web-projects/justin-portfolio/docs/deployment/update-workflow.md`

