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
  - 官方 xAI：`SMART_SEARCH_API_URL=https://api.x.ai/v1` 时，默认走 Responses API 的 `/responses`，并启用 `web_search,x_search` 工具。
  - 通用中转：其他 OpenAI-compatible 服务默认走 Chat Completions 的 `/chat/completions`。
- Exa：适合查官方文档、API、论文和高质量网页。
- Tavily：适合网页正文提取、站点 map 和补充搜索来源。
- Firecrawl：作为网页抓取或搜索补充来源。

这些服务推荐通过 `smart-search setup` 保存到当前用户的本机配置文件。仓库里不会保存你的真实 key；环境变量仍可用于 CI 或高级用户覆盖本机配置。

注意：不要给 Chat Completions 中转路线强塞 xAI 的 `web_search` / `x_search` 工具或旧 `search_parameters`。xAI 的 Chat Completions Live Search 已废弃；官方联网搜索路线是 Responses API。

### 每个命令会用到哪些服务

| 命令 | 主要用途 | 会用到的服务 |
| --- | --- | --- |
| `search` | 综合搜索并生成回答 | 主搜索接口；如果设置 `--extra-sources`，会额外调用 Tavily / Firecrawl 补来源 |
| `exa-search` | 查官方文档、API、论文、产品页 | Exa |
| `exa-similar` | 根据一个 URL 找相似网页 | Exa |
| `fetch` | 抓取一个网页正文 | 先用 Tavily；Tavily 没抓到时再用 Firecrawl 兜底 |
| `map` | 读取一个站点的页面结构 | Tavily |
| `doctor` | 检查配置和连通状态 | 主搜索接口、Exa、Tavily；Firecrawl 当前只检查 key 是否已设置 |
| `model` | 查看或修改默认模型名 | 本地配置文件 |
| `regression` | 跑离线回归测试 | 本地 pytest，不调用真实外部服务 |

`search --extra-sources N` 的行为要特别注意：

- 如果 Tavily 和 Firecrawl 都配置了，会把额外来源拆给两边，Tavily 大约占 60%，Firecrawl 占剩下部分。
- 如果只配置了 Tavily，就只用 Tavily 补来源。
- 如果只配置了 Firecrawl，就只用 Firecrawl 补来源。
- 如果不传 `--extra-sources`，`search` 只调用主搜索接口，不额外调用 Tavily / Firecrawl。

### 安装

#### 普通用户：通过 npm 全局安装

如果你只是想像 `ctx7` 一样直接装一个命令，推荐用 npm：

```powershell
npm install -g @konbakuyomu/smart-search@latest
smart-search --help
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

`setup` 会把配置保存到当前用户的本机配置文件。你可以查看配置文件路径：

```powershell
smart-search config path --format json
```

也可以用非交互方式写入配置，适合脚本或安装说明：

```powershell
smart-search setup --non-interactive `
  --api-url "https://your-api.example.com/v1" `
  --api-key "your-api-key" `
  --api-mode "auto" `
  --xai-tools "web_search,x_search" `
  --model "your-model-name" `
  --exa-key "your-exa-key" `
  --tavily-key "your-tavily-key" `
  --firecrawl-key "your-firecrawl-key"
```

查看已保存配置时会自动遮住 key：

```powershell
smart-search config list --format json
```

高级用户和 CI 仍然可以使用环境变量。环境变量优先级高于本机配置文件。最少需要配置主搜索接口：

```powershell
$env:SMART_SEARCH_API_URL = "https://your-api.example.com/v1"
$env:SMART_SEARCH_API_KEY = "your-api-key"
$env:SMART_SEARCH_API_MODE = "auto"
$env:SMART_SEARCH_XAI_TOOLS = "web_search,x_search"
$env:SMART_SEARCH_MODEL = "your-model-name"
```

可选 provider：

```powershell
$env:EXA_API_KEY = "your-exa-key"
$env:TAVILY_API_KEY = "your-tavily-key"
$env:FIRECRAWL_API_KEY = "your-firecrawl-key"
```

常用配置项：

| 变量 | 用途 |
| --- | --- |
| `SMART_SEARCH_API_URL` | 主搜索接口地址；`https://api.x.ai/v1` 默认走 xAI Responses API，其他地址默认走 Chat Completions |
| `SMART_SEARCH_API_KEY` | 主搜索接口 key |
| `SMART_SEARCH_API_MODE` | 主搜索模式：`auto`、`xai-responses`、`chat-completions`，默认 `auto` |
| `SMART_SEARCH_XAI_TOOLS` | xAI Responses API 使用的工具，默认 `web_search,x_search`；只支持这两个值 |
| `SMART_SEARCH_MODEL` | 默认模型名 |
| `SMART_SEARCH_DEBUG` | 是否打开调试日志 |
| `SMART_SEARCH_LOG_LEVEL` | 日志级别，默认 `INFO` |
| `SMART_SEARCH_LOG_DIR` | 日志目录 |
| `SMART_SEARCH_OUTPUT_CLEANUP` | 是否清理模型输出里的多余思考/拒答前缀 |
| `SMART_SEARCH_LOG_TO_FILE` | 是否把日志写入文件 |
| `SSL_VERIFY` | 是否校验证书，默认开启 |
| `EXA_API_KEY` | Exa 搜索 key |
| `TAVILY_API_KEY` | Tavily key |
| `FIRECRAWL_API_KEY` | Firecrawl key |

