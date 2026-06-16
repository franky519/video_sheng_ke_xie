# Google Vertex AI Gemini 接入教程（付费模式）

创建时间：2026-06-10 20:30（北京时间）
最后更新时间：2026-06-10 20:30（北京时间）
更新次数：1

## 背景

之前一直在用 AI Studio 的免费额度（API Key 方式）调用 Gemini。现在要切换到 Vertex AI 的付费模式，主要差异：

| | AI Studio（免费） | Vertex AI（付费） |
|:---|:---|:---|
| 认证方式 | API Key (`?key=xxx`) | Service Account JSON + Bearer Token |
| 端点 | `generativelanguage.googleapis.com` | `{region}-aiplatform.googleapis.com` |
| 速率限制 | 严格（5-15 RPM） | 按配额可调，高得多 |
| 视频上传 | Files API（resumable upload） | Cloud Storage 或 inline base64 |
| 免费额度 | Flash 模型免费 | 无（纯付费） |
| 数据使用 | 可能被用于改进产品 | 默认不用于训练 |

Token 单价跟 AI Studio 付费版一样，比如 gemini-2.5-flash 都是 $0.30/$2.50 每百万 token。

---

## 第一步：创建/选择 Google Cloud 项目

1. 打开 [Google Cloud Console](https://console.cloud.google.com/)
2. 在顶部下拉菜单里，点击"新建项目"（或者选一个已有的项目）
3. 填写项目名称，比如 `gemini-video-analysis`
4. 记下 **项目 ID**（后面会用到）

---

## 第二步：启用结算

> Vertex AI 必须绑定结算账号才能用，不能靠免费额度。

1. 左侧菜单 → **结算**（Billing）
2. 如果还没有结算账号，按提示创建一个（绑信用卡）
3. 进入"我的项目"标签，把你刚创建的项目**关联到这个结算账号**

---

## 第三步：启用 Vertex AI API

1. 左侧菜单 → **API 和服务** → **库**
2. 搜索 `Vertex AI API`
3. 点进去，点击 **启用**

---

## 第四步：创建服务账号并下载密钥

这是最关键的一步。Vertex AI 不用 API Key，而是用服务账号的 JSON 密钥来做身份认证。

1. 左侧菜单 → **IAM 和管理** → **服务账号**
2. 点击顶部 **创建服务账号**
3. 填写：
   - 服务账号名称：`gemini-api-caller`（随意）
   - 服务账号 ID：自动生成，不用改
   - 描述：随便写
4. 点击"创建并继续"
5. **角色选择**：搜索并勾选 `Vertex AI User`（这一步很重要）
6. 点击"继续" → "完成"
7. 回到服务账号列表，找到刚创建的账号，点击它
8. 顶部切换到 **密钥** 标签
9. 点击 **添加密钥** → **创建新密钥** → 选择 **JSON**
10. 浏览器会自动下载一个 JSON 文件，把它保存到安全的地方

---

## 第五步：配置密钥到项目中

把下载的 JSON 文件放到项目里：

```bash
# 我把这个文件命名为 service-account-key.json，放在项目根目录
mv ~/Downloads/你的项目名-xxxxx.json \
  ~/AI_workspace/coding/projects/general_chat/省科协科普视频/service-account-key.json
```

然后在 `.env` 里追加 Vertex AI 的配置：

```bash
# 在 Gemini本地私密配置.env 文件末尾追加以下内容：
VERTEX_PROJECT_ID=你的项目ID
VERTEX_LOCATION=us-central1
VERTEX_CREDENTIALS_PATH=./service-account-key.json
```

> `VERTEX_PROJECT_ID` 就是第一步里记下的项目 ID（不是项目名称），类似 `gemini-video-analysis-123456`

---

## 第六步：安装 Python 依赖

项目已有 `.venv` 虚拟环境，依赖已经预装好了。确认一下：

```bash
.venv/bin/python3 -c "import cv2; from google.oauth2 import service_account; print('OK')"
```

如果提示缺少模块，手动安装：

```bash
.venv/bin/pip install opencv-python google-auth google-auth-httplib2
```

> 之后运行 Vertex AI 脚本一律用 `.venv/bin/python3`，而不是系统的 `python3`。

---

## 第七步：运行 Vertex AI 版分析脚本

配套脚本在同目录下：`2026-06-10_20-30_vertex_ai_gemini_analyze.py`

```bash
cd ~/AI_workspace/coding/projects/general_chat/省科协科普视频/03_视频抽帧与裁剪工具/

# 只做文本对话测试
.venv/bin/python3 2026-06-10_20-30_vertex_ai_gemini_analyze.py --text "你好，请简单介绍你自己"

# 默认：裁剪前30秒视频，缩放到640p，inline base64 发送给 Gemini
.venv/bin/python3 2026-06-10_20-30_vertex_ai_gemini_analyze.py

# 指定其他时段
.venv/bin/python3 2026-06-10_20-30_vertex_ai_gemini_analyze.py --start 30 --end 60
```

---

## Vertex AI vs AI Studio 代码层面的差异

对比一下两边的核心调用代码，帮助理解差异：

### AI Studio 方式（你现在用的）

```python
# 认证：API Key 拼接在 URL 参数里
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={api_key}"

# 视频：先通过 Files API 上传，得到 file_uri，然后在请求里引用
payload = {
    "contents": [{
        "role": "user",
        "parts": [
            {"file_data": {"mime_type": "video/mp4", "file_uri": file_uri}},
            {"text": prompt_text}
        ]
    }]
}
```

### Vertex AI 方式（教程要用的）

```python
# 认证：Bearer Token 放在 HTTP Header 里
token = get_access_token(credentials)  # 从服务账号 JSON 生成
headers = {"Authorization": f"Bearer {token}"}

# 端点：带项目 ID 和区域
url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}/locations/us-central1/publishers/google/models/{model}:streamGenerateContent"

# 视频：inline base64 塞进请求体（或者用 GCS URI）
payload = {
    "contents": [{
        "role": "user",
        "parts": [
            {"text": prompt_text},
            {"inlineData": {"mimeType": "video/mp4", "data": base64_video}}
        ]
    }]
}
```

---

## 费用估算

以你的 5 分钟视频拉片场景为例（gemini-2.5-flash）：

- 视频部分：12MB mp4 → base64 → 约 300 帧 → 约 77,000 input tokens
- Prompt 文字：约 2,000 tokens
- 输出：约 8,000 tokens

单次 30 秒段分析：
- 输入：79K × $0.30/1M = **$0.024**
- 输出：8K × $2.50/1M = **$0.020**
- 合计：**约 $0.04（约 ¥0.29）**

全量 5 分钟（10 个段）：**约 $0.40（约 ¥2.87）**

> 如果用 gemini-3.5-flash（$1.50/$9.00），单次约 $0.19，全量约 $1.90。

---

## 常见问题

### Q: 为什么不用 Vertex AI 的 Cloud Storage 来存视频？（类似 Files API）

可以的，但配置更复杂——需要开 GCS bucket、设权限、获取 signed URL。对 12MB 这种大小的视频，inline base64 完全够用，而且 Google 直连不会像 OpenRouter 那样超时。

后续如果你觉得 inline 不够用，再升级到 GCS 方案也只需要改上传部分的代码。

### Q: 免费额度还能用吗？

AI Studio 的免费额度（API Key 方式）和 Vertex AI 是两条完全独立的通道，可以并存。你现在可以同时拥有：
- `.env` 里的 `GEMINI_API_KEY` → 走 AI Studio 免费额度
- `.env` 里的 `VERTEX_*` → 走 Vertex AI 付费

脚本会根据你指定的渠道选择对应的认证方式。

### Q: 服务账号密钥泄露了怎么办？

去 IAM → 服务账号 → 密钥 → 删掉泄露的密钥，创建一个新的。旧密钥即刻失效。
