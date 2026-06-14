# Forest Doodle Bird Agent

森系涂鸦风鸟类智能体：FastAPI + ModelScope/OpenAI-compatible tool calling + Wikipedia + Xeno-canto + 本地观鸟日记。

## Install

```bash
pip install -r requirements.txt
```

## Configure

Command Prompt:

```cmd
set MODELSCOPE_API_KEY=your_modelscope_key_here
set MODELSCOPE_MODEL=Qwen/Qwen3-32B
set MODELSCOPE_BASE_URL=https://api-inference.modelscope.cn/v1
```

PowerShell:

```powershell
$env:MODELSCOPE_API_KEY="your_modelscope_key_here"
$env:MODELSCOPE_MODEL="Qwen/Qwen3-32B"
$env:MODELSCOPE_BASE_URL="https://api-inference.modelscope.cn/v1"
```

Bash/zsh:

```bash
export MODELSCOPE_API_KEY=your_modelscope_key_here
export MODELSCOPE_MODEL=Qwen/Qwen3-32B
export MODELSCOPE_BASE_URL=https://api-inference.modelscope.cn/v1
```

If your ModelScope key is named `Bird_Agent` on the website, keep that as the display name there. In this project, put the actual secret value into `MODELSCOPE_API_KEY`.

To use OpenAI instead of ModelScope, set `LLM_PROVIDER=openai`, then set `OPENAI_API_KEY` and optionally `OPENAI_MODEL`.

## Run

```bash
python -m uvicorn app:app --reload
```

`uvicorn app:app --reload` is also okay after install.

Open <http://127.0.0.1:8000/>.

## Fonts

English letters and digits use `Architects Daughter` from Google Fonts.

Chinese text is configured to prefer `方正瘦金书`. Because FounderType fonts require proper authorization, this repository does not bundle or download `方正瘦金书` from unofficial mirrors.

If you have a licensed copy, convert or provide it as:

```text
fonts/FZShouJinShu.woff2
```

The page already defines an optional `@font-face` for that path. If the file is absent, the browser falls back to local calligraphy-style Chinese fonts.

## API

- `POST /api/chat` - chat with the bird agent.
- `GET /api/diary` - read the local birdwatching diary.
- `POST /api/diary` - write a local birdwatching diary entry.

## Verify

```bash
python -m py_compile app.py
python -m uvicorn app:app --reload
```

PowerShell missing-key check:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/chat -ContentType "application/json" -Body '{"message":"hello"}'
```

Without `MODELSCOPE_API_KEY`, `/api/chat` returns a friendly setup message. `/api/diary` works locally.
