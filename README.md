# qiyunlab - 轻量邮件发送服务

部署在云服务器上的轻量邮箱发送服务。前端通过 HTTP 调用本服务，使用 163 SMTP
将邮件发送到指定邮箱。

## 功能

- 纯 Python 标准库实现，无第三方依赖，镜像极简
- HTTP 接口：`GET /health`、`POST /send`、`POST /appointment`
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
curl -X POST http://<服务器IP>/appointment \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: <你的密钥>' \
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

所有密钥（SMTP 授权码、API Key 等）存放在服务器上的 `.env`（权限 600），
**不要**提交到 git 仓库。仓库内只保留 `.env.example` 占位模板。
