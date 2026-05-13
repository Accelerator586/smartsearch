# smart-search

[中文](#中文) | [English](#english)

CLI-first web research for AI agents and command-line users. Use one command to run web search, fetch page content, map a site, inspect configuration, and save reproducible JSON or Markdown evidence.

<p>
  <a href="https://linux.do">
    <img src="https://img.shields.io/badge/LinuxDo-community-1f6feb" alt="LinuxDo">
  </a>
</p>

感谢真诚、友善、团结、专业的 [LinuxDo](https://linux.do) 社区。本项目的 CLI + Skills 路线和开源推广说明均来自社区交流与启发。Thanks to the [LinuxDo](https://linux.do) community for the discussions that shaped this CLI + Skills workflow.

![Star History Chart](https://api.star-history.com/svg?repos=konbakuyomu/smartsearch&type=Date)

## 中文

`smart-search` 是一个给 AI 助手和命令行用户使用的网页研究工具。你可以把它理解成一个“统一搜索入口”：用同一个命令完成联网搜索、打开网页、读取站点目录、检查配置，并把结果稳定地输出成 JSON 或 Markdown。

本项目认可并感谢 [LinuxDo](https://linux.do) 社区，欢迎从 LinuxDo 讨论帖进入仓库、提交反馈或参与改进。

这个仓库只提供 CLI，也就是命令行工具。日常使用只需要记住一个命令：

```powershell
smart-search
```

### 适合什么时候用

- 你想让 AI 助手查当前网页信息，但希望留下可复现的命令和来源。
- 你想抓取一个 URL 的正文，并保存成 Markdown。
- 你想查官方文档、API 文档、论文、产品页面，并拿到低噪声来源列表。
- 你想在开始搜索前确认 API Key、模型和各个 provider 是否配置正确。

### 它由哪些服务组成

- 主搜索接口：支持两种路线，用来回答综合搜索问题。
  - 官方 xAI：`XAI_API_KEY` 配置后走 Responses API 的 `/responses`，并启用 `web_search,x_search` 工具。
  - 通用中转：`OPENAI_COMPATIBLE_API_URL` + `OPENAI_COMPATIBLE_API_KEY` 配置后走 Chat Completions 的 `/chat/completions`。
  - 两者都配置时是平级 `main_search` provider，默认 xAI Responses -> OpenAI-compatible 同能力兜底。
- Exa：适合查官方文档、API、论文和高质量网页。
- Context7：适合查 SDK、API、框架和库文档，作为文档检索兜底。
- 智谱：适合中文、国内、时效或域名过滤类 Web Search 补强。
- Tavily：适合网页正文提取、站点 map 和补充搜索来源。
- Firecrawl：作为网页抓取或搜索补充来源。

这些服务推荐通过 `smart-search setup` 保存到当前用户的本机配置文件。仓库里不会保存你的真实 key；环境变量仍可用于 CI 或高级用户覆盖本机配置。

注意：不要给 Chat Completions 中转路线强塞 xAI 的 `web_search` / `x_search` 工具或旧 `search_parameters`。xAI 的 Chat Completions Live Search 已废弃；官方联网搜索路线是 Responses API。

### 每个命令会用到哪些服务

| 命令 | 主要用途 | 会用到的服务 |
| --- | --- | --- |
| `search` | 综合搜索并生成回答 | 主搜索接口；按意图补充智谱 / Exa / Context7；如果设置 `--extra-sources`，会额外调用 Tavily / Firecrawl 补来源 |
| `exa-search` | 查官方文档、API、论文、产品页 | Exa |
| `exa-similar` | 根据一个 URL 找相似网页 | Exa |
| `zhipu-search` | 中文、国内、时效或域名过滤类来源检索 | 智谱 |
| `context7-library` / `context7-docs` | 查库、框架、SDK、API 文档 | Context7 |
| `fetch` | 抓取一个网页正文 | 先用 Tavily；Tavily 没抓到时再用 Firecrawl 兜底 |
| `map` | 读取一个站点的页面结构 | Tavily |
| `doctor` | 检查配置和连通状态 | 主搜索接口、Exa、Tavily、智谱、Context7；Firecrawl 当前只检查 key 是否已设置 |
| `model` | 查看或修改默认模型名 | 本地配置文件 |
| `regression` | 跑离线回归测试 | 本地 pytest，不调用真实外部服务 |
| `smoke` | 跑 provider 路由和兜底冒烟测试 | `--mock` 不用真实 key；`--live` 调真实 provider |

常用简写：

| 完整命令 | 简写 |
| --- | --- |
| `--version` | `--v` / `-v` |
| `search` / `fetch` / `map` / `doctor` | `s` / `f` / `m` / `d` |
| `exa-search` / `exa-similar` / `zhipu-search` | `exa` 或 `x` / `xs` / `z` 或 `zp` |
| `context7-library` / `context7-docs` | `c7` 或 `ctx7` / `c7docs` 或 `ctx7-docs` |
| `config list` / `config set` / `config unset` | `cfg ls` / `cfg s` / `cfg rm` |
| `model current` / `model set` | `mdl cur` / `mdl s` |
| `smoke` / `regression` | `sm` / `reg` |

`search --extra-sources N` 的行为要特别注意：

- 如果 Tavily 和 Firecrawl 都配置了，会把额外来源拆给两边，Tavily 大约占 60%，Firecrawl 占剩下部分。
- 如果只配置了 Tavily，就只用 Tavily 补来源。
- 如果只配置了 Firecrawl，就只用 Firecrawl 补来源。
- 如果不传 `--extra-sources`，`search` 仍会调用主搜索接口；在 `balanced` / `strict` 下，还会按意图调用同能力验证 provider，但不会无脑调用 Tavily / Firecrawl 额外来源。

输出里的来源字段分三层：

- `primary_sources`：主搜索接口回答中明确带出的来源，更接近回答本身的引用依据。
- `extra_sources`：Tavily / Firecrawl 并行检索到的候选来源，用来补充查证方向。
- `sources`：为了兼容旧脚本保留的合并列表，等于 `primary_sources + extra_sources` 去重后结果。

注意：`extra_sources` 不是自动事实校验。也就是说，`sources_count > 0` 只能说明工具找到了来源链接，不代表回答里的每一句话都已经被这些链接验证。新闻、政策、财经、医疗等高风险问题，建议先用 `exa-search` 找可靠来源，再用 `fetch` 抓正文，最后只基于已抓取的正文做总结。

### Deep Research 深度搜索

`smart-search` 的默认 `search` 仍然是快速搜索入口；Deep Research 是 `smart-search-cli` skill 的可选工作流，不是新的 CLI 命令，也不依赖 MCP session。用户说“帮我深度搜索...”“深度调研...”时，AI 助手会先生成一个 `research_plan`，再像拼积木一样组合现有命令。

Deep Research 不是固定题材配方。行情、选型、技术文档、新闻政策、真假核验、用户给 URL 这些都只是用户语言示例，不是 schema 里的固定枚举。skill 会先判断 `intent_signals`，例如是否强时效、是否是 docs/API、是否给了 URL、是否需要权威来源、风险高不高、是否要交叉验证，再生成 `capability_plan`。

Deep Research 计划至少包含 `mode`、`question`、`difficulty`、`intent_signals`、`capability_plan`、`evidence_policy`、`steps`、`gap_check`、`final_answer_policy`。`steps[].tool` 只使用现有 CLI 积木：`search`、`exa-search`、`exa-similar`、`zhipu-search`、`context7-library`、`context7-docs`、`fetch`、`map`；每一步都要写明用途、完整命令和输出文件路径。`doctor` 只是配置预检，不算 research step。

能力边界是：`search` 做广泛发现和综合回答，并读取现有 `routing_decision` / `provider_attempts` / `fallback_used` / `source_warning`；`exa-search` 做官方文档、API、论文、产品页、可信网页、已知域名和发布时间过滤等低噪声来源发现；`exa-similar` 从一个可靠 URL 扩展相邻来源；`zhipu-search` 补中文、国内、时效或域名过滤来源；`context7-library` / `context7-docs` 只用于库、框架、SDK、API 文档；`map` 只看站点结构；`fetch` 抓正文，是关键结论的证据入口。

默认链路是：不确定配置时先 `doctor`，用 `search --validation balanced --extra-sources 1..3` 做广泛发现，再按能力补 `exa-search` / `exa-similar` / `zhipu-search` / `context7-*` / `map`，对关键 URL 跑 `fetch` 抓正文，最后做一次 `gap_check`：没有正文证据的关键结论，要继续 fetch 或降级为未验证候选。`primary_sources` 和 `extra_sources` 在 Deep Research 里只是候选来源，不能直接当作每句话的证明。

### 安装

#### 普通用户：通过 npm 全局安装

如果你只是想像 `ctx7` 一样直接装一个命令，推荐用 npm：

```powershell
npm install -g @konbakuyomu/smart-search@latest
smart-search --help
smart-search --version
```

这个 npm 包会在安装时自动创建一个独立的 Python 虚拟环境，并把本仓库里的 Python CLI 安装进去。你仍然只需要使用 `smart-search` 这个命令。

前置条件：

- Node.js / npm 已安装。
- Python 3.10 或更新版本已安装，并且终端里能运行 `python`、`python3` 或 Windows 的 `py -3`。

#### 开发者：从源码安装

先进入仓库目录：

```powershell
cd D:\Dev\20_Software\21_Mine\smartsearch
```

创建虚拟环境并安装：

```powershell
uv venv
uv pip install -e ".[dev]"
```

如果你不用 `uv`，也可以用普通 Python 环境安装：

```powershell
python -m pip install -e ".[dev]"
```

### 配置

普通用户推荐使用内置配置向导，不需要手动设置全局环境变量：

```powershell
smart-search setup
smart-search doctor --format json
```

交互式 `setup` 会先显示 Smart Search 标题、选择语言，然后可以把 `smart-search-cli` skill 安装到当前项目的 AI 工具目录，再按能力分组配置。默认界面支持方向键移动、空格勾选、回车确认；只有 API key 和自定义 URL 需要粘贴输入：

- skill 注入：可选安装到 Codex / Claude Code / Cursor / OpenCode / GitHub Copilot 等项目本地目录，也支持 Hermes Agent 的 `~/.hermes/skills/`；只安装 `smart-search-cli`，不会初始化 Trellis，也不会生成 hooks、agents 或 commands。
- `main_search` 主搜索：xAI Responses 或 OpenAI-compatible 至少一个。
- `docs_search` 文档搜索：Exa 或 Context7 至少一个。
- `web_fetch` 网页抓取：Tavily 或 Firecrawl 至少一个。
- `web_search` 网页补强：Zhipu / Tavily / Firecrawl，属于可选增强。

如果你取消勾选一个已经配置过的 provider，`setup` 不会删除旧 key；删除配置请显式运行 `smart-search config unset KEY`。

第一次不知道怎么填，先配齐三类：`main_search + docs_search + web_fetch`。OpenAI-compatible 示例地址用官方 `https://api.openai.com/v1`；Tavily 官方地址用 `https://api.tavily.com`，号池用 `https://<host>/api/tavily`。

如果要直接进入英文向导：

```powershell
smart-search setup --lang en
```

如果你需要像旧版一样逐项配置底层 key：

```powershell
smart-search setup --advanced
```

如果只想配置 provider，不安装项目本地 skill：

```powershell
smart-search setup --skip-skills
```

如果想用脚本把 skill 注入到某个项目目录，或安装给 Hermes Agent：

```powershell
smart-search setup --non-interactive --install-skills codex,claude,cursor --skills-root "D:\path\to\project"
smart-search setup --non-interactive --install-skills hermes
```

提示：`--skills-root` 只影响 Codex / Claude Code / Cursor 等项目本地目标；Hermes Agent 按官方约定安装到当前用户的 `~/.hermes/skills/`。

`setup` 会把配置保存到当前用户的本机配置文件。你可以查看配置文件路径：

```powershell
smart-search config path --format json
```

也可以用非交互方式写入配置，适合脚本或安装说明：

```powershell
smart-search setup --non-interactive `
  --xai-api-key "your-xai-key" `
  --xai-model "grok-4-fast" `
  --openai-compatible-api-url "https://api.openai.com/v1" `
  --openai-compatible-api-key "your-openai-key" `
  --openai-compatible-model "gpt-4.1" `
  --validation-level "balanced" `
  --fallback-mode "auto" `
  --minimum-profile "standard" `
  --exa-key "your-exa-key" `
  --context7-key "your-context7-key" `
  --zhipu-key "your-zhipu-key" `
  --tavily-api-url "https://api.tavily.com" `
  --tavily-key "your-tavily-key" `
  --firecrawl-api-url "https://api.firecrawl.dev/v2" `
  --firecrawl-key "your-firecrawl-key"
```

Tavily 官方地址默认是 `https://api.tavily.com`。如果使用 Tavily Hikari/号池，REST base 应写成 `https://<host>/api/tavily`；`setup` 会把根域名或 `/mcp` 地址自动规范化到 `/api/tavily`。`/mcp` 是 MCP 入口，不是 Smart Search 调 Tavily REST 的地址。

查看已保存配置时会自动遮住 key：

```powershell
smart-search config list --format json
```

高级用户和 CI 仍然可以使用环境变量。环境变量优先级高于本机配置文件。主搜索可以只配 xAI Responses、只配 OpenAI-compatible，或两者都配：

```powershell
$env:XAI_API_KEY = "your-xai-key"
$env:XAI_MODEL = "grok-4-fast"
$env:XAI_TOOLS = "web_search,x_search"
$env:OPENAI_COMPATIBLE_API_URL = "https://api.openai.com/v1"
$env:OPENAI_COMPATIBLE_API_KEY = "your-openai-key"
$env:OPENAI_COMPATIBLE_MODEL = "gpt-4.1"
```

旧配置 `SMART_SEARCH_API_URL` / `SMART_SEARCH_API_KEY` / `SMART_SEARCH_API_MODE` / `SMART_SEARCH_MODEL` 仍兼容：`https://api.x.ai/v1` 会被识别为 xAI Responses，其他地址会被识别为 OpenAI-compatible。新配置存在时会优先生效，并把两条主搜索路线当成同能力平级 provider。

可选 provider：

```powershell
$env:EXA_API_KEY = "your-exa-key"
$env:CONTEXT7_API_KEY = "your-context7-key"
$env:ZHIPU_API_KEY = "your-zhipu-key"
$env:TAVILY_API_URL = "https://api.tavily.com"
$env:TAVILY_API_KEY = "your-tavily-key"
$env:FIRECRAWL_API_URL = "https://api.firecrawl.dev/v2"
$env:FIRECRAWL_API_KEY = "your-firecrawl-key"
```

默认最低配置是 `SMART_SEARCH_MINIMUM_PROFILE=standard`。也就是说，分发给其他环境时必须至少满足三类能力：

- `main_search`：至少配置 `XAI_API_KEY`，或 `OPENAI_COMPATIBLE_API_URL` + `OPENAI_COMPATIBLE_API_KEY`；两者都配置时按 xAI Responses -> OpenAI-compatible 做同能力兜底。
- `docs_search`：至少配置 `EXA_API_KEY` 或 `CONTEXT7_API_KEY`。
- `web_fetch`：至少配置 `TAVILY_API_KEY` 或 `FIRECRAWL_API_KEY`。

缺少任一最低能力时，`doctor` 和 `search` 会 fail closed，并返回缺失 capability。`SMART_SEARCH_MINIMUM_PROFILE=off` 只建议用于本地调试或单 provider 实验。

常用配置项：

| 变量 | 用途 |
| --- | --- |
| `SMART_SEARCH_API_URL` | 主搜索接口地址；`https://api.x.ai/v1` 默认走 xAI Responses API，其他地址默认走 Chat Completions |
| `SMART_SEARCH_API_KEY` | 主搜索接口 key |
| `SMART_SEARCH_API_MODE` | 主搜索模式：`auto`、`xai-responses`、`chat-completions`，默认 `auto` |
| `SMART_SEARCH_XAI_TOOLS` | xAI Responses API 使用的工具，默认 `web_search,x_search`；只支持这两个值 |
| `SMART_SEARCH_MODEL` | 默认模型名 |
| `XAI_API_URL` | xAI Responses API 地址，默认 `https://api.x.ai/v1` |
| `XAI_API_KEY` | xAI API key；配置后注册 `main_search` 的 xAI Responses provider |
| `XAI_MODEL` | xAI Responses 模型名，默认沿用 `SMART_SEARCH_MODEL` 或 `grok-4-fast` |
| `XAI_TOOLS` | xAI Responses 工具列表；未设置时沿用 `SMART_SEARCH_XAI_TOOLS` |
| `OPENAI_COMPATIBLE_API_URL` | OpenAI-compatible Chat Completions 地址 |
| `OPENAI_COMPATIBLE_API_KEY` | OpenAI-compatible API key；配置后注册 `main_search` 的兼容 provider |
| `OPENAI_COMPATIBLE_MODEL` | OpenAI-compatible 模型名，默认沿用 `SMART_SEARCH_MODEL` |
| `SMART_SEARCH_VALIDATION_LEVEL` | `search` 默认交叉验证强度：`fast`、`balanced`、`strict`，默认 `balanced` |
| `SMART_SEARCH_FALLBACK_MODE` | 兜底模式：`auto` 或 `off`，默认 `auto` |
| `SMART_SEARCH_MINIMUM_PROFILE` | 最低配置门槛：`standard` 或 `off`，默认 `standard` |
| `SMART_SEARCH_DEBUG` | 是否打开调试日志 |
| `SMART_SEARCH_LOG_LEVEL` | 日志级别，默认 `INFO` |
| `SMART_SEARCH_LOG_DIR` | 日志目录 |
| `SMART_SEARCH_CONFIG_DIR` | 显式指定 config 和 logs 的根目录，默认 `~/.config/smart-search`；在 sandbox / 容器 / CI 等 home 目录不可写场景下推荐显式设置 |
| `SMART_SEARCH_OUTPUT_CLEANUP` | 是否清理模型输出里的多余思考/拒答前缀 |
| `SMART_SEARCH_LOG_TO_FILE` | 是否把日志写入文件 |
| `SSL_VERIFY` | 是否校验证书，默认开启 |
| `EXA_API_KEY` | Exa 搜索 key |
| `CONTEXT7_API_KEY` | Context7 文档检索 key |
| `CONTEXT7_BASE_URL` | Context7 API 地址，默认 `https://context7.com` |
| `ZHIPU_API_KEY` | 智谱 Web Search key |
| `ZHIPU_API_URL` | 智谱 API 地址，默认 `https://open.bigmodel.cn/api` |
| `ZHIPU_SEARCH_ENGINE` | 智谱搜索引擎，默认 `search_std` |
| `TAVILY_API_URL` | Tavily REST base，默认 `https://api.tavily.com`；Hikari/号池使用 `https://<host>/api/tavily` |
| `TAVILY_API_KEY` | Tavily key |
| `FIRECRAWL_API_URL` | Firecrawl REST base，默认 `https://api.firecrawl.dev/v2` |
| `FIRECRAWL_API_KEY` | Firecrawl key |

检查配置是否可用：

```powershell
smart-search doctor --format json
```

`doctor` 会遮住 key，只显示配置是否完整、`primary_api_mode` 实际模式和各服务连通状态。`main_search_connection_tests` 会分别报告已配置的 xAI Responses 与 OpenAI-compatible；旧字段 `primary_connection_test` 保留为链上第一个 main provider 的结果。

### 常用命令

查配置：

```powershell
smart-search doctor --format json
```

综合搜索：

```powershell
smart-search search "今天 OpenAI Responses API 有哪些新变化？" --extra-sources 3 --timeout 90 --format json
```

常用参数：

- `--platform NAME`：提示主搜索接口优先关注某个平台或来源。
- `--model ID`：本次搜索临时指定模型，不修改默认模型。
- `--extra-sources N`：额外从 Tavily / Firecrawl 拉取 N 条来源。
- `--validation fast|balanced|strict`：控制交叉验证强度；默认读取 `SMART_SEARCH_VALIDATION_LEVEL`。
- `--fallback auto|off`：控制同能力兜底；`off` 会让 provider 失败时不继续尝试同 capability 下一个 provider。
- `--providers auto|CSV`：限制本次可用 provider，例如 `exa,context7`。
- `--timeout SECONDS`：本次搜索最多等待多少秒。
- `--format json|markdown|content`：选择输出格式；`content` 只打印正文，适合终端直读。
- `--output PATH`：同时把结果写入文件。

查官方文档或 API：

```powershell
smart-search exa-search "OpenAI Responses API documentation" --num-results 5 --include-highlights --format json
```

文档检索路由会优先使用 Exa；当 Exa 失败或空结果且 Context7 已配置时，Context7 作为同类文档检索兜底。普通新闻或综合查询不会强制调用 Context7。

常用参数：

- `--num-results N`：返回多少条结果。
- `--search-type neural|keyword|auto`：选择 Exa 搜索类型。
- `--include-text`：把网页正文片段也放进结果。
- `--include-highlights`：返回 Exa 的 highlights。
- `--include-domains DOMAIN...`：只搜索这些域名，例如 `docs.python.org developer.mozilla.org`，也兼容逗号分隔的 `docs.python.org,developer.mozilla.org`。
- `--exclude-domains DOMAIN...`：排除这些域名，同样兼容空格或逗号分隔。
- `--start-published-date YYYY-MM-DD`：只要某个日期之后发布的结果。
- `--category NAME`：使用 Exa 支持的分类过滤。

Context7 文档命令：

```powershell
smart-search context7-library "react" "hooks" --format json
smart-search context7-docs "/facebook/react" "useEffect cleanup" --format json
```

智谱 Web Search 命令：

```powershell
smart-search zhipu-search "今天国内 AI 新闻" --count 5 --format json
```

根据一个 URL 找相似网页：

```powershell
smart-search exa-similar "https://example.com/article" --num-results 5 --format json
```

抓取网页正文：

```powershell
smart-search fetch "https://example.com" --format markdown
```

`fetch` 会先尝试 Tavily。Tavily 没抓到正文时，如果配置了 Firecrawl，就会继续尝试 Firecrawl。

查看一个文档站点的页面结构：

```powershell
smart-search map "https://docs.example.com" --max-depth 1 --limit 50 --format json
```

`map` 当前只调用 Tavily，不调用 Firecrawl。

常用参数：

- `--instructions TEXT`：告诉 Tavily 重点找什么。
- `--max-depth N`：最多向下探索几层链接。
- `--max-breadth N`：每层最多展开多少链接。
- `--limit N`：最多返回多少个 URL。
- `--timeout SECONDS`：站点 map 最多等待多少秒。

查看当前默认模型：

```powershell
smart-search model current --format json
```

修改默认模型：

```powershell
smart-search model set "your-model-name" --format json
```

运行离线回归测试：

```powershell
smart-search regression
```

运行 provider 架构冒烟测试：

```powershell
smart-search smoke --mock --format json
smart-search smoke --live --format json
```

`--mock` 不依赖任何真实 key，用来验证 minimum profile、routing、fallback、strict insufficient evidence 等架构路径。`--live` 会调用真实 provider；单个增强 provider 失败但同 capability 仍有可用兜底时，会出现在 `degraded_cases`，关键路径失败才会退出非 0。

### 输出格式怎么选

默认用 JSON，适合 AI 助手继续解析：

```powershell
smart-search search "query" --format json
```

想直接阅读搜索生成的正文时，用 Content：

```powershell
smart-search search "nba战报" --format content
```

想直接阅读网页正文时，用 Markdown：

```powershell
smart-search fetch "https://example.com" --format markdown
```

想同时保存结果到文件：

```powershell
smart-search exa-search "Python packaging guide" --format json --output result.json
```

### 退出码

| 退出码 | 含义 |
| ---: | --- |
| `0` | 成功 |
| `2` | 参数错误 |
| `3` | 配置错误，比如缺少 key |
| `4` | 网络或上游服务错误 |
| `5` | 运行时错误或解析错误 |

### 新手排障

如果 `smart-search doctor --format json` 显示 `config_error`：

1. 先运行 `smart-search setup`，按提示填写主接口地址和 key。
2. 再运行 `smart-search config list --format json`，确认 `XAI_API_KEY` 或 `OPENAI_COMPATIBLE_API_KEY` 已保存，key 会被自动遮住。
3. 最后运行 `smart-search doctor --format json` 重新检查连通性。高级用户如果使用环境变量，可看 `config_sources` 判断当前值来自 `environment` 还是 `config_file`。

如果 `search` 很慢：

1. 先降低 `--extra-sources`，例如从 `5` 改成 `1`。
2. 把大问题拆成几个小问题分别查。
3. 先用 `exa-search` 找来源，再用 `fetch` 抓关键网页。

如果你在查“今天发生了什么”这类新闻：

1. 不要只用一个很宽泛的 `search` 结果直接写结论。
2. 先用 `exa-search` 或带来源名称的 `search --platform` 找到 Reuters、AP、BBC、新华社、官方发布页等相对可靠链接。
3. 对关键链接运行 `fetch`，最终回答只引用抓取正文中能确认的信息。

如果只想确认工具本身是否正常：

```powershell
smart-search --help
smart-search --version
smart-search regression
```

### 开发验证

运行全部测试：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

运行 CLI 回归测试：

```powershell
.\.venv\Scripts\python.exe -m smart_search.cli regression
```

验证 npm 包装层：

```powershell
npm install
npm test
npm pack --dry-run
```

## English

`smart-search` is a CLI-first web research tool for AI agents and terminal users. Think of it as one stable command for searching the web, fetching page content, mapping documentation sites, checking configuration, and saving evidence as JSON or Markdown.

This project acknowledges and thanks the [LinuxDo](https://linux.do) community. Feedback and discussion from LinuxDo users are welcome.

This repository ships only a CLI. The main command is:

```powershell
smart-search
```

### When To Use It

- You want an AI agent to use current web information with reproducible command evidence.
- You want to fetch a URL and save the page content as Markdown.
- You want low-noise sources for official docs, API references, papers, or product pages.
- You want to verify API keys, model settings, and provider connectivity before research.

### Providers

- Primary search endpoint: two routes are supported for broad research answers.
  - Official xAI: `XAI_API_KEY` uses the Responses API `/responses` endpoint with `web_search,x_search` tools.
  - Generic relays: `OPENAI_COMPATIBLE_API_URL` plus `OPENAI_COMPATIBLE_API_KEY` uses Chat Completions `/chat/completions`.
  - When both are configured, they are peer `main_search` providers with xAI Responses -> OpenAI-compatible same-capability fallback.
- Exa: good for official docs, APIs, papers, and high-quality pages.
- Tavily: used for page extraction, site maps, and extra search sources.
- Firecrawl: used as an extra search source and a fetch fallback.

All providers are configured through the local config file or environment variables. Do not commit real keys to this repository.

Do not add xAI `web_search` / `x_search` tools or the old `search_parameters` field to Chat Completions relay requests. xAI Chat Completions Live Search is deprecated; the official xAI search path is the Responses API.

### Provider Usage By Command

| Command | Purpose | Providers |
| --- | --- | --- |
| `search` | Broad search and answer generation | Main search providers; with `--extra-sources`, also Tavily / Firecrawl |
| `exa-search` | Official docs, APIs, papers, product pages | Exa |
| `exa-similar` | Find pages similar to a URL | Exa |
| `fetch` | Fetch page content | Tavily first; Firecrawl fallback if Tavily returns no content |
| `map` | Map a site structure | Tavily |
| `doctor` | Check config and connectivity | Main search providers, Exa, Tavily, Zhipu, Context7; Firecrawl currently checks whether a key is configured |
| `model` | Read or change the default model name | Local config file |
| `regression` | Run offline regression tests | Local pytest, no real provider calls |

Common short aliases:

| Full command | Alias |
| --- | --- |
| `--version` | `--v` / `-v` |
| `search` / `fetch` / `map` / `doctor` | `s` / `f` / `m` / `d` |
| `exa-search` / `exa-similar` / `zhipu-search` | `exa` or `x` / `xs` / `z` or `zp` |
| `context7-library` / `context7-docs` | `c7` or `ctx7` / `c7docs` or `ctx7-docs` |
| `config list` / `config set` / `config unset` | `cfg ls` / `cfg s` / `cfg rm` |
| `model current` / `model set` | `mdl cur` / `mdl s` |
| `smoke` / `regression` | `sm` / `reg` |

`search --extra-sources N` works like this:

- If both Tavily and Firecrawl are configured, extra sources are split between them. Tavily gets about 60%, Firecrawl gets the rest.
- If only Tavily is configured, only Tavily is used for extra sources.
- If only Firecrawl is configured, only Firecrawl is used for extra sources.
- If `--extra-sources` is omitted, `search` only calls configured main search providers plus intent-routed validation providers.

Search output separates source provenance:

- `primary_sources`: sources explicitly extracted from the primary search answer.
- `extra_sources`: parallel Tavily / Firecrawl candidate links for follow-up checks.
- `sources`: the backward-compatible merged list, deduped from `primary_sources + extra_sources`.

Important: `extra_sources` are not automatic fact verification. `sources_count > 0` means links were found; it does not prove every claim in `content`. For news, policy, finance, health, or other high-risk facts, use `exa-search` to find reliable pages, `fetch` key URLs, and summarize only from fetched page text.

### Deep Research

Default `smart-search search` remains the fast search entrypoint. Deep Research is an optional `smart-search-cli` skill workflow, not a new CLI command and not an MCP-session dependency. When the user asks for "deep search", "deep research", or similar multi-source verification, the AI agent first creates a `research_plan`, then composes existing CLI commands like building blocks.

Deep Research is not a fixed topic recipe system. Market research, product comparison, technical docs, news or policy, claim verification, and URL-first prompts are examples of user language, not required schema enums. The skill first infers `intent_signals`, such as recency, docs/API intent, known URL, source authority need, claim risk, cross-validation need, and breadth/depth budget, then creates a `capability_plan`.

The plan includes `mode`, `question`, `difficulty`, `intent_signals`, `capability_plan`, `evidence_policy`, `steps`, `gap_check`, and `final_answer_policy`. `steps[].tool` may only use existing CLI blocks: `search`, `exa-search`, `exa-similar`, `zhipu-search`, `context7-library`, `context7-docs`, `fetch`, and `map`; each step must include its purpose, full command, and output path. `doctor` is preflight, not a research step.

Capability boundaries: `search` is for broad discovery and synthesis, using existing `routing_decision` / `provider_attempts` / `fallback_used` / `source_warning` as routing evidence; `exa-search` is for low-noise official/API/paper/product/trusted-page discovery; `exa-similar` expands from a known reliable URL; `zhipu-search` reinforces Chinese, domestic, current, or domain-filtered discovery; `context7-library` / `context7-docs` are only for library, framework, SDK, and API docs; `map` explores site structure; `fetch` extracts page text and is required before claim-level conclusions.

The default chain is: run `doctor` when config is uncertain, use `search --validation balanced --extra-sources 1..3` for broad discovery, add `exa-search` / `exa-similar` / `zhipu-search` / `context7-*` / `map` only when their capability matches the intent, fetch key URLs, then run `gap_check`. Unsupported key claims must be fetched or downgraded to unverified candidates. In Deep Research, `primary_sources` and `extra_sources` are candidates until fetched.

### Installation

#### Users: install globally with npm

If you want a one-command install similar to `ctx7`, use npm:

```powershell
npm install -g @konbakuyomu/smart-search@latest
smart-search --help
smart-search --version
```

The npm package creates an isolated Python virtual environment during installation and installs this repository's Python CLI into it. The command remains `smart-search`.

Prerequisites:

- Node.js / npm is installed.
- Python 3.10 or newer is installed and available as `python`, `python3`, or `py -3` on Windows.

#### Developers: install from source

Enter the repository:

```powershell
cd D:\Dev\20_Software\21_Mine\smartsearch
```

Create a virtual environment and install:

```powershell
uv venv
uv pip install -e ".[dev]"
```

Without `uv`, use pip:

```powershell
python -m pip install -e ".[dev]"
```

### Configuration

Most users should use the built-in setup wizard instead of manually editing global environment variables:

```powershell
smart-search setup
smart-search doctor --format json
```

Interactive `setup` asks for language first, then configures by capability group. The default UI supports arrow-key navigation, Space to select, and Enter to confirm; only API keys and custom URLs need pasted text:

- skill injection: optionally installs `smart-search-cli` into project-local AI tool directories such as Codex, Claude Code, Cursor, OpenCode, and GitHub Copilot. It also supports Hermes Agent's `~/.hermes/skills/`. It only installs the skill; it does not initialize Trellis or generate hooks, agents, or commands.
- `main_search`: at least one of xAI Responses or OpenAI-compatible.
- `docs_search`: at least one of Exa or Context7.
- `web_fetch`: at least one of Tavily or Firecrawl.
- `web_search`: Zhipu / Tavily / Firecrawl as optional reinforcement.

Unchecking an already configured provider does not delete old values. Remove a saved key explicitly with `smart-search config unset KEY`.

If you do not know what to fill on a first install, configure three categories first: `main_search + docs_search + web_fetch`. For OpenAI-compatible examples, use official `https://api.openai.com/v1`; official Tavily uses `https://api.tavily.com`, and pooled endpoints use `https://<host>/api/tavily`.

To open the English wizard directly:

```powershell
smart-search setup --lang en
```

To configure low-level keys one by one like older releases:

```powershell
smart-search setup --advanced
```

To configure providers without installing project-local skills:

```powershell
smart-search setup --skip-skills
```

To install the skill into a project from a script, or install it for Hermes Agent:

```powershell
smart-search setup --non-interactive --install-skills codex,claude,cursor --skills-root "D:\path\to\project"
smart-search setup --non-interactive --install-skills hermes
```

Note: `--skills-root` only affects project-local targets such as Codex, Claude Code, and Cursor. Hermes Agent installs to the current user's `~/.hermes/skills/` by convention.

`setup` saves values to the current user's local Smart Search config file. To inspect the path:

```powershell
smart-search config path --format json
```

For scripts or copy-paste setup instructions, use non-interactive mode:

```powershell
smart-search setup --non-interactive `
  --xai-api-key "your-xai-key" `
  --xai-model "grok-4-fast" `
  --openai-compatible-api-url "https://api.openai.com/v1" `
  --openai-compatible-api-key "your-openai-key" `
  --openai-compatible-model "gpt-4.1" `
  --exa-key "your-exa-key" `
  --tavily-api-url "https://api.tavily.com" `
  --tavily-key "your-tavily-key" `
  --firecrawl-api-url "https://api.firecrawl.dev/v2" `
  --firecrawl-key "your-firecrawl-key"
```

The official Tavily base is `https://api.tavily.com`. For Tavily Hikari or pooled endpoints, the REST base should be `https://<host>/api/tavily`; `setup` normalizes root-host and `/mcp` inputs to `/api/tavily`. `/mcp` is the MCP entrypoint, not the REST base Smart Search should call.

Saved keys are masked when listed:

```powershell
smart-search config list --format json
```

Advanced users and CI can still use environment variables. Environment variables override the local config file. Main search can be xAI Responses only, OpenAI-compatible only, or both:

```powershell
$env:XAI_API_KEY = "your-xai-key"
$env:XAI_MODEL = "grok-4-fast"
$env:XAI_TOOLS = "web_search,x_search"
$env:OPENAI_COMPATIBLE_API_URL = "https://api.openai.com/v1"
$env:OPENAI_COMPATIBLE_API_KEY = "your-openai-key"
$env:OPENAI_COMPATIBLE_MODEL = "gpt-4.1"
```

Legacy `SMART_SEARCH_API_URL` / `SMART_SEARCH_API_KEY` / `SMART_SEARCH_API_MODE` / `SMART_SEARCH_MODEL` still work. `https://api.x.ai/v1` is treated as xAI Responses; other endpoints are treated as OpenAI-compatible. When the new explicit keys are present, xAI Responses and OpenAI-compatible are peer `main_search` providers.

Optional providers:

```powershell
$env:EXA_API_KEY = "your-exa-key"
$env:CONTEXT7_API_KEY = "your-context7-key"
$env:ZHIPU_API_KEY = "your-zhipu-key"
$env:TAVILY_API_URL = "https://api.tavily.com"
$env:TAVILY_API_KEY = "your-tavily-key"
$env:FIRECRAWL_API_URL = "https://api.firecrawl.dev/v2"
$env:FIRECRAWL_API_KEY = "your-firecrawl-key"
```

The default minimum profile is `SMART_SEARCH_MINIMUM_PROFILE=standard`. A distributable install must have at least one provider in each required capability:

- `main_search`: at least `XAI_API_KEY`, or `OPENAI_COMPATIBLE_API_URL` plus `OPENAI_COMPATIBLE_API_KEY`; when both are configured, fallback is xAI Responses -> OpenAI-compatible within the same capability.
- `docs_search`: at least `EXA_API_KEY` or `CONTEXT7_API_KEY`.
- `web_fetch`: at least `TAVILY_API_KEY` or `FIRECRAWL_API_KEY`.

If a required capability is missing, `doctor` and `search` fail closed with the missing capability list. Use `SMART_SEARCH_MINIMUM_PROFILE=off` only for local experiments.

Common settings:

| Variable | Purpose |
| --- | --- |
| `SMART_SEARCH_API_URL` | Primary endpoint URL; `https://api.x.ai/v1` defaults to xAI Responses API, other URLs default to Chat Completions |
| `SMART_SEARCH_API_KEY` | Primary endpoint API key |
| `SMART_SEARCH_API_MODE` | Primary mode: `auto`, `xai-responses`, or `chat-completions`; default `auto` |
| `SMART_SEARCH_XAI_TOOLS` | xAI Responses tools, default `web_search,x_search`; only these two values are supported |
| `SMART_SEARCH_MODEL` | Default model name |
| `XAI_API_URL` | xAI Responses API URL, default `https://api.x.ai/v1` |
| `XAI_API_KEY` | xAI API key; registers the xAI Responses `main_search` provider |
| `XAI_MODEL` | xAI Responses model name, defaults to `SMART_SEARCH_MODEL` or `grok-4-fast` |
| `XAI_TOOLS` | xAI Responses tools; falls back to `SMART_SEARCH_XAI_TOOLS` |
| `OPENAI_COMPATIBLE_API_URL` | OpenAI-compatible Chat Completions endpoint |
| `OPENAI_COMPATIBLE_API_KEY` | OpenAI-compatible API key; registers the compatible `main_search` provider |
| `OPENAI_COMPATIBLE_MODEL` | OpenAI-compatible model name, defaults to `SMART_SEARCH_MODEL` |
| `SMART_SEARCH_VALIDATION_LEVEL` | Default cross-validation level for `search`: `fast`, `balanced`, or `strict`; default `balanced` |
| `SMART_SEARCH_FALLBACK_MODE` | Same-capability fallback mode: `auto` or `off`; default `auto` |
| `SMART_SEARCH_MINIMUM_PROFILE` | Minimum profile gate: `standard` or `off`; default `standard` |
| `SMART_SEARCH_DEBUG` | Enable debug logs |
| `SMART_SEARCH_LOG_LEVEL` | Log level, defaults to `INFO` |
| `SMART_SEARCH_LOG_DIR` | Log directory |
| `SMART_SEARCH_CONFIG_DIR` | Override the root for both config and logs (default `~/.config/smart-search`); recommended in sandbox / container / CI where the home directory is not writable |
| `SMART_SEARCH_OUTPUT_CLEANUP` | Clean extra reasoning/refusal prefixes from model output |
| `SMART_SEARCH_LOG_TO_FILE` | Write logs to a file |
| `SSL_VERIFY` | Verify TLS certificates, enabled by default |
| `EXA_API_KEY` | Exa key |
| `CONTEXT7_API_KEY` | Context7 documentation search key |
| `CONTEXT7_BASE_URL` | Context7 API base URL, default `https://context7.com` |
| `ZHIPU_API_KEY` | Zhipu Web Search key |
| `ZHIPU_API_URL` | Zhipu API base URL, default `https://open.bigmodel.cn/api` |
| `ZHIPU_SEARCH_ENGINE` | Zhipu search engine, default `search_std` |
| `TAVILY_API_URL` | Tavily REST base, default `https://api.tavily.com`; Hikari/pooled endpoints use `https://<host>/api/tavily` |
| `TAVILY_API_KEY` | Tavily key |
| `FIRECRAWL_API_URL` | Firecrawl REST base, default `https://api.firecrawl.dev/v2` |
| `FIRECRAWL_API_KEY` | Firecrawl key |

Check configuration:

```powershell
smart-search doctor --format json
```

`doctor` masks keys and reports config, resolved `primary_api_mode`, and provider status. `main_search_connection_tests` reports each configured xAI Responses and OpenAI-compatible provider separately; the legacy `primary_connection_test` field remains as the first main provider check.

### Common Commands

Check configuration:

```powershell
smart-search doctor --format json
```

Broad search:

```powershell
smart-search search "latest OpenAI Responses API changes" --extra-sources 3 --timeout 90 --format json
```

Useful options:

- `--platform NAME`: ask the selected main search provider to focus on a platform or source.
- `--model ID`: use a model for this run without changing the default.
- `--extra-sources N`: fetch N extra sources from Tavily / Firecrawl.
- `--validation fast|balanced|strict`: control cross-validation level; defaults to `SMART_SEARCH_VALIDATION_LEVEL`.
- `--fallback auto|off`: control same-capability fallback; `off` stops after the first matching provider.
- `--providers auto|CSV`: restrict providers for this run, for example `exa,context7`.
- `--timeout SECONDS`: hard timeout for the search.
- `--format json|markdown|content`: output format; `content` prints only the generated body for direct terminal reading.
- `--output PATH`: also write the rendered output to a file.

Search docs or APIs:

```powershell
smart-search exa-search "OpenAI Responses API documentation" --num-results 5 --include-highlights --format json
```

Docs routing prefers Exa. If Exa fails or returns no results and Context7 is configured, Context7 is used as the same-capability fallback. General news or broad web queries do not force Context7.

Useful options:

- `--num-results N`: number of results.
- `--search-type neural|keyword|auto`: Exa search type.
- `--include-text`: include page text snippets.
- `--include-highlights`: include Exa highlights.
- `--include-domains DOMAIN...`: search only these domains, for example `docs.python.org developer.mozilla.org`; comma-separated `docs.python.org,developer.mozilla.org` is also accepted.
- `--exclude-domains DOMAIN...`: exclude these domains; whitespace-separated and comma-separated forms are both accepted.
- `--start-published-date YYYY-MM-DD`: only results after this date.
- `--category NAME`: Exa category filter.

Context7 documentation commands:

```powershell
smart-search context7-library "react" "hooks" --format json
smart-search context7-docs "/facebook/react" "useEffect cleanup" --format json
```

Zhipu Web Search command:

```powershell
smart-search zhipu-search "today China AI news" --count 5 --format json
```

Find similar pages:

```powershell
smart-search exa-similar "https://example.com/article" --num-results 5 --format json
```

Fetch a page:

```powershell
smart-search fetch "https://example.com" --format markdown
```

`fetch` tries Tavily first. If Tavily returns no content and Firecrawl is configured, it tries Firecrawl.

Map a documentation site:

```powershell
smart-search map "https://docs.example.com" --max-depth 1 --limit 50 --format json
```

`map` currently uses Tavily only.

Useful options:

- `--instructions TEXT`: tell Tavily what to focus on.
- `--max-depth N`: maximum link depth.
- `--max-breadth N`: maximum links to expand per depth.
- `--limit N`: maximum URLs returned.
- `--timeout SECONDS`: site map timeout.

Read current default model:

```powershell
smart-search model current --format json
```

Change default model:

```powershell
smart-search model set "your-model-name" --format json
```

Run offline regression tests:

```powershell
smart-search regression
```

Run provider architecture smoke tests:

```powershell
smart-search smoke --mock --format json
smart-search smoke --live --format json
```

`--mock` uses no real keys and validates the minimum profile gate, routing, fallback, and strict insufficient-evidence path. `--live` calls real providers; a single enhancement provider can be reported in `degraded_cases` when the same capability still has a working fallback, while critical failures still exit non-zero.

### Output Format

Use JSON by default when another tool or agent will parse the result:

```powershell
smart-search search "query" --format json
```

Use Content when you want only the generated answer body:

```powershell
smart-search search "nba战报" --format content
```

Use Markdown when you want to read fetched page content:

```powershell
smart-search fetch "https://example.com" --format markdown
```

Save output to a file:

```powershell
smart-search exa-search "Python packaging guide" --format json --output result.json
```

### Exit Codes

| Code | Meaning |
| ---: | --- |
| `0` | Success |
| `2` | Parameter error |
| `3` | Configuration error, such as a missing key |
| `4` | Network or upstream provider error |
| `5` | Runtime or parse error |

### Beginner Troubleshooting

If `smart-search doctor --format json` returns `config_error`:

1. Run `smart-search setup` and enter at least one main search provider key.
2. Run `smart-search config list --format json` and confirm `XAI_API_KEY` or `OPENAI_COMPATIBLE_API_KEY` is saved. Keys are masked automatically.
3. Run `smart-search doctor --format json` again. Advanced users who rely on environment variables can inspect `config_sources` to see whether a value came from `environment` or `config_file`.

If `search` is slow:

1. Reduce `--extra-sources`, for example from `5` to `1`.
2. Split a broad question into smaller searches.
3. Use `exa-search` to find sources first, then `fetch` key pages.

For current-news questions:

1. Do not rely on one broad `search` result as final evidence.
2. Use `exa-search` or source-focused `search --platform` to find reliable pages such as Reuters, AP, BBC, official releases, or domain-specific primary sources.
3. Run `fetch` on key URLs and cite only facts confirmed by fetched page text.

To check whether the tool itself works:

```powershell
smart-search --help
smart-search --version
smart-search regression
```

### Development

Run all tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Run CLI regression tests:

```powershell
.\.venv\Scripts\python.exe -m smart_search.cli regression
```

Verify the npm wrapper:

```powershell
npm install
npm test
npm pack --dry-run
```

### Release lanes

Stable releases use Git tags and npm `latest`:

```powershell
git tag v0.1.10
git push origin v0.1.10
```

Test releases use npm prereleases and do not move `latest`. A push to `main`
publishes the next `<package.json version>-beta.N` version under npm dist-tag `next`;
`N` resets for each stable base version. For example, after
`0.1.10-beta.1` and `0.1.10-beta.2`, the next `main` publish is
`0.1.10-beta.3`.

GitHub Actions also supports manual backfill for historical test builds through
`workflow_dispatch`. Use an explicit `target_ref` plus an exact version such as
`0.1.9-beta.1`, and publish it with a non-`latest` tag such as `backfill`.
npm versions are immutable:
old `*-dev.*` packages cannot be renamed in place, only superseded by new
`*-beta.N` packages and optionally deprecated later with npm owner credentials.
