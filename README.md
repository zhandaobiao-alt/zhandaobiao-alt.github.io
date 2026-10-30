# 移动巡检机器人研究主页

公开研究进度摘要与GitHub Pages自动构建。论文正文、原始录包、模型权重、SSH密钥及本机绝对路径不进入此仓库。

## 自动流程

1. 本地更新真实代码、实验及论文状态。
2. `python scripts/sync_local.py --state <本地project_state.json>` 只导出白名单摘要。
3. `python -m unittest discover -s tests -v` 校验摘要及公开边界。
4. `python scripts/build.py` 生成 `site/`。
5. `python scripts/publish.py` 提交选定文件并推送；GitHub Actions验证后部署Pages。

Windows可使用 `更新并发布主页.cmd`。第一次使用需要在Git Credential Manager完成GitHub登录；程序不接收聊天中的密码或访问令牌，不把凭据写入仓库。

本主页记录的触发请求来自已有静止录包，不能当作独立真实导航回合。实验计数与完成状态从既有记录导出，不因生成网页而增加。

## 本地预览

```text
python scripts/build.py
python -m http.server 8765 --directory site --bind 127.0.0.1
```

## 文件

- `public/research.json`：允许公开的结构化摘要。
- `web/`：无外部依赖的界面模板、样式和交互。
- `scripts/`：摘要导出、校验构建与发布。
- `.github/workflows/pages.yml`：提交后自动验证和部署；也可手动触发。

这是研究工作记录，不是已通过学位评审、已证明算法新颖性或已完成实机导航的声明。
