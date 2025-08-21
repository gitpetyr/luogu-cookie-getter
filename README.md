# luogu-cookie-getter
luogu-cookie-getter API

## 项目简介

本项目是一个基于 FastAPI 和 DrissionPage 的 **API 服务**，旨在自动化获取洛谷（Luogu）和 VJudge 平台的登录 Cookies。它利用无头浏览器技术模拟用户登录流程，并能通过各种人机验证，最终返回登录成功后的 Cookies。

### 核心功能

  * **自动化登录**：模拟用户输入用户名、密码和验证码，完成洛谷和 VJudge 的登录过程。
  * **验证码识别**：集成 DdddOcr，能够自动识别常见的图片验证码。
  * **并发控制**：使用 `asyncio.Semaphore` 控制浏览器实例的并发数量，避免因资源耗尽导致服务崩溃。
  * **异步处理**：通过 `asyncio.to_thread` 将同步的浏览器操作放入单独的线程中执行，确保 FastAPI 的主事件循环不会被阻塞，从而提升 API 的响应性能和吞吐量。

## API 调用指南

本项目提供了两个主要 API 端点，分别用于获取洛谷和 VJudge 的 Cookies。

### 1\. 获取洛谷（Luogu）Cookies

该 API 用于通过用户名和密码登录洛谷，并返回登录成功后的 Cookies。

  * **URL**：`/getluogucookie`
  * **方法**：`POST`
  * **参数**：
      * `username`（string）：洛谷账号的用户名。
      * `password`（string）：洛谷账号的密码。
  * **请求示例**：

<!-- end list -->

```
curl -X POST "http://127.0.0.1:8000/getluogucookie?username=your_username&password=your_password"
```

  * **成功响应**：

<!-- end list -->

```json
{
  "status": "success",
  "result": {
    "C3VK": "...",
    "__client_id": "...",
    "_uid": "..."
  }
}
```

  * **失败响应**：

<!-- end list -->

```json
{
  "status": "failed",
  "error": "Login failed, please check credentials or captcha.",
  "result": null
}
```

### 2\. 获取 VJudge Cookies

该 API 用于通过用户名和密码登录 VJudge，并返回登录成功后的 Cookies。

  * **URL**：`/getvjudgecookie`
  * **方法**：`POST`
  * **参数**：
      * `username`（string）：VJudge 账号的用户名。
      * `password`（string）：VJudge 账号的密码。
  * **请求示例**：

<!-- end list -->

```
curl -X POST "http://127.0.0.1:8000/getvjudgecookie?username=your_username&password=your_password"
```

  * **成功响应**：

<!-- end list -->

```json
{
  "status": "success",
  "result": {
    "JSESSIONID": "...",
    "JSESSIONlD": "...",
    "JSESSlONID": "...",
    ...
  }
}
```

  * **失败响应**：

<!-- end list -->

```json
{
  "status": "failed",
  "error": "Login failed, please check credentials or captcha.",
  "result": null
}
```

-----

### 注意事项

  * **并发限制**：项目默认设置了 **5** 个并发任务，以平衡性能和资源消耗。如果需要调整，请修改代码中的 `semaphore` 变量。
  * **环境依赖**：运行本项目需要安装 DrissionPage 及其依赖的 Chromium 浏览器，以及 DdddOcr 库。
  * **虚拟显示器**：代码中使用了 `pyvirtualdisplay`，以确保在无头（Headless）环境下，例如在 Linux 服务器上，也能正常运行浏览器。

希望这份 README 对您有所帮助！
