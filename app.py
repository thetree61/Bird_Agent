from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from openai.lib._pydantic import to_strict_json_schema
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
INDEX_PATH = ROOT / "index.html"
DIARY_PATH = ROOT / "diary.json"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "modelscope").lower()
MODELSCOPE_BASE_URL = os.getenv("MODELSCOPE_BASE_URL", "https://api-inference.modelscope.cn/v1")
MODELSCOPE_MODEL = os.getenv("MODELSCOPE_MODEL", "Qwen/Qwen3-32B")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """
你是“林间魔法占卜师”，一个森系、温柔、略带手绘涂鸦气质的鸟类智能体。
你会用中文回答。需要鸟类真实资料、鸟鸣、写入或读取观鸟日记时，必须使用工具。
当用户请求“占卜”时，选择一种合适的鸟，调用鸟鸣工具，然后根据鸟的习性写一段治愈系趣味占卜。
回答要温暖、有画面感，但不要编造工具能查到的事实。
"""

BIRD_NAME_EN = {
    "\u5e03\u8c37\u9e1f": "common cuckoo",
    "\u675c\u9e43": "common cuckoo",
    "\u559c\u9e4a": "eurasian magpie",
    "\u9ebb\u96c0": "eurasian tree sparrow",
    "\u4e4c\u9e26": "carrion crow",
    "\u767d\u9e6d": "little egret",
    "\u7fe0\u9e1f": "common kingfisher",
    "\u71d5\u5b50": "barn swallow",
    "\u591c\u83ba": "common nightingale",
    "\u753b\u7709": "chinese hwamei",
}

app = FastAPI(title="Forest Doodle Bird Agent")


class DiaryEntryIn(BaseModel):
    bird_name: str = Field(..., min_length=1)
    spot_time: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class DiaryEntry(DiaryEntryIn):
    id: str
    created_at: str


class GetBirdWikiArgs(BaseModel):
    bird_name: str = Field(
        ...,
        description="\u4e2d\u6587\u9e1f\u540d\uff0c\u4f8b\u5982\uff1a\u5e03\u8c37\u9e1f\u3001\u559c\u9e4a\u3001\u767d\u9e6d",
    )


class GetBirdSoundArgs(BaseModel):
    bird_name_en: str = Field(..., description="English common bird name, for example: common cuckoo")


class WriteBirdDiaryArgs(DiaryEntryIn):
    pass


class ReadBirdDiariesArgs(BaseModel):
    pass


def pydantic_tool(name: str, description: str, model: type[BaseModel]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": to_strict_json_schema(model),
            "strict": True,
        },
    }


TOOLS = [
    pydantic_tool("get_bird_wiki", "查询中文维基百科鸟类资料和图片。", GetBirdWikiArgs),
    pydantic_tool("get_bird_sound", "查询 Xeno-canto 鸟鸣录音 MP3 链接。", GetBirdSoundArgs),
    pydantic_tool("write_bird_diary", "保存一条观鸟日记到本地 JSON。", WriteBirdDiaryArgs),
    pydantic_tool("read_bird_diaries", "读取本地所有观鸟日记。", ReadBirdDiariesArgs),
]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)


def ensure_diary_file() -> None:
    if not DIARY_PATH.exists():
        DIARY_PATH.write_text("[]", encoding="utf-8")


def read_diary_entries() -> list[dict[str, Any]]:
    ensure_diary_file()
    try:
        data = json.loads(DIARY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def load_diary_entries_for_write() -> list[dict[str, Any]]:
    ensure_diary_file()
    raw_diary = DIARY_PATH.read_text(encoding="utf-8")
    try:
        data = json.loads(raw_diary)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, list):
        return data

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    backup_path = DIARY_PATH.with_name(f"{DIARY_PATH.stem}.corrupt-{stamp}-{uuid.uuid4().hex[:8]}{DIARY_PATH.suffix}")
    backup_path.write_text(raw_diary, encoding="utf-8")
    return []


def write_diary_entry(entry: DiaryEntryIn) -> dict[str, Any]:
    entries = load_diary_entries_for_write()
    saved = DiaryEntry(
        id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        **entry.model_dump(),
    ).model_dump()
    entries.append(saved)
    DIARY_PATH.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return saved


def llm_config() -> dict[str, str | None]:
    if LLM_PROVIDER == "openai":
        return {
            "provider": "openai",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": None,
            "model": OPENAI_MODEL,
        }
    return {
        "provider": "modelscope",
        "api_key": os.getenv("MODELSCOPE_API_KEY"),
        "base_url": MODELSCOPE_BASE_URL,
        "model": MODELSCOPE_MODEL,
    }


