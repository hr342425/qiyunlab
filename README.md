# qiyunlab - 轻量邮件发送服务

部署在云服务器上的轻量邮箱发送服务。前端通过 HTTP 调用本服务，使用 163 SMTP
将邮件发送到指定邮箱。

## 功能

- 纯 Python 标准库实现，无第三方依赖，镜像极简
- HTTP 接口：`GET /health`、`POST /send`
- API Key 鉴权，防止开放转发被滥用
- Docker 化 + 一键部署（参考 yiduo 部署方案，国内网络使用 githubfast 加速）

## 快速开始（本地）

```bash
# 配置环境变量
cp .env.example .env

# 直接运行（无需 Docker）
python3 app/mailservice.py
```

## 部署

- [一键部署文档](docs/deployment.md)
- 方式：代码 push 到 GitHub 后，服务器执行 `./deploy/deploy.sh` 自动拉代码 + 重建容器 + 健康检查

## 调用示例

```bash
curl -X POST http://<服务器IP>:8080/send \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: <你的密钥>' \
  -d '{"subject":"测试","content":"你好","html":false}'
```

## 安全说明

所有密钥（SMTP 授权码、API Key 等）存放在服务器上的 `.env`（权限 600），
**不要**提交到 git 仓库。仓库内只保留 `.env.example` 占位模板。
