<h1 align="center" id="title">JavaStream</h1>

# About JavaStream
JavaStream is a Linux-first fork of the original [Comet](https://github.com/g0ldyy/comet) Stremio addon. It focuses on a zero-setup experience with a manager app that starts the server for you, opens the web dashboard on first launch, and keeps everything running in the background.

JavaStream is a fork of Comet with better ease of use. It is designed for Linux and targets a zero-setup flow (download the `.deb`, open the app, and the addon is running with no command line required).

## JavaStream Manager
- One-click start/stop/restart for the JavaStream server
- Optional auto-start on login (systemd user service)
- First launch opens the configuration dashboard automatically
- Distributed as `.deb`, `.tar.gz`, and `.AppImage`

## Enhanced Features
- **Web UI-only configuration**: configure scrapers directly from the setup interface without editing `.env` files
- **Simplified setup**: select and enable scrapers with a few clicks
- **Flexible configuration**: web UI selections override `.env` settings

## Original Comet Features
- Proxy debrid streams for multi-IP usage
- IP-based max connection limit
- Administration dashboard with bandwidth manager, metrics, and more
- Supported scrapers: Jackett, Prowlarr, Torrentio, Zilean, MediaFusion, Debridio, StremThru, AIOStreams, Comet, Jackettio, TorBox, and Nyaa
- Caching system (SQLite/PostgreSQL)
- Fast background scraper
- Smart torrent ranking powered by [RTN](https://github.com/dreulavelle/rank-torrent-name)
- Proxy support to bypass debrid restrictions
- Real-Debrid, All-Debrid, Premiumize, TorBox, Debrid-Link, Debrider, EasyDebrid, OffCloud, and PikPak supported
- Direct torrent support
- [Kitsu](https://kitsu.io/) support (anime)
- Adult content filter

# Installation
To customize your JavaStream experience, see the environment variables in `.env-sample`.

**Note**: JavaStream lets you configure scrapers entirely through the web UI during addon installation. You only need `.env` files for advanced overrides.

## Zero-setup (Linux)
1. Download the JavaStream Manager `.deb`, `.tar.gz`, or `.AppImage`.
2. Launch **JavaStream Manager**.
3. It will start the server and open `http://127.0.0.1:8000/configure` on first launch.

## Self-hosted (from source)
- Clone the repository and enter the folder
    ```sh
    git clone https://github.com/tnewman-afk/comettests
    cd comettests
    ```
- Install dependencies
    ```sh
    pip install uv
    uv sync
    ```
- Start JavaStream
    ```sh
    uv run python -m comet.main
    ```

### With Docker Compose
- Copy `deployment/docker-compose.yml` into a directory
- Copy `.env-sample` to `.env` in the same directory and keep only the variables you wish to modify (remove comments)
- Build and run
    ```sh
    docker compose up -d --build
    ```

### Nginx Reverse Proxy
If you want to serve JavaStream via a Nginx reverse proxy, use:
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
JavaStream is a fork of the original [Comet](https://github.com/g0ldyy/comet) by [g0ldyy](https://github.com/g0ldyy). All credit for the core functionality goes to the original developers.

## Support the Original Project
If you find JavaStream useful, please consider supporting the original Comet project:
- ❤️ **Donate** via [GitHub Sponsors](https://github.com/sponsors/g0ldyy) or [Ko-fi](https://ko-fi.com/g0ldyy)
- ⭐ **Star the original repository** at [g0ldyy/comet](https://github.com/g0ldyy/comet)
- ⭐ **Star the addon** on [stremio-addons.net](https://stremio-addons.net/addons/comet)
