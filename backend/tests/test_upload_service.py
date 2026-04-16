import io
from pathlib import Path

import pytest
from fastapi import UploadFile

from app.services.upload_service import save_upload_file


@pytest.mark.asyncio
async def test_save_upload_file_streams_to_target_directory(tmp_path: Path):
    payload = b"firetrain-upload" * 1024
    upload_file = UploadFile(
        filename="demo.webm",
        file=io.BytesIO(payload),
    )

    saved_file = await save_upload_file(upload_file, str(tmp_path))

    saved_path = Path(saved_file.file_path)
    assert saved_path.exists()
    assert saved_path.read_bytes() == payload
    assert saved_file.file_size == len(payload)
    assert saved_file.original_filename == "demo.webm"
    assert saved_file.save_duration_ms >= 0
    assert saved_path.suffix == ".webm"