async def get_bird_wiki(bird_name: str) -> dict[str, Any]:
    url = "https://zh.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|pageimages",
        "exintro": 1,
        "explaintext": 1,
        "piprop": "original",
        "redirects": 1,
        "titles": bird_name,
    }
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            pages = response.json().get("query", {}).get("pages", {})
    except Exception as exc:
        return {"ok": False, "bird_name": bird_name, "message": f"\u6ca1\u6709\u67e5\u5230\u767e\u79d1\u8d44\u6599\uff1a{exc}"}

    if not isinstance(pages, dict) or not pages:
        return {"ok": False, "bird_name": bird_name, "message": "\u4e2d\u6587\u7ef4\u57fa\u767e\u79d1\u6682\u65f6\u6ca1\u6709\u627e\u5230\u8fd9\u53ea\u9e1f\u3002"}

    page = next(iter(pages.values()), {})
    if not isinstance(page, dict) or not page:
        return {"ok": False, "bird_name": bird_name, "message": "\u4e2d\u6587\u7ef4\u57fa\u767e\u79d1\u6682\u65f6\u6ca1\u6709\u627e\u5230\u8fd9\u53ea\u9e1f\u3002"}

    if "missing" in page:
        return {"ok": False, "bird_name": bird_name, "message": "\u4e2d\u6587\u7ef4\u57fa\u767e\u79d1\u6682\u65f6\u6ca1\u6709\u627e\u5230\u8fd9\u53ea\u9e1f\u3002"}

    page_id = page.get("pageid")
    return {
        "ok": True,
        "bird_name": bird_name,
        "title": page.get("title", bird_name),
        "summary": page.get("extract", "\u8fd8\u6ca1\u6709\u6458\u8981\u3002"),
        "image_url": page.get("original", {}).get("source"),
        "source_url": f"https://zh.wikipedia.org/?curid={page_id}" if page_id else None,
    }


async def get_bird_sound(bird_name_en: str) -> dict[str, Any]:
    query_name = BIRD_NAME_EN.get(bird_name_en, bird_name_en)
    url = "https://xeno-canto.org/api/2/recordings"
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(url, params={"query": query_name})
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        return {"ok": False, "bird_name_en": bird_name_en, "message": f"\u6ca1\u6709\u542c\u89c1\u9e1f\u9e23\uff1a{exc}"}

    recordings = payload.get("recordings") or []
    if not recordings:
        return {"ok": False, "bird_name_en": bird_name_en, "message": "Xeno-canto \u6682\u65f6\u6ca1\u6709\u627e\u5230\u8fd9\u53ea\u9e1f\u7684\u5f55\u97f3\u3002"}

    recording = recordings[0]
    file_url = recording.get("file", "")
    if file_url.startswith("//"):
        file_url = f"https:{file_url}"
    source_url = recording.get("url")
    if source_url and source_url.startswith("//"):
        source_url = f"https:{source_url}"

    return {
        "ok": True,
        "bird_name_en": bird_name_en,
        "common_name": recording.get("en"),
        "scientific_name": recording.get("gen", "") + " " + recording.get("sp", ""),
        "country": recording.get("cnt"),
        "recordist": recording.get("rec"),
        "license": recording.get("lic"),
        "audio_url": file_url,
        "source_url": source_url,
    }


async def write_bird_diary(bird_name: str, spot_time: str, location: str, description: str) -> dict[str, Any]:
    saved = write_diary_entry(
        DiaryEntryIn(
            bird_name=bird_name,
            spot_time=spot_time,
            location=location,
            description=description,
        )
    )
    return {"ok": True, "entry": saved, "diaries": read_diary_entries()}


async def read_bird_diaries() -> dict[str, Any]:
    return {"ok": True, "diaries": read_diary_entries()}


async def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "get_bird_wiki":
        parsed = GetBirdWikiArgs(**args)
        return await get_bird_wiki(parsed.bird_name)
    if name == "get_bird_sound":
        parsed = GetBirdSoundArgs(**args)
        return await get_bird_sound(parsed.bird_name_en)
    if name == "write_bird_diary":
        parsed = WriteBirdDiaryArgs(**args)
        return await write_bird_diary(**parsed.model_dump())
    if name == "read_bird_diaries":
        ReadBirdDiariesArgs(**args)
        return await read_bird_diaries()
    return {"ok": False, "message": f"Unknown tool: {name}"}


