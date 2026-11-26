# 演员排期表排版工具 · 独立部署指南

这套部署包用于把网站部署到第三方云平台，从而拿到一个**不带 sharecode 的干净公开网址**。

当前的 `paiqitu.app.workbuddy.host/?sharecode=...` 是 WorkBuddy 应用托管平台的链接，sharecode 是该平台强制的访问凭据，无法去掉。部署到下方任一平台后，即可得到形如 `https://你的应用名.onrender.com` 这样无需任何参数、任何人都能直接打开的网址。

---

## 一、这套包里有什么

```
saoju-calendar-deploy/
├── app.py              Flask 后端（含全部 API）
├── generator.py        抓取 saoju.net + 渲染 PNG 的核心逻辑
├── templates/
│   └── index.html      前端页面（姓名搜索、配色、底图上传）
├── static/             静态资源
├── requirements.txt    Python 依赖（已固定版本）
├── Dockerfile          容器定义（含 Chromium 与中文字体）
├── .dockerignore       构建排除项
└── DEPLOY_GUIDE.md     本文档
```

已固定版本：Python 3.11、Flask 3.1.2、Playwright 1.58.0。字体使用思源宋体 / 思源黑体（SIL OFL 1.1，可商用），由 Dockerfile 自动安装。

---

## 二、部署前必读（三个关键点）

1. **必须用支持 Docker 或自定义 Python 环境的平台。** 网站需要跑 Playwright + 无头 Chromium 把 HTML 渲染成 PNG，纯静态托管（GitHub Pages、Vercel 静态页等）跑不了。本包已备好 Dockerfile，选支持 Docker 的平台最省事。

2. **服务器需要能访问 y.saoju.net。** 网站在服务器侧抓取演员页数据，如果目标平台的出口 IP 被 saoju.net 拦截，会出现抓取失败。部署后先按第五节验证一下。

3. **文件存储是临时的。** 导出的图片和用户上传的底图存在容器内 `outputs/` 和 `uploads/`，容器重启会清空。对"导出后立即下载"的使用场景没有影响，但不适合当作长期存储。若要多实例长期保留，需要接入对象存储（如 Cloudflare R2、AWS S3），这属于进阶改造。

---

## 三、方案 A：Render（推荐，最省心）

Render 支持直接用 Dockerfile 部署，免费层可用（免费层冷启动较慢，首次访问可能要等几十秒）。

步骤：
1. 注册 Render 账号（https://render.com），可用 GitHub 账号登录。
2. 把本目录整个上传到一个新的 GitHub 仓库（新建仓库 → 上传这些文件）。
3. 在 Render 控制台点 **New + → Web Service**，连接刚才的 GitHub 仓库。
4. 关键配置：
   - Runtime / Environment：选 **Docker**。
   - Plan：免费层选 Free；正式使用建议 Starter（冷启动快、更稳定）。
   - Environment Variables：添加一个变量 `PORT`，值填 `8080`（Dockerfile 默认也是 8080，保持一致即可）。
   - 其余保持默认。
5. 点 **Create Web Service**，等待构建完成（首次构建要下载 Chromium 和字体，约几分钟）。
6. 构建成功后，Render 会给出形如 `https://你的服务名.onrender.com` 的网址，这就是干净链接。

注意：Render 免费层闲置一段时间后会自动休眠，下次访问需等待唤醒。若介意，选付费 Starter 层。

---

## 四、方案 B：Railway

Railway 同样支持 Dockerfile，按用量计费，有免费试用额度。

步骤：
1. 注册 Railway 账号（https://railway.app），可用 GitHub 登录。
2. 新建 Project → **Deploy from GitHub repo**，选择存有本包代码的仓库。
3. Railway 会自动识别 Dockerfile 并构建。
4. 在服务的 **Variables** 里添加 `PORT=8080`。
5. 构建完成后，进入服务 **Settings → Networking → Generate Domain**，获得公开域名。
6. 也可以在这里绑定你自己的域名（见第六节）。

---

## 五、方案 C：Fly.io

Fly.io 免费层有一定额度，适合熟悉命令行的用户。

步骤：
1. 注册 Fly.io 账号（https://fly.io），安装 flyctl 命令行工具并登录 `fly auth login`。
2. 在本目录执行 `fly launch`，按提示创建 fly.toml（识别到 Dockerfile 即可）。
3. 执行 `fly deploy`。
4. 部署完成后用 `fly open` 打开，或用 `fly ips allocate-v4` 分配公网 IP 后绑定域名。

---

## 六、部署后验证（必做）

拿到网址后，逐项确认功能正常：

1. 打开首页 `https://你的域名/`，应看到"演员排期表排版工具"页面，配色卡片正常显示 8 款主题。
2. 输入"沈育奇"点查询排期，应能列出上/本/下月三个选项。
3. 选一个月份与配色，点「开始排版」，应能排版并预览。
4. 上传一张测试底图，再排版一次，确认底图以半透明叠加生效。

如果第 2 步抓取失败，多半是平台出口 IP 被 saoju.net 限制，需换平台或给请求加代理（进阶）。如果第 3 步排版导出时报字体或浏览器错误，检查 Dockerfile 里的 `fonts-noto-cjk` 是否装成功、Playwright 镜像版本是否与 requirements.txt 一致。

---

## 七、绑定你自己的域名（可选）

各平台都支持绑定自有域名（如 `paiban.你的域名.com`）：

- Render：服务页 → Settings → Custom Domains → Add Custom Domain，按提示在你的 DNS 服务商添加 CNAME 记录。
- Railway：服务 → Settings → Networking → Custom Domain。
- Fly.io：`fly certs create 你的域名` 并按提示配置 DNS。

绑定后即可用完全属于你的域名访问，且不携带任何 sharecode 参数。

---

## 八、本地先用 Docker 测试（可选）

有 Docker 的话，可先在本地验证整套包能跑通再上云：

```bash
cd saoju-calendar-deploy
docker build -t paiban .
docker run -d -p 8080:8080 --name paiban paiban
# 打开 http://localhost:8080 测试
```

本地测试通过后，把本目录推到 GitHub 交给云平台构建即可。

---

## 九、和当前链接的关系

部署到你自己的平台后，会得到一个新的干净网址。它与当前的 `paiqitu.app.workbuddy.host/?sharecode=...` 是两套独立部署，互不冲突——你可以两个都保留，也可以只用新的那个。当前链接不受本次部署影响，仍可正常使用。

需要下线当前 WorkBuddy 链接时，直接在对话里告诉我即可。
