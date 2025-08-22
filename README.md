# Luogu Cookie Getter API

Luogu Cookie Getter 是一个基于 FastAPI 的自动化服务，用于通过浏览器自动化登录各大网站，获取用户认证 Cookie 或 Local Storage 数据。支持并发控制、验证码识别（通过 OCR）以及 Cloudflare Turnstile 处理。

## 功能概述

本服务通过模拟浏览器操作，自动完成登录流程，获取用户认证信息（Cookie 或 Local Storage）。支持以下网站：

- 洛谷 (Luogu)
- VJudge
- BeCoder
- LibreOJ (LOJ)
- Codeforces
- AtCoder
- USACO
- UOJ
- QOJ

## 支持的网站及操作说明

以下是支持的在线评测平台及其对应的 API 端点和操作说明：

| 平台          | API 端点                      | 自动执行的操作                                                     |
| ------------- | ----------------------------- | ------------------------------------------------------------ |
| 洛谷 (Luogu)  | `POST /get_luogu_cookie`      | 访问登录页面，输入用户名和密码，识别验证码并提交，获取认证 Cookie（包含 `_uid`）。 |
| VJudge        | `POST /get_vjudge_cookie`     | 访问登录页面，处理可能的 Cloudflare 挑战，输入用户名和密码，获取 Cookie（包含 `JSESSIONlD`）。 |
| BeCoder       | `POST /get_becoder_cookie`    | 访问登录页面，输入用户名和密码，识别验证码并提交，获取 Cookie（包含 `session_token`）。 |
| LibreOJ (LOJ) | `POST /get_loj_local_stor`    | 访问登录页面，输入用户名和密码，获取 Local Storage 数据（`appState` 中的 `token`）。 |
| Codeforces    | `POST /get_codeforces_cookie` | 访问登录页面，处理 Cloudflare 挑战，输入用户名和密码，获取 Cookie（包含 `JSESSIONID`）。 |
| AtCoder       | `POST /get_atcoder_cookie`    | 访问登录页面，处理 Cloudflare 挑战，输入用户名和密码，获取 Cookie（包含 `REVEL_SESSION`）。 |
| USACO         | `POST /get_usaco_cookie`      | 访问登录页面，输入用户名和密码，提交后获取 Cookie（包含 `PHPSESSID`）。 |
| UOJ           | `POST /get_uoj_cookie`        | 访问登录页面，输入用户名和密码，提交后获取 Cookie（包含 `UOJSESSID` 和 `uoj_remember_token`）。 |
| QOJ           | `POST /get_qoj_cookie`        | 访问登录页面，输入用户名和密码，提交后获取 Cookie（包含 `UOJSESSID` 和 `uoj_remember_token`）。 |

**注意**：

- 每个平台的登录操作都会验证 Cookie 或 Local Storage 的有效性，确保登录成功。
- 如果登录失败（例如验证码错误或凭据无效），API 将返回错误信息。
- 服务使用 OCR（DdddOcr）处理验证码，使用 DrissionPage 模拟浏览器操作。

## Docker 部署教程

本服务提供 Docker 镜像 `zhongxiaoma/luogu-cookie-getter:latest`，可快速部署。

### 前置条件

- 安装 Docker（推荐最新版本）。
- 确保 Docker 守护进程正在运行。
- 服务器有足够的内存（建议 2GB 内存？）以支持浏览器自动化。

### 部署步骤

- **拉取 Docker 镜像**

   ```bash
   docker pull zhongxiaoma/luogu-cookie-getter:latest
   ```

- **运行 Docker 容器**

   ```bash
   docker run -d -p 8000:8000 --name luogu-cookie-getter zhongxiaoma/luogu-cookie-getter:latest
   ```

   - `-d`: 后台运行容器。
   - `-p 8000:8000`: 映射容器内的 8000 端口到宿主机的 8000 端口，`宿主机端口 : 容器内端口（8000）`。
   - `--name`: 指定容器名称。

- **验证服务**

   使用 `curl` 调用 API 测试即可：
  
   ```bash
   curl -X POST "http://localhost:8000/get_luogu_cookie" \
   -H 'accept: application/json' \
   -H 'Content-Type: application/json' \
   -d '{"username": "your_luogu_username", "your_luogu_password": "your_password"}'
   ```

   如果服务运行正常，应该可以看到 `"status": "success"`

- **停止和删除容器（可选）**

   ```bash
   docker stop luogu-cookie-getter
   docker rm luogu-cookie-getter
   ```


## API 文档

