# 原始 Prompt 摘录

本文档按项目推进顺序，整理用户在构建 Bird_Agent 过程中向Codex提出的关键原始 Prompt。

## 1. 初始构建 Prompt

```text
你是一个全栈开发专家与顶级的 UI 设计师。构建“森系涂鸦风鸟类智能体（Forest Doodle Bird Agent）”：

这是一个满足学术实验要求的 AI Agent 项目，必须包含以下核心技术与视觉要求：

### 1. 视觉风格：森系手绘涂鸦 (Forest Doodle Aesthetic)
- 背景颜色：温暖的浅纸张色（#fcfaf2）配合淡淡的林间网格或横线。
- 边框质感：所有边框（对话框、卡片、按钮）必须使用黑色、不规则、像手绘一样的线条（使用 CSS 的 border-radius 模拟，例如：border: 2.5px solid #2d3e2d; border-radius: 255px 15px 225px 15px/15px 225px 15px 255px;）。
- 调色板：森林绿（#2d4a22）、树干褐（#7d522e）、秋叶黄（#e0a96d）。
- 字体：引入 Google Fonts 的 "Architects Daughter" 手写体，中文使用圆体或看起来有手写感的系统字体。

### 2. 后端技术架构 (FastAPI + OpenAI API / Tool Calling)
请自动创建 `app.py` 和相关后端文件，实现以下机制：
- 使用 Pydantic 定义 LLM 函数调用（Function Calling）所需的标准 Schema。
- 实现标准的 Tool 调用闭环：当用户输入时，大模型会根据意图自主决定调用以下工具：
  1. `get_bird_wiki(bird_name: str)`: 调用 Wikipedia 中文 API 获取该鸟类的图片 URL、习性、生境等真实数据。
  2. `get_bird_sound(bird_name_en: str)`: 调用开源 Xeno-canto API 获取真实鸟鸣音频录音的 MP3 链接。
  3. `write_bird_diary(bird_name: str, spot_time: str, location: str, description: str)`: 将用户的观鸟日记以标准 JSON 结构保存到本地的 `diary.json` 中。
  4. `read_bird_diaries()`: 从本地 `diary.json` 中读取所有的观鸟记录返回给前端渲染。

- 包含一个具有趣味人格的 System Prompt：大模型不仅是助手，还是“林间魔法占卜师”。
  - 当用户请求“占卜”时，大模型会随机选择一种鸟，调用 `get_bird_sound` 播放其鸟鸣，并根据该鸟的特性给用户写一段治愈系的趣味占卜文（例如：布谷鸟叫代表“不急，好运在路上”）。

### 3. 前端交互界面 (Doodle Style Web UI)
请自动创建 `templates/index.html`（或直接在根目录生成前端文件），要求：
- 界面布局：
  - **左侧/上方区域（观鸟手帐本）：** 展示“每日一鸟”的精美手绘风格卡片，以及一个可上下翻阅的“观鸟日记本”（渲染自本地 `diary.json`）。包含一个可爱的音频播放器用于播放鸟鸣。
  - **右侧/下方区域（林间对话框）：** 用户与“林间占卜师”聊天的交互区域。对话框中的工具调用过程（例如：正在呼唤布谷鸟...）应以可爱的涂鸦标签显示。
  - **日记记录器：** 一个简单但精致的手画风表单，供用户快速手动添加一笔观鸟记录。
- 使用原生 JavaScript 与 `/api/chat`、`/api/diary` 接口进行异步交互。

### 4. 自动化生成文件列表：
请在工作区中直接创建并实现以下文件：
1. `app.py`: FastAPI 后端、工具定义、LLM Function Calling 逻辑、API 路由（包括聊天、写入日记、读取日记）。
2. `diary.json`: 初始化为一个空的 JSON 数组 `[]`。
3. `index.html`: 包含完整的 HTML、手绘风 CSS 样式和交互 JS。
4. `requirements.txt`: 包含 fastapi, uvicorn, httpx, openai, pydantic 等必要依赖。
5. `README.md`: 简单写明如何运行（例如 `pip install -r requirements.txt` 和 `uvicorn app:app --reload`）。
```

## 2. 字体要求 Prompt

```text
可以，字体要求：中文：方正瘦金书，英文/数字：Architects Daughter。需要下载这些字体的花联网搜索下载。
```

## 3. 模型与 API Key 适配 Prompt

```text
先解决一个最重要的问题：我没有openai的api key。我准备使用阿里魔塔的免费api key，我已经在网站上获取到了。根据项目需要，选择合适的模型，并把它适配到我的项目里。需要我输入key的时候我会输入的。
```

```text
名字是我自己命名的，是：Bird_Agent
```

## 4. 第一轮页面问题反馈 Prompt

```text
现在的问题：1.每日一鸟没有图片。2.鸟鸣播放器无法播放3.问答没有反应 4. 长度缩小，让用户的电脑屏幕不用上下滚动就可以完全展示。 5.标题改成创意的英文，并且位于整个页面的上方居中，其余功能的分栏从标题以下再开始 6.整体颜色再绿一些，每个功能的边框都有一只不同的手绘鸟
```

## 5. 日记交互与图片上传 Prompt

```text
1.现在页面很好，就是左侧有点拥挤，去掉“记录一次相遇”板块，只保留观鸟日记本，右下角点击“开始写日记”可以记录，支持用户上传本地图片 2.修复交互bug
```

```text
截图问题
```

## 6. 日记分页、打字机与 Xeno-canto Prompt

```text
很好！1.观鸟日记本的长度和右侧对话框对齐。2.日记本中一条记录占一页，图片显示在右侧，文字在左侧，实现左右翻页而不是上下滚动，黄色实线变成虚线，行与行之间的间距大一点 3.右侧对话的时候实现打字机效果，而不是生成完整的一段才显示。 4.每日一鸟的介绍如果比较多，文字部分可以上下滚动，但是图片固定。5.我已经有了XENO_CANTO_API_KEY，在这个项目中使用它
```

