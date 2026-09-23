"""Download Laya checkpoints into a local models folder.

Usage:
    # 榛樿锛氫粠 Hugging Face 涓嬭浇
    python download_models.py
    python download_models.py --hf-endpoint https://hf-mirror.com
    python download_models.py --only laya-multilingual

    # 浠?GitHub Releases 涓嬭浇 zip锛堜綋绉ぇ鏃舵帹鑽愮粰鐢ㄦ埛锛?    python download_models.py --from-release --repo ljw98/Laya --tag v1.0.0
    python download_models.py --from-release --repo ljw98/Laya --tag v1.0.0 --only laya

Layout written (default MODEL_DIR=./laya-main/models):
    laya/
    laya-multilingual/
    laya-typed-decisions/
"""
from __future__ import annotations

import argparse
import os
import tempfile
import urllib.request
import zipfile
from pathlib import Path

BUNDLE_REPO = os.environ.get("LAYA_HF_REPO", "convaiinnovations/laya")
# 鏈湴鐩綍鍚?-> HF 鍚堝苟浠撳簱涓殑瀛愮洰褰曪紙None = 鏍圭洰褰曪級
SUBFOLDERS = {
    "laya": None,
    "laya-multilingual": "multilingual",
    "laya-typed-decisions": "typed-decisions",
}
REQUIRED_FILES = (
    "rl_agent_config.json",
    "model.safetensors",
    "tokenizer/tokenizer.json",
    "tokenizer/tokenizer_config.json",
    "encoder/config.json",
)


def is_complete(path: Path) -> bool:
    return all((path / r).is_file() and (path / r).stat().st_size > 0 for r in REQUIRED_FILES)


def download_one_hf(name: str, subfolder: str | None, dest: Path) -> None:
    from huggingface_hub import hf_hub_download

    out_dir = dest / name
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{subfolder}/" if subfolder else ""
    for rel in REQUIRED_FILES:
        target = out_dir / rel
        if target.is_file() and target.stat().st_size > 0:
            print(f"  skip  {name}/{rel}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        print(f"  get   {name}/{rel}")
        hf_hub_download(
            repo_id=BUNDLE_REPO,
            filename=prefix + rel,
            local_dir=str(out_dir),
            local_dir_use_symlinks=False,
        )
        nested = out_dir / (prefix + rel)
        if nested != target and nested.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                target.unlink()
            nested.replace(target)
        if prefix:
            p = out_dir / subfolder
            if p.is_dir() and not any(p.iterdir()):
                p.rmdir()
    print(f"  done  {name}  {'OK' if is_complete(out_dir) else 'INCOMPLETE'}")


def download_one_release(name: str, dest: Path, repo: str, tag: str) -> None:
    """涓嬭浇 GitHub Release 璧勪骇 <name>.zip 骞惰В鍘嬪埌 dest/<name>/銆?""
    out_dir = dest / name
    if is_complete(out_dir):
        print(f"  skip  {name} (already complete)")
        return

    url = f"https://github.com/{repo}/releases/download/{tag}/{name}.zip"
    print(f"  get   {url}")
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        tmp_path = Path(tmp.name)
    try:
        urllib.request.urlretrieve(url, tmp_path)
        print(f"  unzip {name}.zip -> {out_dir}")
        with zipfile.ZipFile(tmp_path, "r") as zf:
            zf.extractall(out_dir)
        # 鑻?zip 鍐呭張濂椾簡涓€灞?<name>/锛屼笂绉讳竴灞?        nested = out_dir / name
        if nested.is_dir() and (nested / "rl_agent_config.json").exists():
            for child in nested.iterdir():
                target = out_dir / child.name
                if not target.exists():
                    child.replace(target)
            nested.rmdir()
        print(f"  done  {name}  {'OK' if is_complete(out_dir) else 'INCOMPLETE'}")
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Laya model checkpoints")
    parser.add_argument(
        "--model-dir",
        default=os.environ.get("MODEL_DIR")
        or str(Path(__file__).resolve().parent / "laya-main" / "models"),
        help="where to put checkpoints (default: ./laya-main/models)",
    )
    parser.add_argument(
        "--hf-endpoint",
        default=os.environ.get("HF_ENDPOINT") or None,
        help="Hugging Face endpoint when using HF source, e.g. https://hf-mirror.com",
    )
    parser.add_argument(
        "--only",
        choices=sorted(SUBFOLDERS),
        help="download a single checkpoint",
    )
    parser.add_argument(
        "--from-release",
        action="store_true",
        help="download zip assets from GitHub Releases instead of Hugging Face",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("LAYA_RELEASE_REPO", "ljw98/Laya"),
        help="GitHub repo for releases, e.g. ljw98/Laya",
    )
    parser.add_argument(
        "--tag",
        default=os.environ.get("LAYA_RELEASE_TAG", "v1.0.0"),
        help="release tag (default: v1.0.0)",
    )
    args = parser.parse_args()

    dest = Path(args.model_dir)
    dest.mkdir(parents=True, exist_ok=True)
    names = [args.only] if args.only else list(SUBFOLDERS)

    if args.from_release:
        if not args.repo:
            parser.error("--from-release 闇€瑕?--repo owner/name")
        print(f"source: GitHub Releases {args.repo} tag={args.tag}")
        print(f"model dir: {dest}")
        for name in names:
            download_one_release(name, dest, args.repo, args.tag)
    else:
        if args.hf_endpoint:
            os.environ["HF_ENDPOINT"] = args.hf_endpoint
            print(f"HF_ENDPOINT={args.hf_endpoint}")
        else:
            print("HF_ENDPOINT=(default huggingface.co)")
        print(f"source: Hugging Face {BUNDLE_REPO}")
        print(f"model dir: {dest}")
        for name in names:
            download_one_hf(name, SUBFOLDERS[name], dest)
    print("ALL DONE")


if __name__ == "__main__":
    main()

