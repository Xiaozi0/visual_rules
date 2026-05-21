from __future__ import annotations
from huggingface_hub import HfApi, login

import os
# os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from fnmatch import fnmatch
from pathlib import Path



REPO_ID = "Yezixiao/Visual_scaling_static"
REPO_TYPE = "dataset"
LOCAL_FOLDER_PATH = Path("./datasets")
PATH_IN_REPO = "."

# 用 ** 前缀匹配任意层级，避免目录规则完全失效。
IGNORE_PATTERNS = [
    "*.DS_Store",
    "*.log",
    ".git/*",
    "__pycache__/*",
    "**/.git/*",
    "**/__pycache__/*",
    "smart/SMART101-release-v1/SMART101-Data/**",
    "VisualPuzzles/images/**",
    "VisuLogic-Train/images/**",
]


def should_ignore(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    return any(fnmatch(normalized, pattern) for pattern in IGNORE_PATTERNS)


def summarize_upload(folder: Path) -> None:
    total_files = 0
    kept_files = 0
    ignored_files = 0
    total_size = 0
    kept_size = 0

    for path in folder.rglob("*"):
        if not path.is_file():
            continue

        total_files += 1
        size = path.stat().st_size
        total_size += size

        relative_path = path.relative_to(folder).as_posix()
        if should_ignore(relative_path):
            ignored_files += 1
            continue

        kept_files += 1
        kept_size += size

    print(f"扫描目录: {folder.resolve()}")
    print(f"总文件数: {total_files}")
    print(f"忽略后文件数: {kept_files}")
    print(f"被忽略文件数: {ignored_files}")
    print(f"总大小: {total_size / (1024 ** 3):.2f} GB")
    print(f"待上传大小: {kept_size / (1024 ** 3):.2f} GB")


def main() -> None:
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("未设置 HF_TOKEN 环境变量。先执行: export HF_TOKEN=你的token")

    # if not LOCAL_FOLDER_PATH.exists():
    #     raise FileNotFoundError(f"本地目录不存在: {LOCAL_FOLDER_PATH}")
    login(token=token)

    summarize_upload(LOCAL_FOLDER_PATH)


    api = HfApi()

    print("开始上传，首次可能会先做较久的文件扫描和预检查...")
    api.upload_folder(
        folder_path=str(LOCAL_FOLDER_PATH),
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        path_in_repo=PATH_IN_REPO,
        ignore_patterns=IGNORE_PATTERNS,
    )
    print("上传完成。")


if __name__ == "__main__":
    main()
