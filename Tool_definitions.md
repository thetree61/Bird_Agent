# Forest Doodle Bird Agent - Tool Definitions

## 1. 工具总览

本项目为“森系涂鸦风鸟类智能体”实现了 4 个核心工具。大模型本身不直接访问互联网或本地文件，而是通过这些标准化工具完成真实数据查询与本地状态读写。

| Tool | 核心能力 | 外部/本地数据源 | 典型用途 |
| --- | --- | --- | --- |
| `get_bird_wiki` | 查询鸟类百科资料与图片 | 中文 Wikipedia API | 获取鸟类简介、图片、来源链接 |
| `get_bird_sound` | 查询真实鸟鸣音频 | Xeno-canto API v3，失败时可回退 Wikimedia Commons | 获取 MP3/音频 URL、录音者、国家、许可证 |
| `write_bird_diary` | 写入观鸟日记 | 本地 `diary.json` | 保存用户的观鸟记录 |
| `read_bird_diaries` | 读取观鸟日记 | 本地 `diary.json` | 展示历史观鸟记录 |

---

## 2. 工具详细定义

## 2.1 `get_bird_wiki`

### Function Name

```text
get_bird_wiki
```

### Description

查询中文维基百科鸟类资料和图片。

该工具用于获取鸟类真实百科信息，包括鸟类标题、简介、图片 URL 与来源页面。它让模型在回答“这是什么鸟”“介绍一下某种鸟”“每日一鸟”等问题时，可以基于外部真实数据，而不是凭空编造。

### Parameters & Types

Pydantic 模型：`GetBirdWikiArgs`

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `bird_name` | `str` | yes | 中文鸟名，例如：`布谷鸟`、`喜鹊`、`白鹭` |

### Tool Definition JSON Schema

```json
{
  "type": "function",
  "function": {
    "name": "get_bird_wiki",
    "description": "查询中文维基百科鸟类资料和图片。",
    "parameters": {
      "properties": {
        "bird_name": {
          "description": "中文鸟名，例如：布谷鸟、喜鹊、白鹭",
          "title": "Bird Name",
          "type": "string"
        }
      },
      "required": ["bird_name"],
      "title": "GetBirdWikiArgs",
      "type": "object",
      "additionalProperties": false
    },
    "strict": true
  }
}
```

### Model Tool Call Example

```json
{
  "id": "call_wiki_001",
  "type": "function",
  "function": {
    "name": "get_bird_wiki",
    "arguments": "{\"bird_name\":\"白鹭\"}"
  }
}
```

### Returns

成功时：

```json
{
  "ok": true,
  "bird_name": "白鹭",
  "title": "白鹭",
  "summary": "百科摘要文本",
  "image_url": "https://...",
  "source_url": "https://zh.wikipedia.org/?curid=..."
}
```

失败时：

```json
{
  "ok": false,
  "bird_name": "未知鸟名",
  "message": "中文维基百科暂时没有找到这只鸟。"
}
```

---

## 2.2 `get_bird_sound`

### Function Name

```text
get_bird_sound
```

### Description

查询 Xeno-canto 鸟鸣录音 MP3 链接。

该工具用于获取真实鸟鸣音频。优先调用 Xeno-canto API v3；当没有配置 `XENO_CANTO_API_KEY` 或调用失败时，代码会尝试读取项目中配置的 Wikimedia Commons 兜底音频。

### Parameters & Types

Pydantic 模型：`GetBirdSoundArgs`

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `bird_name_en` | `str` | yes | 英文鸟类通用名，例如：`common cuckoo` |

### Tool Definition JSON Schema

```json
{
  "type": "function",
  "function": {
    "name": "get_bird_sound",
    "description": "查询 Xeno-canto 鸟鸣录音 MP3 链接。",
    "parameters": {
      "properties": {
        "bird_name_en": {
          "description": "English common bird name, for example: common cuckoo",
          "title": "Bird Name En",
          "type": "string"
        }
      },
      "required": ["bird_name_en"],
      "title": "GetBirdSoundArgs",
      "type": "object",
      "additionalProperties": false
    },
    "strict": true
  }
}
```

### Model Tool Call Example

```json
{
  "id": "call_sound_001",
  "type": "function",
  "function": {
    "name": "get_bird_sound",
    "arguments": "{\"bird_name_en\":\"common cuckoo\"}"
  }
}
```

### Returns

成功时：

```json
{
  "ok": true,
  "bird_name_en": "common cuckoo",
  "common_name": "Common Cuckoo",
  "scientific_name": "Cuculus canorus",
  "country": "Netherlands",
  "recordist": "Recordist Name",
  "license": "Creative Commons License",
  "audio_url": "https://...",
  "source_url": "https://..."
}
```

当使用 Wikimedia Commons 兜底音频时，返回中可能包含：

```json
{
  "ok": true,
  "bird_name_en": "common cuckoo",
  "common_name": "common cuckoo",
  "scientific_name": null,
  "country": "Wikimedia Commons",
  "recordist": null,
  "license": "See Wikimedia Commons source page",
  "audio_url": "https://upload.wikimedia.org/...",
  "source_url": "https://commons.wikimedia.org/...",
  "provider": "Wikimedia Commons"
}
```

