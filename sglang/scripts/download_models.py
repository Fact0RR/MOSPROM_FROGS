import argparse
import os
from pathlib import Path

import yaml
from huggingface_hub import hf_hub_download


def download_model(model_cfg, target_root: Path, token: str | None):
    repo_id = model_cfg["hf_repo"]
    filename = model_cfg["filename"]
    model_name = model_cfg["name"]

    destination = target_root / model_name
    destination.mkdir(parents=True, exist_ok=True)

    download_kwargs = {
        "repo_id": repo_id,
        "filename": filename,
        "local_dir": str(destination),
        "local_dir_use_symlinks": False,
    }
    if token:
        download_kwargs["token"] = token

    print(f"Downloading {filename} from {repo_id} into {destination}")
    hf_hub_download(**download_kwargs)


def parse_args():
    parser = argparse.ArgumentParser(description="Download model artifacts declared in models.yaml")
    parser.add_argument("--config", default="/app/config/models.yaml", help="Path to the models configuration YAML")
    parser.add_argument("--models-dir", default="/models", help="Directory to store downloaded model weights")
    parser.add_argument("--token", default=None, help="Optional Hugging Face access token")
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    models = cfg.get("models", [])
    target_root = Path(args.models_dir)
    target_root.mkdir(parents=True, exist_ok=True)

    for model_cfg in models:
        download_model(model_cfg, target_root, args.token)


if __name__ == "__main__":
    main()