检查配置是否可用：

```powershell
smart-search doctor --format json
```

`doctor` 会遮住 key，只显示配置是否完整、`primary_api_mode` 实际模式和各服务连通状态。`xai-responses` 模式会用无工具的最小 `/responses` 请求做连通测试；`chat-completions` 模式继续测试 `/models` 和 `/chat/completions`。

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
- `--timeout SECONDS`：本次搜索最多等待多少秒。
- `--format json|markdown`：选择输出格式。
- `--output PATH`：同时把结果写入文件。

查官方文档或 API：

```powershell
smart-search exa-search "OpenAI Responses API documentation" --num-results 5 --include-highlights --format json
```

常用参数：

- `--num-results N`：返回多少条结果。
- `--search-type neural|keyword|auto`：选择 Exa 搜索类型。
- `--include-text`：把网页正文片段也放进结果。
- `--include-highlights`：返回 Exa 的 highlights。
- `--include-domains CSV`：只搜索这些域名，例如 `docs.python.org,developer.mozilla.org`。
- `--exclude-domains CSV`：排除这些域名。
- `--start-published-date YYYY-MM-DD`：只要某个日期之后发布的结果。
- `--category NAME`：使用 Exa 支持的分类过滤。

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

### 输出格式怎么选

默认用 JSON，适合 AI 助手继续解析：

```powershell
smart-search search "query" --format json
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
2. 再运行 `smart-search config list --format json`，确认 `SMART_SEARCH_API_URL` 和 `SMART_SEARCH_API_KEY` 已保存，key 会被自动遮住。
3. 最后运行 `smart-search doctor --format json` 重新检查连通性。高级用户如果使用环境变量，可看 `config_sources` 判断当前值来自 `environment` 还是 `config_file`。

如果 `search` 很慢：

1. 先降低 `--extra-sources`，例如从 `5` 改成 `1`。
2. 把大问题拆成几个小问题分别查。
3. 先用 `exa-search` 找来源，再用 `fetch` 抓关键网页。

如果只想确认工具本身是否正常：

```powershell
smart-search --help
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
  - Official xAI: when `SMART_SEARCH_API_URL=https://api.x.ai/v1`, `auto` mode uses the Responses API `/responses` endpoint with `web_search,x_search` tools.
  - Generic relays: other OpenAI-compatible services use Chat Completions `/chat/completions` by default.
- Exa: good for official docs, APIs, papers, and high-quality pages.
- Tavily: used for page extraction, site maps, and extra search sources.
- Firecrawl: used as an extra search source and a fetch fallback.

All providers are configured through the local config file or environment variables. Do not commit real keys to this repository.

Do not add xAI `web_search` / `x_search` tools or the old `search_parameters` field to Chat Completions relay requests. xAI Chat Completions Live Search is deprecated; the official xAI search path is the Responses API.

### Provider Usage By Command

| Command | Purpose | Providers |
| --- | --- | --- |
| `search` | Broad search and answer generation | Primary endpoint; with `--extra-sources`, also Tavily / Firecrawl |
| `exa-search` | Official docs, APIs, papers, product pages | Exa |
| `exa-similar` | Find pages similar to a URL | Exa |
| `fetch` | Fetch page content | Tavily first; Firecrawl fallback if Tavily returns no content |
| `map` | Map a site structure | Tavily |
| `doctor` | Check config and connectivity | Primary endpoint, Exa, Tavily; Firecrawl currently checks whether a key is configured |
| `model` | Read or change the default model name | Local config file |
| `regression` | Run offline regression tests | Local pytest, no real provider calls |

`search --extra-sources N` works like this:

- If both Tavily and Firecrawl are configured, extra sources are split between them. Tavily gets about 60%, Firecrawl gets the rest.
- If only Tavily is configured, only Tavily is used for extra sources.
- If only Firecrawl is configured, only Firecrawl is used for extra sources.
- If `--extra-sources` is omitted, `search` only calls the primary endpoint.

### Installation

#### Users: install globally with npm

If you want a one-command install similar to `ctx7`, use npm:

