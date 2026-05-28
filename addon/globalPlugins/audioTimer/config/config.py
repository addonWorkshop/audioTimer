import json
from copy import deepcopy
from pathlib import Path

from .migrations import migrations

INITIAL_CONFIG = {
    "schema_version": 2,
    "next_timer_id": 1,
    "timers": [],
    "ignored_keys": [],
}


def load_config(config_path: Path):
    if config_path.is_file():
        with config_path.open("rb") as f:
            raw_config = json.load(f)
        return handle_raw_config(config_path, raw_config)
    else:
        return deepcopy(INITIAL_CONFIG)


def handle_raw_config(config_path: Path, config: dict):
    if config["schema_version"] > INITIAL_CONFIG["schema_version"]:
        raise ValueError(
            "Unsupported schema version, current schema version "
            f"({config['schema_version']}) is unknown"
        )
    if config["schema_version"] < INITIAL_CONFIG["schema_version"]:
        for i in range(config["schema_version"], INITIAL_CONFIG["schema_version"]):
            migrations[i](config)
        config["schema_version"] = INITIAL_CONFIG["schema_version"]
        save_config(config_path, config)
    return config


def save_config(config_path: Path, config: dict):
    data = json.dumps(config, indent=2, ensure_ascii=False).encode()
    config_path.write_bytes(data)
