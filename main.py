import asyncio
from ddddocr import DdddOcr
from fastapi import FastAPI
import DrissionPage
import uvicorn

# 控制并发数量
semaphore = asyncio.Semaphore(6)

# DdddOcr 实例，全局共享，它是线程安全的
cl = DdddOcr(show_ad=False)

app = FastAPI()

def ocr(image: bytes):
    """同步的 OCR 识别函数"""
    return cl.classification(image)

def _getcookie(username: str, password: str) -> dict:
    """
    同步的浏览器操作函数。
    注意：每个任务都应该创建一个新的 Page 对象来保证隔离性。
    """
    co = DrissionPage.ChromiumOptions()
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.auto_port(True) 
    co.headless(True)
    page = DrissionPage.ChromiumPage(co)
    
    try:
        page.get("https://www.luogu.com.cn/auth/login")
        page.wait.doc_loaded(timeout=10, raise_err=True)

        page.ele("@autocomplete:username").input(username + "\n\n")
        page.wait.ele_displayed("@autocomplete:password", timeout=4, raise_err=True)

        page.ele("@autocomplete:password").input(password)

        # 增加一个短暂的等待，确保验证码元素完全加载
        page.wait(0.8,1) 
        
        captcha_img = page.ele("@src:captcha")
        # print(captcha_img)
        captcha_input = captcha_img.parent().prev()
        captcha_code = ocr(captcha_img.src(base64_to_bytes=True))
        print(f"User: {username}, Captcha: {captcha_code}")
        
        # open("xxx.png","wb").write(captcha_img.src(base64_to_bytes=True)) # 用于调试
        
        captcha_input.input(captcha_code)
        page.ele("@class:solid").click()

        # 等待页面跳转和加载完成
        page.wait(1)
        page.wait.doc_loaded()
        page.wait(1)

        cookies = page.cookies()
        res = {dic["name"]: dic["value"] for dic in cookies}
        return res
    finally:
        # 确保浏览器页面在任务结束后关闭
        page.quit()


@app.post("/getcookie")
async def getcookie(username: str, password: str):
    # 2. 将 FastAPI 路由改为 async def，使其成为异步函数
    print(f"Received request for user: {username}. Waiting for a slot...")
    
    # 3. 使用 async with 语法来获取信号量，执行完毕后会自动释放
    async with semaphore:
        print(f"Slot acquired for user: {username}. Starting browser task...")
        try:
            # 4. 使用 asyncio.to_thread 将同步的阻塞函数放到线程池中运行
            # 这可以防止浏览器操作阻塞 FastAPI 的主事件循环
            res = await asyncio.to_thread(_getcookie, username, password)
            
            # 检查登录是否成功
            if "_uid" not in res or str(res.get("_uid")) == "0":
                print(f"Login failed for user: {username}.")
                return {"status": "failed", "error": "Login failed, please check credentials or captcha.", "result": res}
            
            print(f"Successfully got cookie for user: {username}.")
            return {"status": "success", "result": res}

        except Exception as e:
            print(f"An error occurred for user {username}: {e}")
            return {"status": "failed", "error": str(e), "result": None}

# 用于直接运行此文件
if __name__ == "__main__":
    # 建议使用 uvicorn 命令行来启动，例如: uvicorn your_file_name:app --workers 1 --host 0.0.0.0 --port 8000
    uvicorn.run(app, workers=1, host="0.0.0.0", port=8000)
