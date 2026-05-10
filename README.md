# smart-search

[中文](#中文) | [English](#english)

CLI-first web research for AI agents and command-line users. Use one command to run web search, fetch page content, map a site, inspect configuration, and save reproducible JSON or Markdown evidence.

![Star History Chart](https://api.star-history.com/svg?repos=konbakuyomu/smartsearch&type=Date)

## 中文

`smart-search` 是一个给 AI 助手和命令行用户使用的网页研究工具。你可以把它理解成一个“统一搜索入口”：用同一个命令完成联网搜索、打开网页、读取站点目录、检查配置，并把结果稳定地输出成 JSON 或 Markdown。

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

- 主搜索接口：一个 OpenAI-compatible Chat Completions 接口，用来回答综合搜索问题。
- Exa：适合查官方文档、API、论文和高质量网页。
- Tavily：适合网页正文提取、站点 map 和补充搜索来源。
- Firecrawl：作为网页抓取或搜索补充来源。

这些服务都通过环境变量配置。仓库里不会保存你的真实 key。

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

最少需要配置主搜索接口：

```powershell
$env:SMART_SEARCH_API_URL = "https://your-api.example.com/v1"
$env:SMART_SEARCH_API_KEY = "your-api-key"
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
| `SMART_SEARCH_API_URL` | 主搜索接口地址，要求兼容 OpenAI Chat Completions |
| `SMART_SEARCH_API_KEY` | 主搜索接口 key |
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

`doctor` 会遮住 key，只显示配置是否完整和各服务连通状态。

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

1. 检查 `SMART_SEARCH_API_URL` 是否设置。
2. 检查 `SMART_SEARCH_API_KEY` 是否设置。
3. 检查当前终端是不是新开的，旧终端可能没有加载最新环境变量。

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

### npm 发布路线

本仓库的 npm 包名是 `@konbakuyomu/smart-search`。安装后的命令仍然叫 `smart-search`。

首次发布前，维护者需要做一次 npm Trusted Publishing 绑定。先确认已经登录 npm：

```powershell
npm login
npm whoami
```

然后用新版 npm 绑定 GitHub Actions 工作流：

```powershell
npx npm@latest trust github @konbakuyomu/smart-search --repo konbakuyomu/smartsearch --file publish-npm.yml --yes
```

这个绑定的意思是：只有 `konbakuyomu/smartsearch` 仓库里的 `.github/workflows/publish-npm.yml` 可以通过 GitHub Actions 发布这个 npm 包。仓库不需要保存长期 `NPM_TOKEN`。

日常发布步骤：

```powershell
git status --short --branch
npm version patch
git push origin main
git push origin v0.1.1
```

`npm version patch` 会同步更新 `package.json`、`package-lock.json` 和 `pyproject.toml`，这样 npm 包版本和 Python 包版本不会分叉。

如果是第一次发布当前版本，可以直接打当前版本标签：

```powershell
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions 会在推送 `v*` 标签时运行测试，然后执行 `npm publish --access public --provenance`。

如果 `npm trust github ...` 在包还没发布前返回 `E403`，先用本机登录态做一次首发：

```powershell
npm publish --access public
```

首发创建包之后，再重新运行 `npm trust github ...`。后续版本就可以只走 tag 触发的自动发布。

发布工作流会先检查 npm 上是否已经存在同版本。如果这个版本已经手动发布过，Actions 会跑完测试后跳过 `npm publish`，避免重复版本导致失败。

每次提交到 `main` 也会自动发布一个 `next` 预发布版，版本格式类似 `0.1.0-dev.123.1`。它不会修改仓库里的版本文件，只在 GitHub Actions 的临时工作目录里改版本。想安装最新提交版时使用：

```powershell
npm install -g @konbakuyomu/smart-search@next
```

正式用户默认安装的 `latest` 仍然只由 `v*` 标签发布。

公开仓库前建议检查不要提交真实 key：

```powershell
rg -n "SMART_SEARCH_API_KEY|EXA_API_KEY|TAVILY_API_KEY|FIRECRAWL_API_KEY" .
```

README 里的 `your-api-key`、`your-exa-key` 只是占位符，不要替换成真实密钥后提交。

## English

`smart-search` is a CLI-first web research tool for AI agents and terminal users. Think of it as one stable command for searching the web, fetching page content, mapping documentation sites, checking configuration, and saving evidence as JSON or Markdown.

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

- Primary search endpoint: an OpenAI-compatible Chat Completions endpoint for broad research answers.
- Exa: good for official docs, APIs, papers, and high-quality pages.
- Tavily: used for page extraction, site maps, and extra search sources.
- Firecrawl: used as an extra search source and a fetch fallback.

All providers are configured through environment variables. Do not commit real keys to this repository.

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

At minimum, configure the primary search endpoint:

```powershell
$env:SMART_SEARCH_API_URL = "https://your-api.example.com/v1"
$env:SMART_SEARCH_API_KEY = "your-api-key"
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
| `SMART_SEARCH_API_URL` | Primary OpenAI-compatible Chat Completions endpoint |
| `SMART_SEARCH_API_KEY` | Primary endpoint API key |
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

`doctor` masks keys and reports config plus provider status.

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

1. Check `SMART_SEARCH_API_URL`.
2. Check `SMART_SEARCH_API_KEY`.
3. Open a new terminal if you recently changed environment variables.

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

### npm Publishing

The npm package name is `@konbakuyomu/smart-search`. The installed command is still `smart-search`.

Before the first release, the maintainer must configure npm Trusted Publishing once. First make sure npm login works:

```powershell
npm login
npm whoami
```

Then bind the GitHub Actions workflow with a current npm CLI:

```powershell
npx npm@latest trust github @konbakuyomu/smart-search --repo konbakuyomu/smartsearch --file publish-npm.yml --yes
```

This allows only `.github/workflows/publish-npm.yml` in `konbakuyomu/smartsearch` to publish this package through GitHub Actions. The repository does not need a long-lived `NPM_TOKEN` secret.

Normal release flow:

```powershell
git status --short --branch
npm version patch
git push origin main
git push origin v0.1.1
```

`npm version patch` keeps `package.json`, `package-lock.json`, and `pyproject.toml` in sync, so the npm package version and Python package version do not drift.

For the first release of the current version:

```powershell
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions runs on `v*` tags, tests the package, and publishes with `npm publish --access public --provenance`.

If `npm trust github ...` returns `E403` before the package exists, do one local bootstrap publish first:

```powershell
npm publish --access public
```

After the first publish creates the package, run `npm trust github ...` again. Future versions can use the tag-triggered automatic publish path.

The publish workflow checks whether the same npm version already exists. If it was already published manually, Actions still runs tests and then skips `npm publish` instead of failing on a duplicate version.

Every push to `main` also publishes a `next` prerelease version such as `0.1.0-dev.123.1`. It does not modify committed version files; the version is changed only inside the GitHub Actions workspace. To install the newest commit build:

```powershell
npm install -g @konbakuyomu/smart-search@next
```

The default `latest` release remains tag-driven through `v*` tags.

Before publishing, check that no real keys are committed:

```powershell
rg -n "SMART_SEARCH_API_KEY|EXA_API_KEY|TAVILY_API_KEY|FIRECRAWL_API_KEY" .
```

The `your-api-key` and `your-exa-key` strings in this README are placeholders. Do not replace them with real secrets before committing.
