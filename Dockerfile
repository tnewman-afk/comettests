FROM ghcr.io/astral-sh/uv:python3.11-alpine
LABEL name="JavaStream" \
      description="JavaStream is a fast torrent/debrid search add-on for Stremio." \
      url="https://github.com/tnewman-afk/comettests"

RUN apk add --no-cache gcc python3-dev musl-dev linux-headers

WORKDIR /app

ARG DATABASE_PATH

COPY pyproject.toml .

RUN uv sync

COPY . .

ENTRYPOINT ["uv", "run", "python", "-m", "comet.main"]
