# 物料进销存看板 GitHub Pages 发布说明

## 页面地址

- 综合主看板：`https://dash.weishenghjxh.xyz/material-main-dashboard/`
- 进销存看板：`https://dash.weishenghjxh.xyz/material-dashboard/`
- 运费看板：`https://dash.weishenghjxh.xyz/material-freight-dashboard/`

## 日常更新

运行 `一键更新物料看板.bat`：

1. 分别读取 `库存分析看板源数据.xlsx`、`设备分析.xlsx`、`物料运费分析.xlsx`、`售后跟进.xlsx` 和 `物料开发进度跟进表.xlsx`，不再依赖 `物料及设备报表集合.xlsx`。
2. 同时生成综合主看板、进销存看板和运费看板三个静态目录。
3. 将数据拆分或复制为带内容哈希的 JS/JSON 文件。
4. 使用 WOFF2 字体，并只保留华康圆体 W7 一个中文字重。
5. 为三个看板分别生成 Service Worker，提供持久缓存。
6. 自动改写三个页面之间的导航链接。

## 独立数据源关系

- 进销存看板：`库存分析看板源数据.xlsx` + `设备分析.xlsx`。
- 运费看板：`物料运费分析.xlsx`，同时生成汇总、订单明细、物料明细和运费试算器数据。
- 综合主看板：汇总上述库存、设备、运费数据，并读取 `售后跟进.xlsx` 和 `物料开发进度跟进表.xlsx`。
- `物料及设备报表集合.xlsx` 已退出三个看板的自动更新链路。

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
