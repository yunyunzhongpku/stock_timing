# Git & VS Code 小抄（GIT‑CHEATSHEET.md)

> 目的：把「我改了代码 → 提交 → 同步到远程 → 回看旧版本/撤销/对比」这些高频动作一次讲清，**VS Code 操作与 CLI 等价**一一对应。

---

## 0. 最短口诀（记这个就够）
**改 → 加（Stage）→ 注（写 message）→ 本（Commit 到本地）→ 推（Push 到远程）→ 提（开 PR）→ 合（Merge）**

> VS Code 里没有“submit”这个术语；你说的 *submit* 通常指 **Push**（推到远程）或在 GitHub 上 **开 PR**。

---

## 1. 三层模型
工作区（文件） → **暂存区**（`git add`/Stage） → 本地提交（`git commit`） → 远程（`git push`）

- **CHANGES**：未暂存改动（M=修改、U=未跟踪、A=新增、D=删除、R=重命名）
- **STAGED CHANGES**：已 `add`，等待 `commit`
- **GRAPH 历史**：按提交查看全库历史（点圆点）

---

## 2. 常用操作对照表（VS Code ↔ CLI）

| 目标 | VS Code 操作 | 命令行等价 |
|---|---|---|
| 暂存单个文件 | 文件前 **+** / 右键 *Stage Changes* | `git add path/to/file` |
| 暂存全部 | 顶部 `…` → *Stage All* | `git add -A` |
| 取消暂存 | 文件前 **–** / 右键 *Unstage* | `git restore --staged path/to/file` |
| 提交 | 输入框写说明 → **Commit** | `git commit -m "msg"` |
| 修补上次提交 | `…` → *Amend Last Commit* | `git commit --amend` |
| 推送到远程 | **Push**（云朵/同步图标） | `git push` |
| 首次公开分支 | **Publish Branch** | `git push -u origin <branch>` |
| 获取远程更新 | `…` → *Fetch* | `git fetch` |
| 拉取并合并 | `…` → *Pull* | `git pull --ff-only`（或 `--rebase`） |
| 新建分支 | 左下角分支名 → *Create Branch* | `git switch -c new-branch` |
| 切换分支 | 左下角分支名 → 选择 | `git switch <branch>` |
| 从某提交建分支 | Graph 右键提交 → *Create Branch From Commit* | `git switch -c tmp <commit>` |
| 打标签 | 命令面板 *Git: Create Tag* | `git tag v1.0 && git push --tags` |
| 看历史 | Graph/Timeline | `git log --oneline --graph --decorate` |
| 看文件历史 | 打开文件 → 右上角 **Timeline** | `git log -- path/to/file` |
| 与上一版对比 | 文件右键 → *Compare with Previous* | `git diff HEAD^ -- path/to/file` |
| 与任意提交对比 | Graph 右键提交 *Select for Compare* → 文件右键 *Compare with Selected* | `git diff <a> <b> -- file` |
| 还原单文件到某提交 | Graph/Timeline 右键文件 *Restore* | `git restore --source=<commit> -- path/to/file` |
| 回滚一笔提交（安全） | Graph 右键提交 *Revert* | `git revert <commit>` |
| 重置到旧提交（危险） | Graph 右键 *Reset…*（Soft/Mixed/Hard） | `git reset --soft|--mixed|--hard <commit>` |
| 暂存现场 | `…` → *Stash* / *Stash (Include Untracked)* | `git stash push -u -m "msg"` |
| 取回现场 | `…` → *Apply/Pop Stash* | `git stash apply` / `git stash pop` |
| 找出谁改了这行 | 右键 → *Open Timeline*（或装 GitLens 看 Blame） | `git blame file` |
| 摘樱桃（挑一笔改动过来） | Graph 右键提交 *Cherry Pick* | `git cherry-pick <commit>` |
| 二分定位坏提交 |（装插件更方便） | `git bisect start`… |
| 多工位并行查看 |（命令行为主） | `git worktree add ../repo-old <commit>` |

---

## 3. 高频场景 Playbook

### A. “我就想看看以前的代码”
1) **Graph** 点某个提交 → 右侧文件列表 → 点文件即可查看历史快照（只读）。  
2) 单文件：打开文件 → **Timeline** → 选一条记录。

### B. “临时回旧版本跑一下”
- **推荐**：Graph 右键旧提交 → *Create Branch From Commit* → 切过去跑；避免 *detached HEAD*。

### C. “把旧版里的某个文件拿回来”
- Graph/Timeline 里对该文件 **Restore**（或复制粘贴）。  
- CLI：`git restore --source=<commit> -- path/to/file`

### D. “撤销一笔已经推到远程的错误提交”
- **Revert**（生成反向提交，历史不变）比 **Reset** 更安全。

### E. “我改到一半，要切分支/下班”
- **Stash**：存起来 → 之后 *Apply/Pop* 继续。

### F. “解决合并冲突（极简心法）”
1) Pull 或合并出现冲突→ VS Code 会在文件中高亮 `<<<<<<<` `=======` `>>>>>>>`。  
2) 用每处的 **Accept Current/Incoming/Both** 选择。  
3) 处理完：**Stage** 冲突文件 → **Commit** →（必要时）**Push**。

---

## 4. 提交信息（建议）
- 尽量采用「**动词 + 目的**」：`fix: handle NaN in risk model` / `feat: add rolling Sharpe panel` / `refactor: extract fetch_wind_data()`
- 一次提交专注一件事；描述能让“未来的你”秒懂。

---

## 5. 常见混淆 & 风险
- **add（Stage）≠ 真正入库**：仅把当前改动放入“本次提交候选集”。
- **commit 只在本地**：不 Push，别人看不到。
- **Revert vs Reset**：线上优先 *Revert*；*Reset* 会改历史，公共分支慎用，`--hard` 会丢改动。
- **Restore vs Checkout**：恢复文件内容用 *Restore*；切换分支/提交用 *Switch/Checkout*。

---

## 6. VS Code 小设置（可选）
- **Smart Commit**：`git.enableSmartCommit`（新手建议关闭，按“先 Stage 再 Commit”流程更清晰）
- **Pull 时使用 rebase**：`git.pullRebase` = true（历史更直）
- **忽略空白对比**：`diffEditor.ignoreTrimWhitespace` = true

---

## 7. 实用命令别名（可加到 `~/.gitconfig`）
```ini
[alias]
  st = status -sb
  co = checkout
  sw = switch
  br = branch
  cm = commit -m
  aa = add -A
  lg = log --oneline --graph --decorate --all
  last = show --stat HEAD
```

---

## 8. 最后再复习 10 秒
**改 → Stage → Commit → Push →（GitHub）开 PR → Merge**  
回看旧版：**Graph/Timeline**； 还原单文件：**Restore**；撤销错误：**Revert**；收起现场：**Stash**。

> 放在项目根目录命名为 **`GIT-CHEATSHEET.md`**，以后迷糊时 30 秒能找回全部节奏。

