"""時鐘與時間查詢工具模組 / Clock and Timezone Query Tool Module.

[正體中文]
本模組提供即時時間查詢工具：
在自然語言處理中，大型語言模型本身並無物理時鐘感知能力，無法得知當前確切時間。
透過此工具，AI 可以向系統取得指定 IANA 時區（如 `Asia/Taipei`、`America/New_York` 或 `UTC`）的當前精確時間。

[English]
This module provides the real-time clock lookup tool:
Large language models do not possess an internal real-time clock.
This tool enables the AI agent to query the system for the exact current time
in any specified IANA timezone (e.g. `Asia/Taipei`, `America/New_York`, or `UTC`).
"""

from datetime import datetime
from zoneinfo import ZoneInfo


def current_time(time_zone: str = "UTC") -> str:
    """取得指定 IANA 時區之當前時間 / Get the current time in the requested IANA timezone.

    [正體中文]
    參數說明：
    - `time_zone`: IANA 標準時區字串（預設為 "UTC"，例如 "Asia/Taipei"、"Europe/London"）。

    回傳說明：
    - 回傳格式化後的 ISO 8601 時間字串以及時區標記。
    - 若傳入無效時區字串，將自動退避為 "UTC" 時區以保證穩定性。

    [English]
    Parameters:
    - `time_zone`: IANA standard timezone string (default "UTC", e.g. "Asia/Taipei").

    Returns:
    - Formatted ISO 8601 timestamp with the timezone tag.
    - Gracefully falls back to "UTC" if an invalid timezone identifier is supplied.
    """
    try:
        # [正體中文] 嘗試以指定的 IANA 時區建立時間物件
        # [English] Attempt to resolve the requested IANA timezone
        now = datetime.now(ZoneInfo(time_zone))
    except Exception:
        # [正體中文] 若時區名稱無效或找不到，退避回 UTC 時區
        # [English] Fallback to UTC if the timezone string is invalid
        now = datetime.now(ZoneInfo("UTC"))
        time_zone = "UTC"

    # [正體中文] 格式化為 ISO 秒級字串，並附加時區標籤便於模型理解
    # [English] Format as ISO 8601 with seconds precision and attach timezone identifier
    return now.isoformat(timespec="seconds") + f" ({time_zone})"