```powershell
npm install -g @konbakuyomu/smart-search@latest
smart-search --help
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

`setup` saves values to the current user's local Smart Search config file. To inspect the path:

```powershell
smart-search config path --format json
```

For scripts or copy-paste setup instructions, use non-interactive mode:

```powershell
smart-search setup --non-interactive `
  --api-url "https://your-api.example.com/v1" `
  --api-key "your-api-key" `
  --api-mode "auto" `
  --xai-tools "web_search,x_search" `
  --model "your-model-name" `
  --exa-key "your-exa-key" `
  --tavily-key "your-tavily-key" `
  --firecrawl-key "your-firecrawl-key"
```

Saved keys are masked when listed:

```powershell
smart-search config list --format json
```

Advanced users and CI can still use environment variables. Environment variables override the local config file. At minimum, configure the primary search endpoint:

```powershell
$env:SMART_SEARCH_API_URL = "https://your-api.example.com/v1"
$env:SMART_SEARCH_API_KEY = "your-api-key"
$env:SMART_SEARCH_API_MODE = "auto"
$env:SMART_SEARCH_XAI_TOOLS = "web_search,x_search"
$env:SMART_SEARCH_MODEL = "your-model-name"
```

Optional providers:

```powershell
$env:EXA_API_KEY = "your-exa-key"
$env:TAVILY_API_KEY = "your-tavily-key"
$env:FIRECRAWL_API_KEY = "your-firecrawl-key"
```

Common settings:

| Variable | Purpose |
| --- | --- |
| `SMART_SEARCH_API_URL` | Primary endpoint URL; `https://api.x.ai/v1` defaults to xAI Responses API, other URLs default to Chat Completions |
| `SMART_SEARCH_API_KEY` | Primary endpoint API key |
| `SMART_SEARCH_API_MODE` | Primary mode: `auto`, `xai-responses`, or `chat-completions`; default `auto` |
| `SMART_SEARCH_XAI_TOOLS` | xAI Responses tools, default `web_search,x_search`; only these two values are supported |
| `SMART_SEARCH_MODEL` | Default model name |
| `SMART_SEARCH_DEBUG` | Enable debug logs |
| `SMART_SEARCH_LOG_LEVEL` | Log level, defaults to `INFO` |
| `SMART_SEARCH_LOG_DIR` | Log directory |
| `SMART_SEARCH_OUTPUT_CLEANUP` | Clean extra reasoning/refusal prefixes from model output |
| `SMART_SEARCH_LOG_TO_FILE` | Write logs to a file |
| `SSL_VERIFY` | Verify TLS certificates, enabled by default |
| `EXA_API_KEY` | Exa key |
| `TAVILY_API_KEY` | Tavily key |
| `FIRECRAWL_API_KEY` | Firecrawl key |

Check configuration:

```powershell
smart-search doctor --format json
```

`doctor` masks keys and reports config, resolved `primary_api_mode`, and provider status. In `xai-responses` mode it tests `/responses` with a minimal no-tool request; in `chat-completions` mode it keeps the `/models` plus `/chat/completions` checks.

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

- `--platform NAME`: ask the primary endpoint to focus on a platform or source.
- `--model ID`: use a model for this run without changing the default.
- `--extra-sources N`: fetch N extra sources from Tavily / Firecrawl.
- `--timeout SECONDS`: hard timeout for the search.
- `--format json|markdown`: output format.
- `--output PATH`: also write the rendered output to a file.

Search docs or APIs:

```powershell
smart-search exa-search "OpenAI Responses API documentation" --num-results 5 --include-highlights --format json
```

Useful options:

- `--num-results N`: number of results.
- `--search-type neural|keyword|auto`: Exa search type.
- `--include-text`: include page text snippets.
- `--include-highlights`: include Exa highlights.
- `--include-domains CSV`: search only these domains, for example `docs.python.org,developer.mozilla.org`.
- `--exclude-domains CSV`: exclude these domains.
- `--start-published-date YYYY-MM-DD`: only results after this date.
- `--category NAME`: Exa category filter.

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

### Output Format

Use JSON by default when another tool or agent will parse the result:

```powershell
smart-search search "query" --format json
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

1. Run `smart-search setup` and enter the primary endpoint URL and key.
2. Run `smart-search config list --format json` and confirm `SMART_SEARCH_API_URL` and `SMART_SEARCH_API_KEY` are saved. Keys are masked automatically.
3. Run `smart-search doctor --format json` again. Advanced users who rely on environment variables can inspect `config_sources` to see whether a value came from `environment` or `config_file`.

If `search` is slow:

1. Reduce `--extra-sources`, for example from `5` to `1`.
2. Split a broad question into smaller searches.
3. Use `exa-search` to find sources first, then `fetch` key pages.

To check whether the tool itself works:

```powershell
smart-search --help
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
