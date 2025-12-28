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
- **Manager + Admin Dashboard configuration**: configure scrapers and service settings from the Manager app or the `/admin` dashboard
- **Clean addon setup UI**: `/configure` focuses on per-addon preferences (debrid, languages, resolutions)
- **Consistent config storage**: scraper settings stay in sync between the Manager app and Admin Dashboard

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

**Note**: Scrapers are configured server-wide (Admin Dashboard or JavaStream Manager). The `/configure` page is for addon preferences; `.env` is still supported for advanced/self-hosted setups.

## Zero-setup (Linux)
1. Download the JavaStream Manager `.deb`, `.tar.gz`, or `.AppImage`.
2. Launch **JavaStream Manager**.
3. On first launch it will ask for this machine's **static LAN IP** (use **Auto-detect** if you're not sure), then open `http://<LAN-IP>:8000/configure`.
4. Use **Open Admin Dashboard** in the Manager app (or visit `http://<LAN-IP>:8000/admin`) to manage scrapers and service settings.

### Notes for other devices
- For devices on the same LAN, open `http://<LAN-IP>:8000/configure` on that device and install from there.
- If you are using **Stremio Web** in a browser, addon install over plain `http://<LAN-IP>` may fail (browsers block mixed-content). Use a native Stremio app or put JavaStream behind HTTPS (reverse proxy / tunnel).

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

## Building packages
This repo includes a build script that outputs `.deb`, `.tar.gz`, and `.AppImage` bundles:

```sh
bash scripts/build_javastream_manager.sh
```

Artifacts are written to `build/` (the script prints the exact filenames when it finishes).

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
