"""Save and load chat history as a small JSON file on this computer."""
import json
import os
import time
import uuid
from pathlib import Path

import pandas as pd

HISTORY_FILE = Path("data/chat_history.json")
MAX_ROWS_STORED = 200     # rows of each result kept in history
MAX_CHATS = 50            # oldest chats are dropped beyond this


def new_chat() -> dict:
    return {"id": uuid.uuid4().hex[:8], "title": "New chat",
            "created": time.time(), "messages": []}


def make_title(question: str) -> str:
    q = " ".join(question.split())
    return q if len(q) <= 40 else q[:37] + "..."


def pack_result(r: dict) -> dict:
    """Turn the dict returned by ask() into something JSON can store."""
    msg = {"role": "assistant", "status": r["status"], "sql": r.get("sql", ""),
           "error": r.get("error", ""), "retries": r.get("retries", 0),
           "columns": [], "rows": [], "total_rows": 0, "feedback": None}
    df = r.get("df")
    if df is not None:
        part = json.loads(df.head(MAX_ROWS_STORED).to_json(orient="split"))
        msg["columns"], msg["rows"] = part["columns"], part["data"]
        msg["total_rows"] = len(df)
    return msg


def unpack_df(msg: dict) -> pd.DataFrame:
    return pd.DataFrame(msg["rows"], columns=msg["columns"])


def load_chats() -> dict:
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return {c["id"]: c for c in data if c.get("messages")}
    except Exception:
        return {}


def save_chats(chats: dict) -> bool:
    keep = [c for c in chats.values() if c["messages"]]
    keep = sorted(keep, key=lambda c: c["created"], reverse=True)[:MAX_CHATS]
    try:
        tmp = HISTORY_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(keep), encoding="utf-8")
        os.replace(tmp, HISTORY_FILE)
        return True
    except Exception:
        return False