# smart-search

`smart-search` 是一个给 AI 助手和命令行用户使用的网页研究工具。你可以把它理解成一个“统一搜索入口”：用同一个命令完成联网搜索、打开网页、读取站点目录、检查配置，并把结果稳定地输出成 JSON 或 Markdown。

这个仓库只提供 CLI，也就是命令行工具。日常使用只需要记住一个命令：

```powershell
smart-search
```

## 适合什么时候用

- 你想让 AI 助手查当前网页信息，但希望留下可复现的命令和来源。
- 你想抓取一个 URL 的正文，并保存成 Markdown。
- 你想查官方文档、API 文档、论文、产品页面，并拿到低噪声来源列表。
- 你想在开始搜索前确认 API Key、模型和各个 provider 是否配置正确。

## 它由哪些服务组成

- 主搜索接口：一个 OpenAI-compatible Chat Completions 接口，用来回答综合搜索问题。
- Exa：适合查官方文档、API、论文和高质量网页。
- Tavily：适合网页正文提取、站点 map 和补充搜索来源。
- Firecrawl：作为网页抓取或搜索补充来源。

这些服务都通过环境变量配置。仓库里不会保存你的真实 key。

## 每个命令会用到哪些服务

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

## 安装

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

## 配置

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

## 常用命令

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

## 输出格式怎么选

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

## 退出码

| 退出码 | 含义 |
| ---: | --- |
| `0` | 成功 |
| `2` | 参数错误 |
| `3` | 配置错误，比如缺少 key |
| `4` | 网络或上游服务错误 |
| `5` | 运行时错误或解析错误 |

## 新手排障

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

## 开发验证

运行全部测试：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

运行 CLI 回归测试：

```powershell
.\.venv\Scripts\python.exe -m smart_search.cli regression
```

公开仓库前建议检查不要提交真实 key：

```powershell
rg -n "SMART_SEARCH_API_KEY|EXA_API_KEY|TAVILY_API_KEY|FIRECRAWL_API_KEY" .
```

README 里的 `your-api-key`、`your-exa-key` 只是占位符，不要替换成真实密钥后提交。
