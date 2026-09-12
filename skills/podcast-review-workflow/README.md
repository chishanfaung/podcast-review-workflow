# 播客视频剪辑 / 审片 Skill

这是一个“先审片、后决定是否压制”的本地播客视频工作流。它把原视频、Whisper 转写、保守文字校正、金句/重点词、智能切镜建议、横竖版预览和可携带的审片设置连接起来。

最重要的产品定义：浏览器页面是决策和校对层，不是剪映、CapCut、Premiere 等 NLE。默认不删素材、不重排内容、不改变原视频时长，也不把字符级时间当作剪辑时间。

## 先看结论

这个包适合：

- 双人远程访谈、会议录屏、播客录制，且原视频是左右分屏或类似的双人布局；
- 需要先核对 ASR、字幕、金句、重点词和切镜，再交给剪辑师精剪；
- 需要在同一份审片决定上检查横版 16:9 和竖版 9:16；
- 需要把人工校正和镜头选择导出成 JSON，跨机器或交给后续脚本继续处理。

它不适合直接承诺以下结果：

- 任意单人相机、多机位素材、游戏画面、纯屏幕录制或非左右分屏源的自动裁切；
- 依据 SRT 或字符时间自动做字级剪辑；
- 自动删除口癖、停顿、重复、冷场或重排叙事；
- 仅凭单声道音量判断谁在说话；
- 把 HTML 预览当成最终像素构图、发布质量或 NLE 工程文件。

如果对方的素材不符合兼容性门槛，AI 必须先报告“不支持/需要适配”，不能先生成完整成片再让用户发现画面、字幕或同步不可用。

## 给接手 AI 的使用说明

拿到这个目录后，不要直接运行渲染脚本，也不要先扫描或修改整段视频。按下面顺序接手：

1. 先读取 `SKILL.md`，再读取本 README 的“兼容性门槛”“依赖缺失时的真实能力边界”“LLM 后处理”和“发布前阻断清单”。
2. 向用户确认目标是：只做已有页面审片、重新建立审片页、重新转写/分析，还是输出横版/竖版视频。没有明确要求时默认只做非破坏性审片，不压制。
3. 运行对应的依赖探测，例如 `python3 scripts/check_dependencies.py --mode build-review`；`--mode` 可选 `existing-review`、`build-review`、`transcribe`、`render`。缺依赖就报告阻断，不要自动假装降级成功。
4. 检查源视频布局。至少抽查开头、中段、结尾，确认是左右双人分屏；否则停在“需要适配 profile”，不要套用默认裁切。
5. 检查或生成媒体基线、raw words、analysis 和 plan。每份数据必须绑定同一源视频；先校验时长和时间范围。
6. 技术输出之后执行或验证 LLM 后处理：修正明确错字/专名，提出金句和重点词，保留 correction log；没有 LLM 时必须标记“未校正”。
7. 用 `build_review.py` 生成页面，通过 `serve_review.py` 以 HTTP 打开；先验证 Range 请求和浏览器播放。
8. 让用户在页面中确认文字、金句和镜头，导出 review-settings JSON。不要把浏览器 `localStorage` 当唯一备份。
9. 用户明确要求视频文件后，先 `--prepare-only`，再分别输出横版和竖版短样片；样片通过音画、构图、字幕和尺寸检查后才允许全量压制。
10. 交付时说明已完成到哪个状态，并同时给出启动命令、页面地址、settings 备份、输出文件和仍需在 NLE 中完成的工作。

建议 AI 每个阶段只报告以下状态之一，避免把“页面生成成功”说成“成片完成”：

```text
BLOCKED_DEPENDENCY   依赖缺失，无法进入该工作模式
BLOCKED_COMPATIBILITY  素材布局或数据不符合当前 profile
READY_REVIEW         审片页可用，尚未生成视频
READY_SAMPLE         横竖版短样片已通过检查
READY_RENDER         全量输出已完成，并已完成媒体校验
```

用户可以把下面这段作为交给 AI 的启动提示：

```text
请使用 podcast-review-workflow。先读取 SKILL.md 和 README.md，运行对应模式的依赖探测，检查源视频布局、音视频流、时长和数据绑定关系。先做非破坏性审片，不要自动压制。技术转写完成后，执行有审计记录的 LLM 文本/金句/重点词处理；保留 raw ASR，不修改时间戳，不用字符时间剪辑。只有我明确要求输出视频时，才先 prepare-only，再做横版和竖版短样片，样片通过后再全量渲染。遇到缺依赖、布局不兼容、时长不匹配或字幕/音画风险时立即阻断并说明原因。
```