async def run_chat_tool_call(tool_call: Any) -> tuple[str, dict[str, Any], dict[str, Any]]:
    function = getattr(tool_call, "function", None)
    name = getattr(function, "name", "")
    raw_args = getattr(function, "arguments", None) or "{}"
    args: dict[str, Any] = {}
    try:
        loaded_args = json.loads(raw_args)
        if not isinstance(loaded_args, dict):
            raise ValueError("Tool arguments must be a JSON object.")
        args = loaded_args
        result = await call_tool(name, args)
    except Exception as exc:
        result = {"ok": False, "message": f"工具调用失败：{exc}"}
    return name, args, result


def tool_trace_label(name: str, args: dict[str, Any], result: dict[str, Any]) -> str:
    if name == "get_bird_wiki":
        return f"正在翻找 {args.get('bird_name', '这只鸟')} 的林间百科..."
    if name == "get_bird_sound":
        bird = args.get("bird_name_en", "mystery bird")
        return f"正在呼唤 {bird} 的鸟鸣..."
    if name == "write_bird_diary":
        return "正在把这次相遇写进观鸟手帐..."
    if name == "read_bird_diaries":
        return "正在翻开观鸟日记本..."
    return "林间小工具正在忙碌..."


@app.get("/")
def index() -> FileResponse:
    if not INDEX_PATH.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(INDEX_PATH)


@app.get("/api/diary")
def api_read_diary() -> dict[str, Any]:
    return {"diaries": read_diary_entries()}


@app.post("/api/diary")
def api_write_diary(entry: DiaryEntryIn) -> dict[str, Any]:
    saved = write_diary_entry(entry)
    return {"entry": saved, "diaries": read_diary_entries()}


@app.post("/api/chat")
async def api_chat(request: ChatRequest) -> dict[str, Any]:
    tool_traces: list[str] = []
    latest_bird: dict[str, Any] | None = None
    latest_sound: dict[str, Any] | None = None
    latest_diaries: list[dict[str, Any]] | None = None

    config = llm_config()
    key_name = "OPENAI_API_KEY" if config["provider"] == "openai" else "MODELSCOPE_API_KEY"

    if not config["api_key"]:
        return {
            "reply": f"还没有设置 {key_name}。林间占卜师已经坐好，但水晶球还没点亮。",
            "tool_traces": [],
            "bird": None,
            "sound": None,
            "diaries": read_diary_entries(),
        }

    client_kwargs = {"api_key": config["api_key"]}
    if config["base_url"]:
        client_kwargs["base_url"] = config["base_url"]
    client = AsyncOpenAI(**client_kwargs)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    for item in request.history[-8:]:
        if item.role in {"user", "assistant"}:
            messages.append({"role": item.role, "content": item.content})
    messages.append({"role": "user", "content": request.message})

    try:
        response = await client.chat.completions.create(
            model=config["model"],
            messages=messages,
            tools=TOOLS,
        )
    except Exception:
        return {
            "reply": "林间的水晶球刚刚起雾了，暂时没能连上星光。请稍后再试一次。",
            "tool_traces": tool_traces,
            "bird": latest_bird,
            "sound": latest_sound,
            "diaries": read_diary_entries(),
        }

    reply = "林间风声有点轻，我刚刚没听清。"
    for _ in range(3):
        message = response.choices[0].message
        tool_calls = list(message.tool_calls or [])
        if not tool_calls:
            reply = message.content or reply
            break

        messages.append(message.model_dump(exclude_none=True))
        for tool_call in tool_calls:
            tool_name, args, result = await run_chat_tool_call(tool_call)
            tool_traces.append(tool_trace_label(tool_name, args, result))
            if tool_name == "get_bird_wiki":
                latest_bird = result
            if tool_name == "get_bird_sound":
                latest_sound = result
            if tool_name in {"write_bird_diary", "read_bird_diaries"}:
                latest_diaries = result.get("diaries")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

        try:
            response = await client.chat.completions.create(model=config["model"], messages=messages, tools=TOOLS)
        except Exception:
            return {
                "reply": "林间的回声刚刚断了一下，但我已经把听见的线索收好了。请稍后再试一次。",
                "tool_traces": tool_traces,
                "bird": latest_bird,
                "sound": latest_sound,
                "diaries": latest_diaries if latest_diaries is not None else read_diary_entries(),
            }

    return {
        "reply": reply,
        "tool_traces": tool_traces,
        "bird": latest_bird,
        "sound": latest_sound,
        "diaries": latest_diaries if latest_diaries is not None else read_diary_entries(),
    }