> 参考：
> - http://your-host:your-port/redoc
> - http://your-host:your-port/docs
> - http://your-host:your-port/openapi.json

### 请求格式

所有 API 端点均接受 `POST` 请求，请求体为 JSON 格式，包含以下字段：

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

### 响应格式

响应为 JSON 格式，包含以下字段：

- `status`: 字符串，表示操作结果（`"success"` 或 `"failed"`）。
- `result`: 对象，包含获取到的 Cookie 或 Local Storage 数据（成功时返回，失败时可能为 `null` 或部分数据）。
- `error`: 字符串，错误信息（成功时为 `null`，失败时提供错误原因）。

示例响应（成功）：

```json
{
  "status": "success",
  "result": {
    "_uid": "12345",
    "...": "and anything more"
  },
  "error": null
}
```

示例响应（失败）：

```json
{
  "status": "failed",
  "result": null,
  "error": "Login failed, please check credentials or captcha."
}
```

### API 端点详情

1. **洛谷 Cookie 获取**

   - **端点**: `POST /get_luogu_cookie`

   - **描述**: 登录洛谷，处理验证码并返回 Cookie。

   - **请求示例**:

     ```json
     {
       "username": "user123",
       "password": "pass123"
     }
     ```

   - **响应示例**:

     ```json
     {
       "status": "success",
       "result": {
         "_uid": "12345",
         "session_id": "abc123..."
       },
       "error": null
     }
     ```

2. **VJudge Cookie 获取**

   - **端点**: `POST /get_vjudge_cookie`
   - **描述**: 登录 VJudge，处理 Cloudflare 挑战并返回 Cookie。
   - **请求/响应格式同上**。

3. **BeCoder Cookie 获取**

   - **端点**: `POST /get_becoder_cookie`
   - **描述**: 登录 BeCoder，处理验证码并返回 Cookie。
   - **请求/响应格式同上**。

4. **LibreOJ Local Storage 获取**

   - **端点**: `POST /get_loj_local_stor`
   - **描述**: 登录 LibreOJ，返回 Local Storage 数据（`appState`）。
   - **请求/响应格式同上**。

5. **Codeforces Cookie 获取**

   - **端点**: `POST /get_codeforces_cookie`
   - **描述**: 登录 Codeforces，处理 Cloudflare 挑战并返回 Cookie。
   - **请求/响应格式同上**。

6. **AtCoder Cookie 获取**

   - **端点**: `POST /get_atcoder_cookie`
   - **描述**: 登录 AtCoder，处理 Cloudflare 挑战并返回 Cookie。
   - **请求/响应格式同上**。

7. **USACO Cookie 获取**

   - **端点**: `POST /get_usaco_cookie`
   - **描述**: 登录 USACO，返回 Cookie。
   - **请求/响应格式同上**。

8. **UOJ Cookie 获取**

   - **端点**: `POST /get_uoj_cookie`
   - **描述**: 登录 UOJ，返回 Cookie。
   - **请求/响应格式同上**。

9. **QOJ Cookie 获取**

   - **端点**: `POST /get_qoj_cookie`
   - **描述**: 登录 QOJ，返回 Cookie。
   - **请求/响应格式同上**。

### 注意事项

- **并发控制**: 服务默认限制 6 个并发任务（通过 `asyncio.Semaphore`），可根据服务器性能调整。
- **依赖**: 镜像已包含所有依赖（如 DrissionPage、DdddOcr、Chromium 浏览器等）。
- **日志**: 服务会在控制台输出日志，记录登录尝试、验证码识别和错误信息。
- **网络**: 确保服务器网络可访问目标网站，且未被屏蔽。

## 使用示例

以下是使用 `curl` 调用 API 的示例：

```bash
curl -X POST "http://localhost:8000/get_luogu_cookie" \
-H 'accept: application/json' \
-H 'Content-Type: application/json' \
-d '{"username": "your_username", "password": "your_password"}'
```

返回结果：

```json
{
  "status": "success",
  "result": {
    "_uid": "123456",
    "somethings": "1145"
  },
  "error": null
}
```

## 常见问题

1. **登录失败怎么办？**
   - 检查用户名和密码是否正确。
   - 验证码识别可能失败，多次重试或检查 OCR 模块（DdddOcr）配置。
   - 如果涉及 Cloudflare 挑战，确保 `turnstilePatch` 扩展正确加载。
   - Cloudflare 可能存在 has been blocked 的情况。

2. **如何调试？**
   - 查看容器日志：`docker logs luogu-cookie-getter`。
