# Rebase develop onto upstream/main

## Goal

把 fork 仓库 `Accelerator586/smartsearch` 的 `develop` 分支 rebase 到 `upstream/main` 最新提交之上，吸收上游 11 个提交，同时保留本地 5 个 Trellis 工作流相关的提交。

## Context

- 仓库为个人 fork（不向上游 PR），`origin` = `Accelerator586/smartsearch`，`upstream` = `konbakuyomu/smartsearch`。
- `develop` 当前领先 upstream 5 个提交、落后 11 个提交。
- upstream 在 fetch 时报告了一次 `forced update`（`bd80b95...8e24a75`），说明上游 main 历史被改写过，rebase 时需注意 base 对齐。
- 本地 5 个提交全部是 Trellis 相关（`.trellis/` 目录、skills、journal），与上游 `src/` 代码改动应无冲突。

## Requirements

- 优先保持线性历史，吸收上游 11 个提交。
- 完成后通过 `git push --force-with-lease` 推到 `origin/develop`。

## Decision Log

直接 `git rebase upstream/main` 在 `dfa3ddd feat(skills): adopt dual-axis evidence extension contract` 一步产生 6 个文件冲突
（`README.md`、`skills/smart-search-cli/SKILL.md`、`skills/smart-search-cli/references/cli-contract.md`、
对称的 `src/smart_search/assets/skills/smart-search-cli/...` 两个文件、`tests/test_regression.py`）。
冲突源于本地 dual-axis contract 改造与上游 deep-research / Hermes skill / CLI routing 新代码同时改了相同文件。

最终采用**保守混合方案**：abort rebase，建 backup 分支后 `git reset --hard upstream/main`，
再按时间顺序 cherry-pick **3 个**无冲突的 `.trellis` / `.cursor` 工作流提交。
跳过 `dfa3ddd`（dual-axis contract）和 `5eed123`（清理 dfa3ddd 创建的原始路径文件，依赖 dfa3ddd 才有意义）。

`dfa3ddd` 留作独立后续任务，在阅读完上游新结构后基于新上游重新设计 / 实现 dual-axis 契约。

## Acceptance Criteria

- [x] `git fetch upstream` 成功，本地 `upstream/main` 已是最新。
- [x] `develop` 重置到 `upstream/main` 后 cherry-pick `a03989b`、`27356e1`、`eee048c` 全部干净。
- [x] `git log --oneline develop ^upstream/main` 输出 3 个本地提交（c8d767d、526cff9、e39f648）。
- [x] `git log --oneline upstream/main ^develop` 输出为空（已无落后提交）。
- [x] `origin/develop` 已通过 `--force-with-lease` 更新（`5eed123...e39f648 develop -> develop`）。
- [x] 本地保留 `backup/develop-pre-rebase` 分支（HEAD = 5eed123），可随时回滚。
- [ ] GitHub 页面 "behind 11 commits" 提示消失（待用户在网页上确认）。

## Follow-up

- 创建后续任务"基于新上游重做 dual-axis evidence extension contract"，重新设计 PRD 后再实现。
- backup 分支 `backup/develop-pre-rebase` 在确认 dfa3ddd 重做完成、`dfa3ddd` 内容已迁移后再删除。

## Notes / Risks

- 因为是个人 fork、不向上游 PR，`--force-with-lease` push 是安全的。
- 本任务未对 `src/` 做任何修改，cherry-pick 只触及 `.trellis/` 和 `.cursor/`，因此 develop 的代码态与 upstream/main 完全一致，无需额外跑测试。
