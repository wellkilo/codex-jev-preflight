# Codex Jev Preflight

把 [TypeSafe Jev](https://docs.typesafe.ai) 接入 Codex 的全局 `UserPromptSubmit` Hook。每个新任务开始前，Jev 会先生成一组简短的预判元数据：

- `task_type`：任务类型
- `complexity`：复杂度
- `risk`：风险等级
- `execution_mode`：建议的初始执行方式

这些信息会作为**建议上下文**注入 Codex。它不会替代 Codex，也不会覆盖系统指令、开发者指令或用户的明确要求。

项目采用 fail-open 设计：Jev 超时、限流、额度耗尽或响应异常时，Hook 会跳过判断，原任务继续正常执行。

> 本项目不是 OpenAI、Codex、TypeSafe 或 Jev 的官方项目。

## 在线展示前端

- GitHub Pages：<https://wellkilo.github.io/codex-jev-preflight/>
- 前端源码：[`docs/index.html`](docs/index.html)
- 前端说明：[`docs/README.md`](docs/README.md)

展示页包含安装命令、快速开始 Prompt、路由维度说明和一个不访问真实 API 的交互式评估演示。

## 快速开始（复制 Prompt 给 Codex）

最省事的方式是把下面这段 Prompt 直接粘贴给 Codex。它会读取项目 README、安装项目、隐藏输入 API Key、安装 Hook，并验证结果：

```text
请安装并配置 Codex Jev Preflight。

要求：
1. 阅读 https://github.com/wellkilo/codex-jev-preflight 的 README。
2. 从源码安装项目，并运行 codex-jev-configure 配置 TypeSafe Jev API Key。
3. API Key 必须隐藏输入，不要要求我在聊天中粘贴。
4. 运行 codex-jev-install 安装全局 UserPromptSubmit Hook。
5. 验证 Hook 输出，并告诉我需要重启 Codex 还是新建任务。
6. 不要覆盖 ~/.codex/hooks.json 或 ~/.codex/AGENTS.md 中的其他配置。
```

如果只想手动执行，最快命令是：

```bash
git clone https://github.com/wellkilo/codex-jev-preflight.git
cd codex-jev-preflight
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip && python -m pip install -e .
codex-jev-configure
codex-jev-install
```

安装并重启 Codex 后，不需要在每条消息中手动调用 Jev。下面这些 Prompt 会自然触发预判：

```text
检查这个仓库的认证模块，定位安全风险并给出最小修复方案。
```

```text
阅读项目并实现导出 CSV 的功能，补充测试和 README。
```

```text
对比三个开源方案，给出架构、成本和维护风险建议。
```

## 为什么需要它

普通 Codex 任务通常由模型自行判断“应该直接回答、先检查再执行、先规划，还是先澄清”。本 Hook 把这一步统一交给 Jev，并在模型开始工作前提供稳定的结构化提示。

适用场景：

- 希望多个 Codex 任务使用一致的任务分类和风险判断
- 希望高风险任务更早进入“先检查、后修改”流程
- 希望减少简单任务上的无效规划
- 希望在额度受限时安全降级，不影响 Codex 正常工作

## 和现有 Jev 项目的区别

GitHub 已有多个 Jev + Codex 项目，但侧重点不同：

| 项目 | 主要用途 |
| --- | --- |
| [jev-codex-router](https://github.com/0xNatoshi/jev-codex-router) | 按每次模型调用选择模型和推理强度 |
| [skillpick](https://github.com/govindup63/skillpick) | 按用户提示选择 Agent Skill |
| [jev-mcp](https://github.com/burnigtm/jev-mcp) | 通过 MCP 将 Jev 接入编程工作流 |
| [jev-desktop](https://github.com/yikangy873-gif/jev-desktop) | Codex Computer Use 中的动作选择 |
| **Codex Jev Preflight** | 在 `UserPromptSubmit` 阶段注入任务类型、复杂度、风险和执行模式 |

如果你需要模型路由，优先使用 `jev-codex-router`；如果你只需要任务预判元数据，可以使用本项目。

## 运行要求

- Python 3.9+
- 支持 `UserPromptSubmit` Hook 的 Codex
- 一个可用的 TypeSafe Jev API Key
- 项目本身只使用 Python 标准库，不依赖第三方 Python 包

## 安装

### 方式一：从源码安装到虚拟环境

```bash
git clone https://github.com/wellkilo/codex-jev-preflight.git
cd codex-jev-preflight

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

安装后会得到两个命令：

```bash
codex-jev-configure
codex-jev-install
```

### 方式二：使用 pipx

```bash
pipx install git+https://github.com/wellkilo/codex-jev-preflight.git
```

开发和调试建议使用方式一。

## 第一步：配置 Jev API Key

运行：

```bash
codex-jev-configure
```

程序会隐藏输入 API Key，并默认写入：

```text
~/.codex/jev.env
```

文件权限会自动设置为 `0600`。默认内容如下：

```dotenv
TYPESAFE_API_KEY=你的 Key
TYPESAFE_API_ENDPOINT=https://api.typesafe.ai/v1/systemone
JEV_MODEL=jev-latest
JEV_STATE_PATH=/Users/你的用户名/.codex/.jev_quota_state.json
```

如需自定义位置：

```bash
codex-jev-configure \
  --env-file "$HOME/.config/codex-jev-preflight/env" \
  --state-path "$HOME/.cache/codex-jev-preflight/quota.json"
```

不要把真实 `.env`、`jev.env` 或 API Key 提交到 Git。

## 第二步：安装 Codex 全局 Hook

```bash
codex-jev-install
```

安装器会：

1. 将 Hook 合并到 `~/.codex/hooks.json`
2. 将 Jev-first 规则合并到 `~/.codex/AGENTS.md`
3. 备份原文件为 `.bak`
4. 保留其他已有 `UserPromptSubmit` Hook

出于安全考虑，安装器默认**不会自动信任 Hook**。重启 Codex 或新建任务后，根据界面提示确认一次即可。

如果你明确接受自动信任行为，可以运行：

```bash
codex-jev-install --trust
```

普通使用不建议开启 `--trust`。

## 第三步：验证安装

不消耗 Jev 额度的配置检查：

```bash
python -m unittest discover -s tests -v
```

直接测试 Hook 输出：

```bash
HOOK=$(python -c 'import jev_user_prompt_hook; print(jev_user_prompt_hook.__file__)')
printf '%s' '{"prompt":"检查项目并给出修复方案","hook_event_name":"UserPromptSubmit"}' |
  python "$HOOK"
```

成功时，输出 JSON 的 `additionalContext` 中应包含：

```text
JEV PRE-TASK ASSESSMENT
```

然后重启 Codex 或新开一个任务。新的用户消息前应能看到 Jev 自动生成的预判结果。

## 配置查找顺序

Hook 按以下顺序查找配置：

1. 环境变量 `JEV_ENV_FILE` 指定的文件
2. 项目源码目录中的 `.env`
3. 当前工作目录中的 `.env`
4. `$CODEX_HOME/jev.env`
5. `$XDG_CONFIG_HOME/codex-jev-preflight/env`

已经存在的进程环境变量优先，不会被文件覆盖。

支持以下变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `TYPESAFE_API_KEY` | 无 | Jev API Key，必填 |
| `TYPESAFE_API_ENDPOINT` | `https://api.typesafe.ai/v1/systemone` | TypeSafe System One 端点 |
| `JEV_MODEL` | `jev-latest` | 使用的 Jev 模型 |
| `JEV_STATE_PATH` | `.jev_quota_state.json` | 额度熔断状态文件 |
| `JEV_ENV_FILE` | 无 | 显式指定配置文件 |
| `JEV_HOOK_DEBUG_LOG` | 无 | 可选 Hook 调试日志路径 |

## 路由维度

| 字段 | 可选值 |
| --- | --- |
| `task_type` | `answer`, `code_change`, `research`, `browser_automation`, `planning`, `conversation`, `other` |
| `complexity` | `trivial`, `simple`, `moderate`, `complex` |
| `risk` | `low`, `medium`, `high` |
| `execution_mode` | `direct_answer`, `inspect_then_act`, `plan_then_execute`, `ask_clarification` |

示例：

```text
JEV PRE-TASK ASSESSMENT (automatic, advisory routing metadata):
- task_type: code_change
- complexity: moderate
- risk: medium
- execution_mode: inspect_then_act
```

Jev 返回未知值时会被安全归一化为 `unknown`。

## 隐私和网络

Hook 会将当前用户提示的**前 24,000 个字符**发送到配置的 TypeSafe 端点。除此之外，本项目不会主动收集或上传：

- 本机文件
- Git 仓库内容
- 环境变量全集
- Codex 对话历史
- API Key 以外的认证信息

请根据你的组织和数据合规要求决定是否启用。不要在提示中提交不希望发送到第三方服务的敏感信息。

## 额度处理和降级

客户端包含持久化熔断器：

- API 明确返回额度耗尽时，写入状态并停止后续 Jev 调用
- HTTP 429 等临时错误使用短时冷却
- 熔断期间 Hook 输出 `skipped` 上下文，Codex 继续正常工作
- 增加额度后可以删除状态文件，或运行：

```bash
python -c 'from jev_agent import get_default_client; get_default_client().reset()'
```

## 卸载

1. 从 `~/.codex/hooks.json` 删除本项目的 `UserPromptSubmit` Handler。
2. 从 `~/.codex/AGENTS.md` 删除 `JEV-FIRST-START` 和 `JEV-FIRST-END` 之间的内容。
3. 如需恢复安装前状态，可使用同目录下生成的 `.bak` 备份。
4. 删除 `~/.codex/jev.env` 和额度状态文件。
5. 如果使用 pip 或 pipx 安装，再执行 `pip uninstall codex-jev-preflight` 或 `pipx uninstall codex-jev-preflight`。

## 开发

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

测试完全离线，不会调用真实 Jev API。

## 文档目录

| 文档 | 内容 |
| --- | --- |
| [展示前端](docs/index.html) | 快速开始、交互式演示和项目概览 |
| [前端说明](docs/README.md) | 本地预览与 GitHub Pages 部署 |
| [架构说明](docs/architecture.md) | Hook 流程、路由字段和降级路径 |
| [安全说明](SECURITY.md) | 数据边界和漏洞报告方式 |
| [贡献指南](CONTRIBUTING.md) | 本地开发和提交要求 |

## License

MIT License。见 [`LICENSE`](LICENSE)。
