<h1 align="center" id="title">☄️ Comet Enhanced - A Fork of Comet with Enhanced Features</h1>
<p align="center"><img src="https://socialify.git.ci/g0ldyy/comet/image?description=1&font=Inter&forks=1&language=1&name=1&owner=1&pattern=Solid&stargazers=1&theme=Dark" /></p>

# About Comet Enhanced
Comet Enhanced is a fork of the original [Comet](https://github.com/g0ldyy/comet) Stremio addon with enhanced features and improvements. While maintaining all the powerful features of the original Comet, this fork adds user-friendly enhancements to make configuration easier and more flexible.

## Enhanced Features
- **🎯 Web UI-Only Configuration**: Configure scrapers directly from the web setup interface without modifying .env files
- **✨ Simplified Setup**: Select and enable scrapers with just a few clicks - no command-line or file editing required
- **🔧 Flexible Configuration**: Web UI selections override .env settings for maximum flexibility

## Original Comet Features
- The first Stremio addon to Proxy Debrid Streams to allow use of the Debrid Service on multiple IPs at the same time on the same account!
- IP-Based Max Connection Limit
- Administration Dashboard with Bandwidth Manager, Metrics and more...
- Supported Scrapers: Jackett, Prowlarr, Torrentio, Zilean, MediaFusion, Debridio, StremThru, AIOStreams, Comet, Jackettio, TorBox and Nyaa
- Caching system ft. SQLite / PostgreSQL
- Blazing Fast Background Scraper
- Smart Torrent Ranking powered by [RTN](https://github.com/dreulavelle/rank-torrent-name)
- Proxy support to bypass debrid restrictions
- Real-Debrid, All-Debrid, Premiumize, TorBox, Debrid-Link, Debrider, EasyDebrid, OffCloud and PikPak supported
- Direct Torrent supported
- [Kitsu](https://kitsu.io/) support (anime)
- Adult Content Filter

# Installation
To customize your Comet Enhanced experience to suit your needs, please take a look at all the [environment variables](https://github.com/g0ldyy/comet/blob/main/.env-sample)!

**Note**: With Comet Enhanced, you can now configure scrapers entirely through the web UI during addon installation. You only need to set up .env files if you want to use advanced features or override web UI settings.

## Self Hosted
### From source
- Clone the repository and enter the folder
    ```sh
    git clone https://github.com/tnewman-afk/comettests
    cd comettests
    ```
- Install dependencies
    ```sh
    pip install uv
    uv sync
    ````
- Start Comet Enhanced
    ```sh
    uv run python -m comet.main
    ````

### With Docker Compose
- Copy *deployment/docker-compose.yml* in a directory
- Copy *.env-sample* to *.env* in the same directory and keep only the variables you wish to modify, also remove all comments
- Pull the latest version from docker hub
    ```sh
      docker compose pull
    ```
- Run
    ```sh
      docker compose up -d
    ```

### Nginx Reverse Proxy
If you want to serve Comet Enhanced via a Nginx Reverse Proxy, here's the configuration you should use.
```
server {
    server_name example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Credits
This project is a fork of the original [Comet](https://github.com/g0ldyy/comet) by [g0ldyy](https://github.com/g0ldyy). All credit for the core functionality goes to the original developers.

## Support the Original Project
If you find Comet Enhanced useful, please consider supporting the original Comet project:
- ❤️ **Donate** via [GitHub Sponsors](https://github.com/sponsors/g0ldyy) or [Ko-fi](https://ko-fi.com/g0ldyy)
- ⭐ **Star the original repository** at [g0ldyy/comet](https://github.com/g0ldyy/comet)
- ⭐ **Star the addon** on [stremio-addons.net](https://stremio-addons.net/addons/comet)

## Web UI Showcase
<img src="https://i.imgur.com/7xY5AEi.png" />
<img src="https://i.imgur.com/Dzs4wax.png" />
<img src="https://i.imgur.com/L3RkfO8.jpeg" />