如果对方 AI 不能读取目录内文件，应先把 skill 解压到它的 skills 目录，确保 `SKILL.md` 位于 `podcast-review-workflow/SKILL.md`；不要只发送 README 或某个 HTML 文件。

## 兼容性门槛（不通过就停止）

### 素材形态

当前内置模板和 FFmpeg filter 假设源视频有两个左右并列的人物区域，通常是 16:9、1920×1080 的会议录屏。横版单人镜头会放大对应半屏；竖版单人镜头会从对应人物区域裁出 9:16；竖版双人镜头会把左右半屏上下堆叠。

使用前必须抽查开头、一次切镜附近、画面中段和结尾，确认：

- 左右人物确实长期位于预期半屏；
- 没有变化的布局、弹窗、共享屏幕、浮层或摄像头位置导致裁切失效；
- 上下黑边、顶部标题、底部控制栏和人脸位置已被识别；
- 原片旋转信息、有效画面区域和字幕安全区与当前 CSS/FFmpeg 参数一致。

仅凭“分辨率是 1920×1080”不能证明素材兼容。

### 必需工具

依赖按工作模式分层，不要因为“网页能打开”就默认整套流程可用：

| 工作模式 | 必需依赖 | 缺失时可以做什么 | 明确不能做什么 |
|---|---|---|---|
| 只看已经生成的审片页 | 现代 Chromium 浏览器 | 打开现成页面、人工审片、导出已有设置 | 不能重建页面、重新分析或压制 |
| 新建审片页 | Python 3、`ffprobe`、浏览器、可解码源视频 | 绑定已有 words/plan/analysis 并审片 | 没有 `ffprobe` 不能安全确认媒体基线 |
| 重新转写/分析 | 上一行依赖 + `ffmpeg` + 本地或已授权的 ASR 后端/模型 | 生成 raw words、analysis、plan | 没有 ASR 不能声称已完成可靠转写 |
| 横竖版压制 | Python 3、`ffmpeg`、可用字体和编码器 | 先 prepare、短样片、全量输出 | 没有 FFmpeg/字体/编码器不能生成最终视频 |

需要生成或检查媒体时，还需要：

- `ffprobe`：媒体基线和时长校验；
- `ffmpeg`：音频归一化、抽帧、ASS 字幕和横竖版压制；
- 本地 Whisper 或等价 ASR 后端：带 word/token 时间优先；
- 可用字体：默认压制脚本使用 macOS 的 `/System/Library/Fonts/STHeiti Medium.ttc`，非 macOS 必须改字体路径或确认 FFmpeg 能找到替代字体。

联网不是本 Skill 的必需条件。ASR 可以完全本地运行；如果对方改为云端识别，必须由对方自行确认隐私和上传授权，且仍要保存 raw 结果和后端/模型信息。

## 依赖缺失时的真实能力边界

这里没有“没有依赖也能自动完成”的魔法降级。可实现的是：先探测、明确阻断、使用用户已有产物进入受限模式，或在用户授权后安装/接入依赖。不能用浏览器时长、SRT 块级时间或文本平均分配来冒充 FFmpeg/Whisper。

### 先探测，不先安装

让对方 AI 先运行：

```bash
python3 --version
command -v ffprobe || true
command -v ffmpeg || true
python3 - <<'PY'
import importlib.util
for name in ('whisper', 'faster_whisper', 'mlx_whisper'):
    print(f'{name}:', 'present' if importlib.util.find_spec(name) else 'missing')
PY
```

`whisper` 没有统一的可执行文件名，不能只用 `command -v whisper` 判断。还要确认实际模型文件、模型格式、语言和 word/token timestamp 能力。

也可以使用包内探测脚本。它只检查，不安装依赖；退出码非 0 就是该模式的阻断信号：

```bash
python3 scripts/check_dependencies.py --mode existing-review
python3 scripts/check_dependencies.py --mode build-review
python3 scripts/check_dependencies.py --mode transcribe
python3 scripts/check_dependencies.py --mode render
```

`existing-review` 只代表脚本没有额外的本地依赖，不代表浏览器、源视频 codec 或审片页面一定可用；这些仍需人工打开验证。

### 缺少 FFmpeg / ffprobe

`ffprobe` 是媒体身份和时长校验的硬门槛；`ffmpeg` 是音频归一化、抽帧和压制的硬门槛。没有它们时：

- 若用户已经有可运行的审片页面和数据，可以进入“只看已有审片页”模式，并明确标记“不能重建/不能压制”；
- 若只有原视频，不能安全生成新的审片页，更不能用浏览器时长或文件名替代 `ffprobe`；
- 安装系统依赖前先询问用户或遵循对方环境的授权流程，不要默认执行包管理器、管理员权限或网络下载。