失败时：

```json
{
  "ok": false,
  "bird_name_en": "unknown bird",
  "message": "Xeno-canto 暂时没有找到这只鸟的录音。"
}
```

---

## 2.3 `write_bird_diary`

### Function Name

```text
write_bird_diary
```

### Description

保存一条观鸟日记到本地 JSON。

该工具让模型可以根据用户自然语言中的观鸟信息，自动结构化为标准日记记录，并写入本地 `diary.json`。这使 Agent 不只是问答系统，还具备可持久化的“手帐记忆”。

### Parameters & Types

Pydantic 模型：`WriteBirdDiaryArgs`，继承自 `DiaryEntryIn`

| 参数 | 类型 | 必填 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `bird_name` | `str` | yes | `minLength: 1` | 鸟名 |
| `spot_time` | `str` | yes | `minLength: 1` | 观察时间 |
| `location` | `str` | yes | `minLength: 1` | 观察地点 |
| `description` | `str` | yes | `minLength: 1` | 观察描述 |

### Tool Definition JSON Schema

```json
{
  "type": "function",
  "function": {
    "name": "write_bird_diary",
    "description": "保存一条观鸟日记到本地 JSON。",
    "parameters": {
      "properties": {
        "bird_name": {
          "minLength": 1,
          "title": "Bird Name",
          "type": "string"
        },
        "spot_time": {
          "minLength": 1,
          "title": "Spot Time",
          "type": "string"
        },
        "location": {
          "minLength": 1,
          "title": "Location",
          "type": "string"
        },
        "description": {
          "minLength": 1,
          "title": "Description",
          "type": "string"
        }
      },
      "required": ["bird_name", "spot_time", "location", "description"],
      "title": "WriteBirdDiaryArgs",
      "type": "object",
      "additionalProperties": false
    },
    "strict": true
  }
}
```

### Model Tool Call Example

```json
{
  "id": "call_diary_write_001",
  "type": "function",
  "function": {
    "name": "write_bird_diary",
    "arguments": "{\"bird_name\":\"喜鹊\",\"spot_time\":\"清晨 7:30\",\"location\":\"校园湖边\",\"description\":\"它站在柳树枝头叫了很久，像是在提醒我今天要勇敢一点。\"}"
  }
}
```

### Returns

成功时：

```json
{
  "ok": true,
  "entry": {
    "bird_name": "喜鹊",
    "spot_time": "清晨 7:30",
    "location": "校园湖边",
    "description": "它站在柳树枝头叫了很久。",
    "id": "uuid-string",
    "created_at": "2026-06-14T07:54:48.776549+00:00",
    "image_url": null
  },
  "diaries": [
    {
      "bird_name": "喜鹊",
      "spot_time": "清晨 7:30",
      "location": "校园湖边",
      "description": "它站在柳树枝头叫了很久。",
      "id": "uuid-string",
      "created_at": "2026-06-14T07:54:48.776549+00:00",
      "image_url": null
    }
  ]
}
```

说明：手动前端上传图片时，`image_url` 由 `/api/diary` 的 multipart 接口写入；LLM 工具 `write_bird_diary` 只负责文本日记写入。

---

## 2.4 `read_bird_diaries`

### Function Name

```text
read_bird_diaries
```

### Description

读取本地所有观鸟日记。

该工具让模型可以查看用户已保存的观鸟记录，用于回答“我以前记录过哪些鸟”“帮我总结最近的观鸟记录”等问题。

### Parameters & Types

Pydantic 模型：`ReadBirdDiariesArgs`

该工具不需要输入参数。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| none | none | no | 空对象 `{}` |

### Tool Definition JSON Schema

```json
{
  "type": "function",
  "function": {
    "name": "read_bird_diaries",
    "description": "读取本地所有观鸟日记。",
    "parameters": {
      "properties": {},
      "title": "ReadBirdDiariesArgs",
      "type": "object",
      "additionalProperties": false,
      "required": []
    },
    "strict": true
  }
}
```

### Model Tool Call Example

```json
{
  "id": "call_diary_read_001",
  "type": "function",
  "function": {
    "name": "read_bird_diaries",
    "arguments": "{}"
  }
}
```

### Returns

成功时：

```json
{
  "ok": true,
  "diaries": [
    {
      "bird_name": "麻雀",
      "spot_time": "中午13:30",
      "location": "校园树上",
      "description": "叽叽喳喳",
      "id": "uuid-string",
      "created_at": "2026-06-14T07:35:59.576828+00:00",
      "image_url": "/uploads/example.jpg"
    }
  ]
}
```

## 3. 小结

这 4 个工具共同构成了 Bird Agent 的外部能力边界：

- `get_bird_wiki` 负责真实百科与图片。
- `get_bird_sound` 负责真实鸟鸣音频。
- `write_bird_diary` 负责本地记忆写入。
- `read_bird_diaries` 负责本地记忆读取。

它们让“林间魔法占卜师”不只是一个会聊天的角色，而是一个能查询真实世界、保存用户观察、再把数据带回对话中的完整 AI Agent。
