from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any


def sha256_bytes(content: bytes) -> str:
    """
    Tạo SHA-256 từ file bytes.

    Dùng cho CV hash:
        CV bytes → cv_hash
    """

    if not isinstance(content, bytes):
        raise TypeError(
            "sha256_bytes chỉ nhận dữ liệu bytes."
        )

    return hashlib.sha256(content).hexdigest()


def sha256_text(value: str, *, encoding: str = "utf-8") -> str:
    """
    Tạo SHA-256 từ chuỗi text.
    """

    if not isinstance(value, str):
        raise TypeError(
            "sha256_text chỉ nhận dữ liệu str."
        )

    return hashlib.sha256(value.encode(encoding)).hexdigest()


def canonical_json(value: Any) -> str:
    """
    Chuyển object thành JSON ổn định.

    Hai dictionary cùng dữ liệu nhưng khác thứ tự key
    sẽ tạo cùng một chuỗi canonical JSON.
    """

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    )


def sha256_json(value: Any) -> str:
    """
    Tạo SHA-256 từ object JSON-serializable.

    Dùng cho:
    - Job snapshot fingerprint;
    - profile snapshot fingerprint;
    - analysis key payload;
    - version/config fingerprint.
    """

    return sha256_text(canonical_json(value))


def _json_default(value: Any) -> Any:
    """
    Chuyển các kiểu Python phổ biến sang dạng JSON ổn định.
    """

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, set):
        return sorted(value)

    if isinstance(value, frozenset):
        return sorted(value)

    if isinstance(value, tuple):
        return list(value)

    raise TypeError(
        "Không thể serialize object kiểu "
        f"{type(value).__name__} sang canonical JSON."
    )