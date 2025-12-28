import base64
import binascii

import orjson

from comet.core.models import (ConfigModel, default_config,
                               rtn_ranking_default, rtn_settings_default,
                               settings)


def _decode_config_payload(b64config: str) -> dict:
    text = (b64config or "").strip()
    if not text:
        raise ValueError("Empty config")

    normalized = text.replace("-", "+").replace("_", "/")
    padding = "=" * (-len(normalized) % 4)
    try:
        raw = base64.b64decode(normalized + padding)
    except binascii.Error:
        raw = base64.urlsafe_b64decode(text + ("=" * (-len(text) % 4)))
    return orjson.loads(raw.decode())


def config_check(b64config: str):
    try:
        config = _decode_config_payload(b64config)

        validated_config = ConfigModel(**config)
        validated_config = validated_config.model_dump()

        for key in list(validated_config["options"].keys()):
            if key not in [
                "remove_ranks_under",
                "allow_english_in_languages",
                "remove_unknown_languages",
            ]:
                validated_config["options"].pop(key)

        validated_config["options"]["remove_all_trash"] = validated_config[
            "removeTrash"
        ]

        rtn_settings = rtn_settings_default.model_copy(
            update={
                "resolutions": rtn_settings_default.resolutions.model_copy(
                    update=validated_config["resolutions"]
                ),
                "options": rtn_settings_default.options.model_copy(
                    update=validated_config["options"]
                ),
                "languages": rtn_settings_default.languages.model_copy(
                    update=validated_config["languages"]
                ),
            }
        )

        validated_config["rtnSettings"] = rtn_settings
        validated_config["rtnRanking"] = rtn_ranking_default

        if (
            settings.PROXY_DEBRID_STREAM
            and settings.PROXY_DEBRID_STREAM_PASSWORD
            == validated_config["debridStreamProxyPassword"]
            and validated_config["debridApiKey"] == ""
        ):
            validated_config["debridService"] = (
                settings.PROXY_DEBRID_STREAM_DEBRID_DEFAULT_SERVICE
            )
            validated_config["debridApiKey"] = (
                settings.PROXY_DEBRID_STREAM_DEBRID_DEFAULT_APIKEY
            )

        return validated_config
    except Exception:
        return default_config  # if it doesn't pass, return default config
