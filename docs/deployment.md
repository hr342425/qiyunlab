# qiyunlab 邮件发送服务 - 一键部署

采用与 yiduo 相同的一键部署模式：代码推送到 GitHub 后，在服务器上执行 `deploy/deploy.sh`，
脚本会自动 `git pull` 最新代码并 `docker compose` 重建、重启容器，最后做健康检查。

## 首次部署（一次性准备）

### 1. 安装 Docker

```bash
cd /path/to/qiyunlab
./scripts/install-docker-ubuntu.sh
```

### 2. 克隆仓库

> 国内网络使用 githubfast.com 镜像加速拉取；若使用官方 github.com 请自行替换地址。
> `deploy/deploy.sh` 通过 `git pull origin` 拉代码，因此服务器上仓库的 origin remote 应指向
> 加速地址，避免 pull 超时。若已按官方地址克隆，可手动改 remote：
> ```bash
> cd /opt/qiyunlab/app
> git remote set-url origin https://githubfast.com/hr342425/qiyunlab.git
> ```

```bash
mkdir -p /opt/qiyunlab
git clone https://githubfast.com/hr342425/qiyunlab.git /opt/qiyunlab/app
cd /opt/qiyunlab/app
```

### 3. 创建真实 .env（密钥只存在服务器上，不要提交到 git）

```bash
cp .env.example .env
chmod 600 .env
vim .env   # 填入真实 SMTP 授权码、收件人、API Key
```

### 4. 一键部署

```bash
./deploy/deploy.sh
```

## 日常更新（修改代码后）

1. 本地改代码，push 到 GitHub：
   ```bash
   git add -A && git commit -m "..." && git push
   ```
2. 服务器上执行：
   ```bash
   cd /opt/qiyunlab/app
   ./deploy/deploy.sh
   ```

## 可选参数

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `APP_DIR` | `/opt/qiyunlab/app` | 服务器上仓库所在目录 |
| `BRANCH` | `main` | 要部署的分支 |
| `FORCE_SYNC` | `0` | 设为 `1` 时强制硬重置到远端 |
| `HEALTH_URL` | `http://127.0.0.1/health` | 健康检查地址（经 nginx 80） |

## 运维命令

```bash
docker compose ps
docker compose logs -f mail
docker compose restart mail
```

## 架构与端口

- 公网只暴露 **80 端口**（80 在安全组默认放行）
- Nginx 容器（`qiyunlab-nginx`）监听 80，同时：
  - 托管前端静态页面（`/`）
  - 把 `/appointment`、`/api/appointment` 反代到内网 `mail:8080`，并**服务端注入 `X-API-Key`**
- 邮件服务容器（`qiyunlab-mail`）只在容器内部网络监听 8080，不直接暴露公网
- 安全组只需放行 80 即可，无需放行 8080

## 密钥管理（方案 A）

- 前端**不再携带** API Key，请求改为同源 `/appointment`
- Nginx 反代时由服务端注入 `X-API-Key`（取自 `.env` 的 `MAIL_API_KEY`），公网用户看不到
- 邮件服务仍校验 `X-API-Key`，因此**绕过 Nginx 直连后端端口会因缺少密钥被拒绝**
- Nginx 对 API 路径做限流（同一 IP 限速），防表单被刷

## 接口说明

- 前端：`GET http://<IP>/` 访问官网页面
- 健康检查：`GET http://<IP>/health`
- 预约/试用表单：`POST http://<IP>/appointment`（前端同源调用，无需携带密钥）
- `/api/appointment` 是预约接口的兼容路径
- 预约表单的 `email` 是收件邮箱；不填写时使用 `MAIL_RECIPIENT`，默认发送到 `qykjlab@163.com`
- 新版 nuVision 试用申请通过 `operatingSystem` 字段自动识别，完整请求结构见项目 `README.md`

## HTTPS（Let's Encrypt + 自动续期）

前置条件：**域名必须能通过公网访问到服务器 80 端口**。若域名被云厂商 ICP 备案拦截
（大陆服务器 + 未备案域名返回 403），Let's Encrypt 的 HTTP-01 校验会失败，无法签发证书。

### 首次签发

```bash
cd /opt/qiyunlab/app
sudo bash scripts/setup-letsencrypt-https.sh \
  -d qiyunlab.cc.cd \
  -d www.qiyunlab.cc.cd \
  -m you@example.com
```

脚本会自动：
1. 安装 certbot（snap）
2. 写入 .env（LETSENCRYPT_DIR、CERTBOT_WEBROOT、MAIL_PRIMARY_DOMAIN、MAIL_DOMAINS、MAIL_HTTPS）
3. 先用 HTTP+ACME 配置启动，校验公网 ACME 路径
4. 用 webroot 方式向 Let's Encrypt 签发证书
5. 切换到 HTTPS 配置（80 重定向到 443 + 443 SSL）
6. 写入续期 deploy 钩子（续期后 reload nginx）
7. `certbot renew --dry-run` 自检

### 自动续期

- certbot 安装后自带 systemd 定时器 `certbot.timer`，每天检查，证书到期前自动续期
- 续期成功后触发 `/etc/letsencrypt/renewal-hooks/deploy/reload-qiyunlab-nginx.sh` 重载 nginx

### 手动续期/查看

```bash
sudo certbot renew --dry-run      # 测试续期
sudo certbot certificates          # 查看证书
systemctl status certbot.timer     # 查看续期定时器
```

### Nginx 配置说明

- `deploy/nginx.http.template`：HTTP 阶段（ACME 校验 + 前端 + API 反代）
- `deploy/nginx.https.template`：HTTPS 生产配置（80→443 重定向 + 443 SSL + 前端 + API 反代）
- `scripts/render-nginx.sh`：根据 .env 渲染 `deploy/nginx.conf`（已 gitignore，含密钥，不进仓库）
- `deploy.sh` 会自动调用渲染；`MAIL_HTTPS=1` 时渲染 HTTPS 配置
