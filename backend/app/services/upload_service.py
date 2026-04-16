"""文件上传保存服务。"""
from __future__ import annotations

import os
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool


@dataclass
class SavedUploadFile:
    """保存后的上传文件信息。"""

    file_path: str
    file_size: int
    original_filename: str
    save_duration_ms: int


def _build_unique_filename(original_filename: str | None) -> str:
    suffix = Path(original_filename or "").suffix.lower() or ".mp4"
    return f"{uuid.uuid4()}{suffix}"


def _copy_temp_file(upload_file: UploadFile, destination_path: str, chunk_size: int) -> int:
    upload_file.file.seek(0)

    with open(destination_path, "wb") as output_file:
        shutil.copyfileobj(upload_file.file, output_file, length=chunk_size)

    return os.path.getsize(destination_path)


async def save_upload_file(
    upload_file: UploadFile,
    target_directory: str,
    *,
    filename: str | None = None,
    chunk_size: int = 1024 * 1024,
) -> SavedUploadFile:
    """将上传文件保存到目标目录，避免整文件读入内存。"""
    os.makedirs(target_directory, exist_ok=True)

    final_filename = filename or _build_unique_filename(upload_file.filename)
    destination_path = os.path.join(target_directory, final_filename)
    started_at = time.perf_counter()
    file_size = await run_in_threadpool(
        _copy_temp_file,
        upload_file,
        destination_path,
        chunk_size,
    )
    save_duration_ms = int((time.perf_counter() - started_at) * 1000)

    await upload_file.close()

    return SavedUploadFile(
        file_path=destination_path,
        file_size=file_size,
        original_filename=upload_file.filename or final_filename,
        save_duration_ms=save_duration_ms,
    )
