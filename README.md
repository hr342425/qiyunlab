# qiyunlab - 官网 + 轻量邮件发送服务

部署在云服务器上的官网与邮件发送服务：Nginx 托管前端静态页面，并把表单请求反代到
内网邮件服务，使用 163 SMTP 将邮件发送到指定邮箱。

## 功能

- 纯 Python 标准库实现，无第三方依赖，镜像极简
- Nginx 托管 qyweb 前端（`frontend/`），并反代 `/appointment` 到内网邮件服务
- HTTP 接口：`GET /health`、`POST /appointment`
- 方案 A 密钥管理：前端不携带密钥，Nginx 服务端注入 `X-API-Key`，后端端口不暴露公网
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

前端通过同源 `/appointment` 提交（Nginx 会自动注入密钥）。直接调用接口时：

```bash
curl -X POST http://<服务器IP>/appointment \
  -H 'Content-Type: application/json' \
  -d '{
    "name":"张三",
    "company":"某某公司",
    "phone":"13800138000",
    "email":"",
    "companyType":"施工企业",
    "requirement":"希望预约产品演示"
  }'
```

`/appointment` 同时兼容原预约表单和新版 nuVision 产品试用申请表单。新版表单
请求示例：

```json
{
  "name": "张三",
  "phone": "13800138000",
  "operatingSystem": "Windows",
  "operatingSystemOther": "",
  "dataSize": "100–500G",
  "deployment": "本地部署",
  "deploymentOther": "",
  "dataTypes": ["BIM 模型数据", "地图数据"],
  "dataTypesOther": "",
  "loadTime": "2–5 分钟",
  "concurrencySupport": "是",
  "usedAccelerator": "否",
  "expectedLoadTime": "1–10 秒",
  "expectedConcurrency": "50–100",
  "acceptableDeployment": ["软硬一体本地部署", "云端部署"],
  "acceptableDeploymentOther": "",
  "departmentPosition": "技术部 / 项目经理",
  "organizationType": "私营企业",
  "industry": "交通、工民建",
  "industryOther": "",
  "systemUses": ["项目设计及优化管理", "项目施工管理"],
  "systemUsesOther": "",
  "privacyAccepted": true
}
```

网页当前没有邮箱字段，因此邮件默认发送到服务器 `.env` 中的 `MAIL_RECIPIENT`
（`qykjlab@163.com`）。如后续增加邮箱输入，可以传 `email` 指定收件邮箱。

所有页面标记 `*` 的字段均由接口校验；选中“其它”时，对应的 `*Other` 字段必须填写。
邮件按基础信息、系统基础、加速需求、辅助筛选四部分生成 HTML 排版。

字段别名也兼容：`姓名`、`单位名称`、`手机号`、`邮箱`、`单位类型`、`需求简述`。

## 安全说明

- 所有密钥（SMTP 授权码、API Key 等）存放在服务器上的 `.env`（权限 600），
  **不要**提交到 git 仓库。仓库内只保留 `.env.example` 占位模板。
- 前端源码中的 API Key 已移除（公开前端携带密钥没有安全意义），改为 Nginx 服务端注入。
- 邮件服务端口不映射到公网，只能经 Nginx 访问。

## 前端同步 + 一键部署（sync-deploy.sh）

日常改前端时，不必手动跑 GitLab→GitHub→服务器三步，一条命令即可完成
「拉取内网 GitLab 前端 → 同步/脱敏到 `frontend/` → 推送 GitHub → SSH 到服务器自动部署」。

```bash
./scripts/sync-deploy.sh            # 完整流程：同步 + 推送 + 部署
./scripts/sync-deploy.sh --dry-run  # 只演练，不提交、不部署
./scripts/sync-deploy.sh --skip-deploy  # 只同步+推送，不部署服务器
```

### 首次使用：配置一次

```bash
mkdir -p ~/.config/qiyunlab
cp scripts/sync.env.example ~/.config/qiyunlab/sync.env
chmod 600 ~/.config/qiyunlab/sync.env
vim ~/.config/qiyunlab/sync.env    # 填入下面的真实值
```

`sync.env` 需要填写的项（不要提交到 git）：

| 变量 | 说明 |
|---|---|
| `GITHUB_TOKEN` | GitHub Personal Access Token（`repo` 权限），推送到 `hr342425/qiyunlab` |
| `GITHUB_USER` | 默认 `hr342425`，一般不用改 |
| `SERVER_HOST` / `SERVER_USER` | 服务器地址 `101.133.159.247` / `root` |
| `SERVER_SSH_PASSWORD` | 服务器 SSH 密码（与 `SERVER_SSH_KEY` 二选一） |
| `SERVER_SSH_KEY` | 或提供 SSH 私钥路径（与密码二选一） |

可选覆盖项（不填用默认值）：
`QYUNLAB_DIR`（本仓库路径）、`GITLAB_URL`、`GITLAB_BRANCH`（默认 `develop`）、
`GITLAB_SSH_KEY`（GitLab SSH 私钥，默认 `~/id_ed25519`）。

### 脚本做了什么

1. 用 GitLab SSH 从内网 `qyweb` 的 `develop` 分支拉取最新前端源码
2. 同步到本仓库 `frontend/`，并做**脱敏**（去掉硬编码公网地址 / API Key）
3. 校验无残留密钥后，提交并推送到 GitHub `main`
4. SSH 到服务器执行 `deploy/deploy.sh` 自动构建、部署、健康检查

> 若只改了后端或 Nginx 配置，直接推送 GitHub 后跑服务器上的
> `cd /opt/qiyunlab/app && ./deploy/deploy.sh` 即可，无需走 sync 脚本。