常见的用户自行安装方式（不是本 Skill 自动执行步骤）包括：

```bash
# macOS Homebrew
brew install ffmpeg

# Debian/Ubuntu
sudo apt-get update && sudo apt-get install ffmpeg

# Windows PowerShell（若已安装 winget）
winget install Gyan.FFmpeg.Shared
```

安装后重新运行 `command -v ffprobe`、`ffprobe -version` 和 `ffmpeg -version`。不同系统的字体路径和硬件编码器也必须重新检查。

### 缺少 Whisper / ASR

本 Skill 不捆绑 Whisper 权重，也不假定对方已经安装某个 Python 包。转写有三条合法路径：

1. 用户提供已经生成的 words JSON；只做兼容性校验和审片，不重新识别。
2. 对方提供一个本地 ASR 后端（例如 `faster-whisper`、`whisper.cpp`、MLX Whisper 或已有桌面应用），由适配器把结果转换成 [`references/data-contracts.md`](references/data-contracts.md) 的 words schema。
3. 用户明确授权使用云端 ASR；先说明素材上传、费用、保留策略和隐私风险，再保存原始结果及后端信息。

#### 推荐下载路径：faster-whisper

对大多数本地电脑，推荐先使用官方 [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)；代码包从 [PyPI](https://pypi.org/project/faster-whisper/) 安装，模型在第一次加载时从官方说明所指向的 [Hugging Face Systran 仓库](https://huggingface.co/Systran) 下载。安装和下载模型都需要用户明确允许网络、磁盘和环境变更：

```bash
python3 -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -U pip
python -m pip install faster-whisper
```

先用 30–60 秒音频验证，不要直接处理整集：

```python
from faster_whisper import WhisperModel

# 中文使用多语言模型；CPU 先用 int8，NVIDIA GPU 才考虑 cuda/float16。
model = WhisperModel("large-v3", device="cpu", compute_type="int8")
segments, info = model.transcribe(
    "normalized.wav",
    language="zh",
    beam_size=5,
    word_timestamps=True,
    vad_filter=False,
)
segments = list(segments)  # generator 必须消费，转写才真正执行
for segment in segments[:2]:
    print(segment.start, segment.end, segment.text)
    for word in segment.words or []:
        print(word.start, word.end, word.word, word.probability)
```

官方文档明确给出了 `word_timestamps=True` 和 `segment.words` 的用法。faster-whisper 自己可通过 PyAV 解码音频，但本 Skill 仍建议用 FFmpeg 做统一的 16 kHz 单声道归一化，并且最终压制仍需要 FFmpeg。模型名 `large-v3` 体积和速度成本较高；先用小模型做流程 smoke test，再决定是否升级。

#### 备选：OpenAI Whisper 官方实现

可从官方 [openai/whisper](https://github.com/openai/whisper) 安装：

```bash
python3 -m venv .venv-whisper
source .venv-whisper/bin/activate       # Windows 使用对应 activate.ps1
python -m pip install -U pip
python -m pip install -U openai-whisper
```

首次 `load_model("turbo")` 或执行 CLI 时会下载模型，默认缓存位置由 Whisper 的 `download_root`/缓存设置决定；不要把模型文件提交进 skill zip。中文应使用多语言模型（如 `turbo`、`large`），不要使用 `.en` 英语专用模型。官方实现需要系统 FFmpeg，并可在 Python `model.transcribe(..., word_timestamps=True)` 中请求 word-level timestamps；CLI 也应显式打开该选项。模型下载、缓存和显存需求见官方 README，不要从不明网盘下载权重。

#### 备选：whisper.cpp

如果对方不想依赖 Python ASR，可以使用官方 [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp)。它从自己的仓库构建 CLI，模型通过仓库自带脚本下载，模型也可从其 README 指向的 [ggerganov/whisper.cpp Hugging Face 仓库](https://huggingface.co/ggerganov/whisper.cpp)取得：

```bash
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp
cmake -B build
cmake --build build -j --config Release
sh ./models/download-ggml-model.sh large-v3-turbo
./build/bin/whisper-cli -m models/ggml-large-v3-turbo.bin \
  -f normalized.wav -l zh -ml 1
```

`-ml 1` 是官方文档中的实验性 word-level timestamp 方式；它仍需要一个适配器把 CLI 输出转换成当前 Skill 的 JSON，不能直接把终端文本交给审片页。whisper.cpp 的 CLI 当前要求 16-bit WAV，因此先做音频归一化。

不建议同时安装多个后端后由 AI 随机选择。应记录 `engine`、版本、模型名、模型来源、设备、量化/精度、语言和关键参数，并用同一段音频比较准确率和时间戳后再跑整集。

不要在缺少 ASR 时把 SRT 的块级起止时间伪装成字符级时间，也不要凭文本平均分配时间后直接剪辑。只要没有 word/token timestamp，仍可以做句级文稿审片，但必须把字符高亮标为近似。

若使用 Python ASR 包，安装和模型下载属于环境变更，需由用户决定；模型大小、RAM/显存、Metal/CUDA、CPU 速度和网络都会改变成本。先做 30–60 秒小样本，确认中文、专名、重叠说话和时间戳质量，再处理完整视频。

项目历史上有过一个依赖本机模型目录、Rust aligner 和 macOS Homebrew 硬编码路径的转写脚本；它不是本可迁移 Skill 的一部分。对方 AI 不应在另一台电脑上直接调用这类项目脚本，除非先移除平台硬编码、确认模型格式并按本 README 重新验收。

## Whisper/ASR 需要产出什么，才能支持智能剪辑

Whisper 只负责“听到什么、何时听到”；智能剪辑还需要 LLM、音频分析和画面分析。不要期待一个 `transcript.txt` 就能完成切镜、金句、字幕和安全裁切。

### 最低可接入字段

每个 segment 至少需要：

```json
{
  "text": "这一句的原始识别文本",
  "start": 12.340,
  "end": 15.870,
  "asr_index": 42,
  "words": [
    {"text": "这一", "start": 12.340, "end": 12.920, "probability": 0.96},
    {"text": "句", "start": 12.920, "end": 13.180, "probability": 0.91}
  ]
}
```

其中 `start`/`end` 必须在原视频时间轴上；`words` 用于高亮、字幕分页和人工回听定位，不直接生成 cuts。没有 word-level timestamps 仍可以做句级审片，但字符高亮只能近似。

### 强烈建议保留的 ASR 证据

在不破坏现有 `segments[]` 结构的前提下，建议把以下字段放在顶层 `asr` 或每个 segment 的 `evidence` 中：

| 字段 | 用途 | 不能单独证明 |
|---|---|---|
| `engine`, `engine_version`, `model`, `model_source` | 可复现和追责 | 识别一定正确 |
| `language`, `language_probability` | 判断语言是否选对 | 专名一定正确 |
| `avg_logprob` / `probability` | 排低置信度复核队列 | 可直接安全删除 |
| `no_speech_prob` | 发现可能的静音/幻觉段 | 识别说话人 |
| `compression_ratio`, `temperature` | 发现重复/异常解码 | 语义质量 |
| `tokens` 或 `words` | 播放高亮、局部定位、字幕分页 | 帧级切口绝对准确 |
| `initial_prompt` / glossary version | 记录术语提示影响 | 模型不会误解提示词 |
| `audio_preprocess` | 记录采样率、声道、滤波、时间戳归零 | 音画同步已被修复 |

### 智能剪辑真正还需要的派生数据

这些不是 Whisper 单独产出的，应由其他技术程序或 LLM 另存，避免混淆证据与判断：

| 派生数据 | 产出者 | 用于 |
|---|---|---|
| `corrections[]` + correction log | LLM + 人工 | 错字、专名、数字核对 |
| `quotes[]` | LLM + 人工 | 金句候选及理由 |
| `emphases[]` | LLM + 人工 | 重点词/数字/结论词 |
| `speaker_turns[]` | diarization、独立声道或人工 | 说话人候选；不能只靠音量 |
| `silence[]`, `rms`, `loudness`, clipping | 音频分析 | 停顿、爆音、噪声和节奏 |
| `shots[]`, `face_boxes`, `active_speaker_signal` | 画面分析 | 镜头构图和切镜依据 |
| `edit_suggestions[]` | LLM + 规则 + 人工 | 可选删减建议、风险和置信度 |

推荐的 `edit_suggestions[]` 是“建议”，而不是直接写入当前 settings 的 `cuts`：

```json
{
  "id": "suggestion-017",
  "kind": "sentence_skip_candidate",
  "source_start": 128.420,
  "source_end": 130.110,
  "segment_indexes": [42],
  "reason": "重复表达，需人工确认",
  "confidence": "medium",
  "evidence": ["asr_index:42", "manual-review-required"],
  "status": "proposed"
}
```

只有用户明确确认整句删除，才允许把这类候选交给 `--apply-skips`；字符级时间、低置信度预测和 LLM 的语义判断都不能直接变成剪口。

### 缺少字体或编码器

缺字体通常不会在 prepare 阶段暴露，可能在压制时失败，或回退到不同字体造成溢出。非 macOS 需要修改 `render_review.py` 中的 `fontfile`，并在横版/竖版样片里检查中文字形、字号和行高。硬件编码器不是必需品；优先保留 `libx264` 软件编码作为兼容回退。

### 缺少浏览器或不能使用本地 HTTP

页面依赖现代浏览器的 `<video>`、`requestVideoFrameCallback`（没有时有定时器回退）、`localStorage` 和 Range seek。没有现代 Chromium 时，不应把截图或静态 HTML 当成已通过审片；至少要在目标浏览器实际播放和导入/导出一次。

### 输入数据

最小输入是原视频、words JSON、plan JSON、analysis JSON：

```text
source.mov
words.corrected.words.json
finish.plan.json
finish.analysis.json
```

数据协议见 [`references/data-contracts.md`](references/data-contracts.md)。缺任意一份，或时长与源视频差异超过 0.1 秒，都应在生成页面前停止。

## 交付物和边界

打包后的 skill 应至少包含：

| 路径 | 用途 | 对方 AI 是否可继续修改 |
|---|---|---|
| `SKILL.md` | 触发条件、硬边界、主流程 | 可以，但要保持不变量 |
| `README.md` | 兼容性、运行、定制、风险、交付检查 | 可以，建议作为项目适配入口 |
| `references/data-contracts.md` | JSON 字段和时间语义 | 可以，变更需同步脚本和 UI |
| `references/llm-postprocess.md` | 技术输出后的 LLM 处理边界和审计协议 | 可以，变更需同步数据校验 |
| `references/acceptance-checklist.md` | 发布前阻断检查 | 可以按平台补充 |
| `scripts/build_review.py` | 绑定素材和数据，生成审片页 | 可以扩展输入 profile |
| `scripts/serve_review.py` | 本地 HTTP + Range 服务 | 一般不需要改 |
| `scripts/validate_review_settings.py` | 校验导出的审片设置 | schema 改动时必须同步 |
| `scripts/render_review.py` | 生成 ASS/filter，按需压制 | 改动后必须短样片验证 |
| `scripts/package_skill.py` | 排除缓存和构建产物，生成 zip | 可按发布系统扩展 |
| `scripts/check_dependencies.py` | 按工作模式探测依赖并在缺失时阻断 | 可增加组织内 ASR 后端 |
| `assets/review-template/` | HTML/CSS/JS 页面模板 | 页面定制入口 |

审片设置是“可携带的决定和交接元数据”，不是剪辑工程。它包含文字修正、重点词、关闭的金句、镜头覆盖和可选的整句跳过标记；它不包含可靠的帧级剪口、转场、素材重排、混音或 NLE 项目文件。

## 从零运行

### 1. 建立媒体基线

先记录绝对路径、容器时长、音视频流、编码、分辨率、帧率、采样率、声道、旋转、`start_time` 和像素格式：

```bash
ffprobe -v error \
  -show_entries 'format=filename,duration,size:stream=index,codec_type,codec_name,width,height,avg_frame_rate,sample_rate,channels,pix_fmt,start_time,side_data_list' \
  -of json /absolute/path/source.mov
```

不要只比较文件名或时长。时长相同的两份素材仍可能是不同版本、不同裁切、不同音画同步状态。

### 2. 转写和校正

识别前建议使用 FFmpeg 归一化为单声道 16 kHz，并把时间戳从零开始：

```bash
ffmpeg -i source.mov -vn -ac 1 -ar 16000 \
  -af 'aresample=async=1:first_pts=0' -c:a pcm_s16le normalized.wav
```

保留识别器原结果为 `*.raw.words.json`，只在派生文件或审片设置中保存校正。校正限于明确的错别字、专名、同音词和分块边界问题，不要把口语改写成另一种表达。

SRT 只有字幕块起止时间，不天然提供字符级时间。`tokens`/`chars` 仅用于播放时高亮和核对；中文 token 也不保证一 token 对应一字。任何字符级时间都不能转换为 cuts。

### 3. LLM 后处理：技术输出之后必须显式处理的语义层

技术程序只能产出音视频元数据、ASR、时间戳、RMS/画面分析和初始镜头候选；它不会自动知道专名是否正确、哪句话适合做金句、哪些词应强调。LLM 需要在这些技术结果之上做一轮受约束的处理：

- 对明确的错别字、专名、同音词和分块边界问题提出文本修正；
- 根据上下文提出金句标题/理由和重点词候选；
- 标记低置信度、数字、专名、重叠说话等需要人工回听的句子；
- 不改 `start`/`end`、token/char 时间、音频、视频或 `cuts`，不凭空补写，也不自动删除口癖/停顿。

输出应是 `*.corrected.words.json` 加一份 correction log，记录原文、最终文本、segment/asr ID、原因、置信度、处理者和时间。没有 LLM 时可以继续“未校正文稿审片”，但必须显示未校正状态；不能把技术转写直接包装成已经完成的文本处理。完整输入输出约定见 [`references/llm-postprocess.md`](references/llm-postprocess.md)。

### 4. 生成审片页面

```bash
python3 scripts/build_review.py \
  --serve-root /path/to/project \
  --output /path/to/project/review \
  --source /path/to/project/edit/final.mov \
  --words /path/to/project/edit/final.corrected.words.json \
  --plan /path/to/project/edit/final.finish.json \
  --analysis /path/to/project/edit/final.analysis.json \
  --title '播客定剪版审片' \
  --left-name '左侧嘉宾' --right-name '右侧嘉宾'

python3 scripts/serve_review.py --root /path/to/project --port 8766
```

打开 `http://127.0.0.1:8766/review/`。不要双击 HTML；`file://` 会阻止 JSON 读取，视频拖动也无法可靠依赖 Range 请求。

启动后先检查：

```bash
curl -I http://127.0.0.1:8766/review/
curl -I -H 'Range: bytes=0-1023' http://127.0.0.1:8766/path/to/source.mov
```

视频请求应返回 `206 Partial Content`。如果不能返回，先修服务或容器，不要开始长时间审片。

### 5. 审片和导出

页面中的文字校正、重点词、金句开关、镜头节点、跟随播放和撤销都只改变浏览器状态。结束时必须点击“导出审片设置”，并把 JSON 作为正式备份；`localStorage` 不是可靠交付物。

导出的 settings 必须通过：

```bash
python3 scripts/validate_review_settings.py \
  /path/to/final-review-settings.json \
  --source final.mov --duration 1234.567
```

其中 `cuts` 必须为空数组。`skipSegments` 只表示完整 Whisper segment 的回放跳过候选，不是字符删减单。

## 功能说明和实际语义

### 文稿、播放、高亮

段落是页面运行时合并出来的阅读视图；底层仍保留 segment 的原始时间。点击段落或短句只定位原视频。字符高亮用于判断大致对齐，新增/删除文字后可能退回句内线性估算，因此不能据此判断每个字的真实发音边界。

### 文本校正和重点词

校正只影响显示、字幕和导出 `edits`，不会替换音频。重点词必须是有效文本中的真实子串；它只改变字幕样式。修改文本长度后，原字符时间不再一一对应，页面仍可审片但应人工回听。

### 金句

金句按完整语义、具体观点、上下文独立性和可强调性筛选。情绪、音量或停顿只能作为辅助信号。每条候选都可以关闭；关闭状态在 `disabledQuotes` 中保存。

### 智能切镜

默认优先使用会议软件的主动发言框/边框。音频 RMS 只能判断“可能在说话或停顿”，不能识别说话人。稳定器应使用确认时间、最短镜头时长和不确定时回双人。没有可靠视觉信号时，宁可全程双人或人工编辑镜头表。

镜头表表达“从原时间轴的某个时间开始使用哪种构图”，不表达删减或素材顺序。第一节点必须从 0 秒开始，时间严格递增，视图只能是 `split`、`left`、`right`。

### 横版 / 竖版

HTML 预览和 FFmpeg 压制共用同一组镜头和文本决定，但仍可能因浏览器解码、字体、缩放、滤镜和编码器不同而产生视觉差异。竖版必须重点检查：

- 单人脸是否被裁掉、眼睛是否靠近安全区边缘；
- 双人上下堆叠时是否出现源黑边或两张脸之间的异常空白；
- 字幕是否最多两行、是否有孤字/奇怪断点/阅读过快；
- 顶部和底部是否为平台 UI、头像、标题、按钮预留安全区。

当前默认横版每行约 23 个中文字符，竖版约 10 个字符，最多两行。长句会在原句时段内分页，不改变视频时间轴。

### 短句删减预览与 `--apply-skips`

页面的“跳过删减”只是回放辅助：它跳过完整 segment，不会改源视频。默认渲染也不应用它。

只有用户明确确认要做“整句级删除”时，才可使用：

```bash
python3 scripts/render_review.py --format horizontal \
  --source edit/final.mov --words edit/final.corrected.words.json \
  --plan edit/final.finish.json --settings final-review-settings.json \
  --apply-skips --prepare-only --output edit/final-horizontal-cut.mp4
```

该选项仍不是字符级剪辑：它按完整 Whisper segment 合并区间后 trim/concat，输出时长会缩短，句首句尾可能包含多余音频或切掉语气。必须在 NLE 中二次检查自然度、呼吸、口型、章节时间和字幕边界。

## 压制流程：必须先样片

### 先生成 filter/ASS，不压制

```bash
python3 scripts/render_review.py --format horizontal \
  --source edit/final.mov --words edit/final.corrected.words.json \
  --plan edit/final.finish.json --settings final-review-settings.json \
  --prepare-only --output edit/final-horizontal.mp4

python3 scripts/render_review.py --format vertical \
  --source edit/final.mov --words edit/final.corrected.words.json \
  --plan edit/final.finish.json --settings final-review-settings.json \
  --prepare-only --output edit/final-vertical.mp4
```

检查生成的 `.ass` 和 `.filter.txt`：路径、字幕字体、行数、裁切表达式、输入输出尺寸是否符合当前素材。脚本使用 FFmpeg 的 `-/filter_complex` 文件输入形式；如果目标机器的 FFmpeg 太旧不认识该选项，应升级 FFmpeg 或在确认兼容性后改回旧参数。

### 再生成短样片

```bash
python3 scripts/render_review.py --format horizontal \
  --source edit/final.mov --words edit/final.corrected.words.json \
  --plan edit/final.finish.json --settings final-review-settings.json \
  --sample-seconds 20 --output edit/sample-horizontal.mp4

python3 scripts/render_review.py --format vertical \
  --source edit/final.mov --words edit/final.corrected.words.json \
  --plan edit/final.finish.json --settings final-review-settings.json \
  --sample-seconds 20 --output edit/sample-vertical.mp4
```

样片至少覆盖一个开场、一次切镜、一个金句或重点词、一个长字幕和竖版双人画面；不要只看前 20 秒就批准整集。用 `ffprobe` 检查样片有音频、尺寸正确、时长合理，再用播放器检查音画同步。

### 最后才全量输出

```bash
python3 scripts/render_review.py --format horizontal \
  --source edit/final.mov --words edit/final.corrected.words.json \
  --plan edit/final.finish.json --settings final-review-settings.json \
  --output edit/final-horizontal.mp4

python3 scripts/render_review.py --format vertical \
  --source edit/final.mov --words edit/final.corrected.words.json \
  --plan edit/final.finish.json --settings final-review-settings.json \
  --output edit/final-vertical.mp4
```

默认使用 `libx264`；macOS 可尝试 `--encoder h264_videotoolbox`，但硬件编码失败或质量不稳定时回到软件编码。脚本使用 `-n`，不会覆盖已有输出。

## 哪些可以定制

### 低风险定制

这些改动通常不改变时间语义：

- `--title`、左右人物名字、页面文案和品牌色；
- Whisper 模型、语言、提示词、VAD/DTW 后端；
- 金句标题/理由、重点词、shownotes 章节标签；
- `reviewChecks` 中的待校对 ASR ID；
- 页面默认倍速、字号、是否显示金句；
- 镜头计划的稳定时间、最短保持时长、回双人策略；
- `libx264` 的 preset/CRF 或经过样片验证的硬件编码器。

### 必须联动修改并验证

以下不是“改一个数字就完成”：

- 竖版有效画面带、黑边处理、人脸焦点：同步改 `assets/review-template/formats.css`、`app.js` 和 `scripts/render_review.py`，再抽查左右单人、双人上下堆叠和安全区；
- 字幕行长、字号、分页规则：同步改 `app.js` 的 `captionLayout()`、`style.css` 和 `render_review.py` 的 ASS 宽度/字号；
- settings schema：同步改页面 `validate()`、`validate_review_settings.py`、`references/data-contracts.md`；
- segment 索引策略：若从数组索引改成稳定 ID，必须同时改 UI、导出、加载和渲染映射；
- 源视频裁切：同步改 horizontal/vertical filter、脸部焦点、章节/字幕安全区，不能只改 CSS 预览；
- 章节条：HTML 与 FFmpeg 的位置、字号和安全区必须一起验收。

### 属于架构级适配

这些需求不应伪装成小修小补：

- 单人相机或多机位源；
- 通过 diarization、独立声道、人脸跟踪重新判断说话人；
- 真正的字级/帧级剪辑、转场、素材重排、B-roll、降噪、混音；
- 输出 Premiere/剪映/CapCut 可编辑工程；
- 云端 ASR、素材上传、团队协作、权限和远程存储。

需要这些能力时，可以保留本 Skill 作为审片层，但必须另写 profile、数据协议或 NLE 导出器，并重新建立验收标准。

## 风险登记：对方 AI 必须提前告诉用户

| 风险 | 触发条件 | 可能结果 | 处理方式 |
|---|---|---|---|
| 素材错配 | settings/words/plan/analysis 与源视频不是同一版本 | 字幕、镜头、金句全部套错 | 比对绝对路径、源名、时长和固定锚点；拒绝加载 |
| 时基漂移 | 采样率、时间基、start time 或长音频时间戳异常 | 开头准、结尾越播越偏 | 归一化音频、比较开中尾锚点，显式记录偏移 |
| ASR 错字/漏字 | 口音、重叠说话、专名、音乐或噪音 | 字幕和金句事实错误 | 保留 raw，设待校对队列，人工回听 |
| 字符时间误用 | 用 token/char 时间产生剪口 | 切断音节、口型或相邻词 | 字符时间只用于高亮；cuts 保持空 |
| 自动识别说话人不可靠 | 没有主动发言框、布局变动、静音或重叠讲话 | 镜头切错人、频繁抖动 | 只把音量当 speech gate；不确定时回双人/手动 |
| 预览与成片差异 | 浏览器和 FFmpeg 的缩放、字体、滤镜不同 | 竖版脸位或字幕发布后才出问题 | `--prepare-only` + 横竖短样片 + 开中尾检查 |
| 竖版裁切不适配 | 人物不在默认焦点、源黑边比例不同 | 切头、脸贴边、两人之间出现黑边 | 抽帧确认有效区域，联动修改三处参数 |
| 字幕不可读 | 单句过长、阅读速度过快、弱语义断点 | 观众读不完或断句怪 | 用待校对列表逐条回听，改写字幕分段而非改音频 |
| 字体/编码器缺失 | 非 macOS、字体不可用、VideoToolbox 不可用 | 压制失败或文字换字体溢出 | 预先确认字体和编码器，失败回退并重新样片 |
| 整句删减不自然 | `--apply-skips` 使用 segment 粗边界 | 呼吸、语气、字幕边界不自然 | 只在明确授权后使用，并交 NLE 精修 |
| 浏览器状态丢失 | 清理站点数据、换浏览器、未导出 | 人工修改无法恢复 | 每个里程碑导出 settings，并做 schema 校验 |
| 发布平台二次处理 | 平台加 UI、裁切、压缩、字幕或安全区变化 | 内容被遮挡、画质变化 | 按目标平台做最终设备/平台预览，不只看本地文件 |

## 发布前阻断清单

完整清单见 [`references/acceptance-checklist.md`](references/acceptance-checklist.md)。至少必须满足：

1. 源视频通过 `ffprobe`，同时有可播放的视频和音频流；
2. source、words、analysis、plan、review config 的时长误差不超过 0.1 秒；
3. 源布局已视觉确认，未把双人模板套到不兼容素材；
4. raw ASR 未被覆盖，校正有独立来源和可追溯记录；
5. 页面通过 HTTP 打开，Range 请求返回 206；
6. 开头、中段、结尾均抽查播放高亮、字幕和切镜；
7. 导出的 settings 可重新加载，错误 source/duration、乱序镜头和非空 cuts 会被拒绝；
8. 全量渲染前，横版和竖版短样片都通过音画、构图、字幕、时长和编码检查；
9. 交付时同时提供启动命令、页面 URL、源素材说明、数据文件、settings 备份和已知风险；
10. 用户明确知道：真正字级剪口、转场、重排和最终创作判断仍在 NLE 完成。

## 打包

不要把 `__pycache__`、`.pyc`、Rust `target/`、大视频和本期项目中间文件塞进可迁移 skill。使用包内脚本生成干净 zip：

```bash
python3 skills/podcast-review-workflow/scripts/package_skill.py \
  skills/podcast-review-workflow \
  --output dist/podcast-review-workflow.zip
```

zip 内包含顶层 `podcast-review-workflow/README.md`。交给另一套 AI 时，优先解压整个目录并让它先读取 `SKILL.md`，再根据当前素材只读取相关 references；不要只复制某个 HTML 文件。

## 进一步阅读

- [`SKILL.md`](SKILL.md)：触发条件、硬边界和主流程；
- [`references/data-contracts.md`](references/data-contracts.md)：时间轴和 JSON schema；
- [`references/acceptance-checklist.md`](references/acceptance-checklist.md)：发布前验收；
- `assets/review-template/`：页面定制入口；
- `scripts/render_review.py`：最终 filter/ASS 的实际实现，改动后必须样片验证。
