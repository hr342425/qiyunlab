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
| `HEALTH_URL` | `http://127.0.0.1:8080/health` | 健康检查地址 |

## 运维命令

```bash
docker compose ps
docker compose logs -f mail
docker compose restart mail
```

## 接口说明

- 健康检查：`GET /health`
- 发送邮件：`POST /send`，请求头 `X-API-Key: <token>`，
  请求体 `{"subject":"标题","content":"正文","html":false}`
- 默认收件人为 `MAIL_RECIPIENT` 指定地址；可在请求体加 `"to": "xxx@example.com"` 临时改收件人。
