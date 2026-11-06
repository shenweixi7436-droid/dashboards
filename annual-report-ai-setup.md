# 年度汇报编辑器 AI 配置

编辑器始终可以使用本地安全指令。配置 OpenAI API 后，会自动切换到真实 AI 模式。

## 首次配置

1. 在 OpenAI Platform 创建 API Key。
2. 在 PowerShell 中设置环境变量：

   ```powershell
   setx OPENAI_API_KEY "你的 API Key"
   setx OPENAI_MODEL "gpt-6-astra"
   ```

3. 关闭并重新打开终端或重新登录 Windows，使环境变量生效。
4. 双击 `start-annual-report-builder.cmd`。

不要把 API Key 写入 HTML、提交到 Git，或发送给其他人。

## 日常启动

双击 `start-annual-report-builder.cmd`，浏览器会自动打开：

`http://127.0.0.1:8765/annual-report-builder.html`

AI 面板显示“已连接外部 AI”时，说明配置成功。未配置或服务不可用时，编辑器会保留本地安全指令模式。

## 可选设置

- 更换模型：重新设置 `OPENAI_MODEL`。
- 更换端口：启动前设置 `REPORT_AI_PORT`。
- 联调模式：临时设置 `REPORT_AI_MOCK=1`，无需真实 API Key 即可测试服务连接。
