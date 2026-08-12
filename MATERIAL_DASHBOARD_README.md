# 物料进销存看板 GitHub Pages 发布说明

## 页面地址

发布后访问：`https://dash.weishenghjxh.xyz/material-dashboard/`

## 日常更新

运行 `一键更新物料看板.bat`：

1. 调用源目录的 `update_dashboard_data.py`，从 Excel 生成最新数据。
2. 将大体积内联数据拆分为带内容哈希的 JS/JSON 文件。
3. 复制省份分析数据并更新 HTML 引用。
4. 使用 WOFF2 字体，并只保留华康圆体 W7 一个中文字重。
5. 生成 Service Worker，为带哈希的静态资源提供持久缓存。
6. 将成品写入 `material-dashboard`。

这个 BAT 不会执行 Git 提交或推送。

## 正式发布

运行 `一键发布物料看板到GitHub.bat`。脚本会先更新看板，再列出仅与物料看板有关的 Git 变更。输入 `YES` 后才会提交并推送。它不会暂存仓库中已有的 `index.html`、业务数据或其他看板改动。

## 缓存策略

- `index.html`：优先联网获取，失败时使用离线缓存。
- 带内容哈希的 JS、JSON 和 WOFF2：缓存优先；数据变化会生成新文件名。
- 出入库明细：不进入首屏预缓存，只在打开“库存总览”“出入库分析”或“库存价值分析”时加载；文件使用 gzip 压缩，浏览器解压后首次加载成功即进入持久缓存。

GitHub Pages 不支持项目自行设置任意 HTTP `Cache-Control` 响应头，因此这里使用内容哈希和 Service Worker 达到长期缓存效果。

## 数据安全

生成目录包含业务明细数据。发布前应确认 GitHub 仓库和页面的访问策略符合公司要求；不要将敏感口令、上传文件或 Tunnel Token 放入仓库。
