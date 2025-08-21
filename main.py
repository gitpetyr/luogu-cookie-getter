import asyncio
from ddddocr import DdddOcr
from sys import platform
from fastapi import FastAPI
import DrissionPage
import uvicorn,sys,time,json
from pyvirtualdisplay import Display

display = Display(visible=0,size=(1200, 800))
display.start()

# if platform == "linux" or platform == "linux2":
#     platformIdentifier = "X11; Linux x86_64"
# elif platform == "darwin":
#     platformIdentifier = "Macintosh; Intel Mac OS X 10_15_7"
# elif platform == "win32":
#     platformIdentifier = "Windows NT 10.0; Win64; x64"

# User_agent = f"Mozilla/5.0 ({platformIdentifier}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

# 控制并发数量
semaphore = asyncio.Semaphore(5)

# DdddOcr 实例，全局共享，它是线程安全的
cl = DdddOcr(show_ad=False)

app = FastAPI()

def ocr(image: bytes):
    """同步的 OCR 识别函数"""
    return cl.classification(image)

def getTurnstileToken(page : DrissionPage.ChromiumPage):
    page.run_js("try { turnstile.reset() } catch(e) { }")

    turnstileResponse = None

    for i in range(0, 15):
        try:
            turnstileResponse = page.run_js("try { return turnstile.getResponse() } catch(e) { return null }")
            if turnstileResponse:
                print("Cloudflare Turnstile accepted.")
                return turnstileResponse
            
            challengeSolution = page.ele("@name=cf-turnstile-response")
            challengeWrapper = challengeSolution.parent()
            challengeIframe = challengeWrapper.shadow_root.ele("tag:iframe")
            
            challengeIframe.run_js("""
window.dtp = 1
function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

// old method wouldn't work on 4k screens

let screenX = getRandomInt(800, 1200);
let screenY = getRandomInt(400, 600);

Object.defineProperty(MouseEvent.prototype, 'screenX', { value: screenX });

Object.defineProperty(MouseEvent.prototype, 'screenY', { value: screenY });
                        """)
            
            challengeIframeBody = challengeIframe.ele("tag:body").shadow_root
            challengeButton = challengeIframeBody.ele("tag:input")
            challengeButton.click()
            print("Cloudflare Turnstile passing.")
        except:
            print("Cloudflare Turnstile failed.")
        time.sleep(0.8)
    page.refresh()
    raise Exception("failed to solve turnstile")

def _get_luogu_cookie(username: str, password: str) -> dict:
    """
    同步的浏览器操作函数。
    注意：每个任务都应该创建一个新的 Page 对象来保证隔离性。
    """
    co = DrissionPage.ChromiumOptions()
    co.auto_port(True) 
    # co.set_user_agent(f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
    # co.set_user_agent(User_agent)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.headless(True)
    # co.set_user_agent()
    co.add_extension("turnstilePatch")
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
        page.wait(0.4)
        page.wait.doc_loaded()
        page.wait(0.4,0.6)

        cookies = page.cookies()
        res = {dic["name"]: dic["value"] for dic in cookies}
        return res
    finally:
        # 确保浏览器页面在任务结束后关闭
        page.quit()

def _get_vjudge_cookie(username: str, password: str) -> dict:
    """
    同步的浏览器操作函数。
    注意：每个任务都应该创建一个新的 Page 对象来保证隔离性。
    """
    co = DrissionPage.ChromiumOptions()
    co.auto_port(True) 
    co.add_extension("turnstilePatch")
    # co.headless(True)
    # co.set_user_agent(f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
    # co.set_user_agent(User_agent)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    page = DrissionPage.ChromiumPage(co)
    
    try:
        page.get("https://vjudge.net/")
        page.wait.doc_loaded(timeout=10, raise_err=True)
        page.wait(0.3,0.4)
        # try:
        #     getTurnstileToken(page)
        # except Exception:
        #     pass

        page.ele("@class:login").click()

        page.wait.ele_displayed("@id=login-username", timeout=4, raise_err=True)
        page.wait(0.2)

        page.ele("@id=login-username").input(username)
        page.ele("@id=login-password").input(password)
        page.wait(0.2,0.4)

        page.ele("@id=btn-login").click()
        # page.wait.ele_displayed("@id=userNameDropdown",timeout=3,raise_err=True)
        #userNameDropdown
        try:
            st=page.wait.ele_displayed("@name=cf-turnstile-response",timeout=3,raise_err=True)
            print(st)
            try:
                getTurnstileToken(page)
                page.wait(0.4)
                page.ele("@id=btn-login").click()
                page.wait.load_start()
                page.wait.doc_loaded()
                page.wait(0.5)
            except Exception as e:
                print("Pass cloudflare failed: "+str(e))
        except Exception as e:
            print("No cloudflare.")

        page.refresh()
        page.wait.doc_loaded()

        # try:
        #     getTurnstileToken(page)
        # except Exception:
        #     pass

        cookies = page.cookies() # JSESSIONID JSESSIONlD JSESSlONID
        res = {dic["name"]: dic["value"] for dic in cookies}
        return res
    finally:
        # 确保浏览器页面在任务结束后关闭
        page.quit()

def _get_becoder_cookie(username: str, password: str) -> dict:
    """
    同步的浏览器操作函数。
    注意：每个任务都应该创建一个新的 Page 对象来保证隔离性。
    """
    co = DrissionPage.ChromiumOptions()
    co.auto_port(True) 
    # co.set_user_agent(f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
    # co.set_user_agent(User_agent)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.headless(True)
    # co.set_user_agent()
    co.add_extension("turnstilePatch")
    page = DrissionPage.ChromiumPage(co)
    
    try:
        page.get("https://www.becoder.com.cn/login?url=%2Findex")
        page.wait.doc_loaded(timeout=2, raise_err=True)

        page.ele("@id=username").input(username)
        page.ele("@id=password").input(password)

        page.wait.ele_displayed("@class=verification-code",timeout=2,raise_err=True)

        # 增加一个短暂的等待，确保验证码元素完全加载
        page.wait(0.7,0.8) 
        
        captcha_img = page.ele("@class=verification-code")
        print(captcha_img)
        img = captcha_img.get_screenshot(as_bytes='png')
        # open("xxx.png","wb").write(img)
        # print(captcha_img)
        captcha_input = page.ele("@id=captcha")
        captcha_code = ocr(img)
        print(f"User: {username}, Captcha: {captcha_code}")
        
        # open("xxx.png","wb").write(captcha_img.src(base64_to_bytes=True)) # 用于调试
        
        captcha_input.input(captcha_code)
        page.ele("@id=login-btn").click()

        try :
            page.wait.url_change("https://www.becoder.com.cn/index",timeout=4,raise_err=True)
        except Exception:
            cookies = page.cookies() #session_token
            res = {dic["name"]: dic["value"] for dic in cookies}
            return res
        # 等待页面跳转和加载完成
        page.wait.doc_loaded()
        page.wait(0.4,0.6)

        cookies = page.cookies() #session_token
        res = {dic["name"]: dic["value"] for dic in cookies}
        return res
    finally:
        # 确保浏览器页面在任务结束后关闭
        page.quit()

def _get_loj_local_storage(username: str, password: str) -> dict:
    """
    同步的浏览器操作函数。
    注意：每个任务都应该创建一个新的 Page 对象来保证隔离性。
    """
    co = DrissionPage.ChromiumOptions()
    co.auto_port(True) 
    # co.set_user_agent(f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
    # co.set_user_agent(User_agent)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.headless(True)
    # co.set_user_agent()
    co.add_extension("turnstilePatch")
    page = DrissionPage.ChromiumPage(co)
    
    try:
        page.get("https://loj.ac/login?loginRedirectUrl=%2F")
        page.wait.doc_loaded(timeout=2, raise_err=True)

        page.ele("@autocomplete=username").input(username)
        page.ele("@autocomplete=current-password").input(password+"\n\n")
        
        try:
            page.wait.url_change("https://loj.ac/login",exclude=True,timeout=4,raise_err=True)
        except Exception:
            local_storage = page.local_storage("appState")
            return local_storage
        page.wait.doc_loaded()
        page.wait(0.4,0.5)

        local_storage = page.local_storage("appState")
        return local_storage
    finally:
        # 确保浏览器页面在任务结束后关闭
        page.quit()

def _get_atcoder_cookie(username: str, password: str) -> dict:
    """
    同步的浏览器操作函数。
    注意：每个任务都应该创建一个新的 Page 对象来保证隔离性。
    """
    co = DrissionPage.ChromiumOptions()
    co.auto_port(True) 
    co.add_extension("turnstilePatch")
    # co.headless(True)
    # co.set_user_agent(f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
    # co.set_user_agent(User_agent)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    page = DrissionPage.ChromiumPage(co)
    
    try:
        page.get("https://atcoder.jp/login?continue=https%3A%2F%2Fatcoder.jp%2F")
        page.wait.doc_loaded(timeout=10, raise_err=True)
        page.wait(0.3,0.4)

        page.wait.ele_displayed("@id=username",timeout=3,raise_err=True)

        page.ele("@id=username").input(username,clear=True)
        page.ele("@id=password").input(password,clear=True)
        page.wait(0.3,0.4)

        try :
            getTurnstileToken(page)
        except Exception:
            pass
        
        page.wait(0.3,0.4)

        page.ele("@id=submit").click()

        try:
            page.wait.url_change("https://atcoder.jp/login",exclude=True,timeout=5,raise_err=True)
        except Exception:
            return None
        
        page.wait.doc_loaded(timeout=10,raise_err=True)
        page.refresh()
        page.wait.doc_loaded(timeout=10,raise_err=True)

        cookies = page.cookies()
        res = {dic["name"]: dic["value"] for dic in cookies}
        return res
    finally:
        # 确保浏览器页面在任务结束后关闭
        page.quit()

def _get_codeforces_cookie(username: str, password: str) -> dict:
    """
    同步的浏览器操作函数。
    注意：每个任务都应该创建一个新的 Page 对象来保证隔离性。
    """
    co = DrissionPage.ChromiumOptions()
    co.auto_port(True) 
    co.add_extension("turnstilePatch")
    # co.headless(True)
    # co.set_user_agent(f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
    # co.set_user_agent(User_agent)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    page = DrissionPage.ChromiumPage(co)
    
    try:
        page.get("https://codeforces.com/enter?back=%2F")
        page.wait.doc_loaded(timeout=10, raise_err=True)
        page.wait(0.3,0.4)
        # try:
        #     getTurnstileToken(page)
        # except Exception:
        #     pass

        try :
            getTurnstileToken(page)
        except Exception:
            pass
        page.wait.ele_displayed("@id=finalize-button",timeout=5,raise_err=True)
        page.ele("@id=finalize-button").click()
        page.wait.ele_displayed("@id=handleOrEmail",timeout=20,raise_err=True)

        page.ele("@id=handleOrEmail").input(username,clear=True)
        page.ele("@id=password").input(password,clear=True)
        page.ele("@id=remember").check()
        page.wait(0.2,0.3)

        page.ele("@class=submit").click()
        try:
            page.wait.url_change("https://codeforces.com/enter",exclude=True,timeout=7,raise_err=True)
        except Exception:
            return None

        # page.wait.ele_displayed("@id=userNameDropdown",timeout=3,raise_err=True)
        #userNameDropdown

        page.refresh()
        page.wait.doc_loaded()

        # try :
        #     getTurnstileToken(page)
        # except Exception:
        #     pass

        # try:
        #     getTurnstileToken(page)
        # except Exception:
        #     pass
        try :
            page.ele("@href:enter")
        except Exception:
            return None

        cookies = page.cookies()
        res = {dic["name"]: dic["value"] for dic in cookies}
        return res
    finally:
        # 确保浏览器页面在任务结束后关闭
        page.quit()

@app.post("/get_luogu_cookie")
async def getluogucookie(username: str, password: str):
    # 2. 将 FastAPI 路由改为 async def，使其成为异步函数
    print(f"Received request for luogu user: {username}. Waiting for a slot...")
    
    # 3. 使用 async with 语法来获取信号量，执行完毕后会自动释放
    async with semaphore:
        print(f"Slot acquired for luogu user: {username}. Starting browser task...")
        try:
            # 4. 使用 asyncio.to_thread 将同步的阻塞函数放到线程池中运行
            # 这可以防止浏览器操作阻塞 FastAPI 的主事件循环
            res = await asyncio.to_thread(_get_luogu_cookie, username, password)
            
            # 检查登录是否成功
            if "_uid" not in res or str(res.get("_uid")) == "0":
                print(f"Login failed for luogu user: {username}.")
                return {"status": "failed", "error": "Login failed, please check credentials or captcha.", "result": res}
            
            print(f"Successfully got cookie for luogu user: {username}.")
            return {"status": "success", "result": res}

        except Exception as e:
            print(f"An error occurred for luogu user {username}: {e}")
            return {"status": "failed", "error": str(e), "result": None}

@app.post("/get_vjudge_cookie")
async def get_vjudge_cookie(username: str, password: str):
    # 2. 将 FastAPI 路由改为 async def，使其成为异步函数
    print(f"Received request for vjudge user: {username}. Waiting for a slot...")
    
    # 3. 使用 async with 语法来获取信号量，执行完毕后会自动释放
    async with semaphore:
        print(f"Slot acquired for vjudge user: {username}. Starting browser task...")
        try:
            # 4. 使用 asyncio.to_thread 将同步的阻塞函数放到线程池中运行
            # 这可以防止浏览器操作阻塞 FastAPI 的主事件循环
            res = await asyncio.to_thread(_get_vjudge_cookie, username, password)
            
            # 检查登录是否成功
            if "JSESSIONlD" not in res or str(res.get("JSESSIONlD")) == "":
                print(f"Login failed for vjudge user: {username}.")
                return {"status": "failed", "error": "Login failed, please check credentials or captcha.", "result": res}
            
            print(f"Successfully got cookie for vjudge user: {username}.")
            return {"status": "success", "result": res}

        except Exception as e:
            print(f"An error occurred for vjudge user {username}: {e}")
            return {"status": "failed", "error": str(e), "result": None}
        
@app.post("/get_becoder_cookie")
async def get_becoder_cookie(username: str, password: str):
    # 2. 将 FastAPI 路由改为 async def，使其成为异步函数
    print(f"Received request for becoder user: {username}. Waiting for a slot...")
    
    # 3. 使用 async with 语法来获取信号量，执行完毕后会自动释放
    async with semaphore:
        print(f"Slot acquired for becoder user: {username}. Starting browser task...")
        try:
            # 4. 使用 asyncio.to_thread 将同步的阻塞函数放到线程池中运行
            # 这可以防止浏览器操作阻塞 FastAPI 的主事件循环
            res = await asyncio.to_thread(_get_becoder_cookie, username, password)
            
            # 检查登录是否成功
            if "session_token" not in res or str(res.get("session_token")) == "":
                print(f"Login failed for becoder user: {username}.")
                return {"status": "failed", "error": "Login failed, please check credentials or captcha.", "result": res}
            
            print(f"Successfully got cookie for becoder user: {username}.")
            return {"status": "success", "result": res}

        except Exception as e:
            print(f"An error occurred for becoder user {username}: {e}")
            return {"status": "failed", "error": str(e), "result": None}

@app.post("/getloj_local_stor")
async def getloj_local_storage(username: str, password: str):
    # 2. 将 FastAPI 路由改为 async def，使其成为异步函数
    print(f"Received request for loj user: {username}. Waiting for a slot...")
    
    # 3. 使用 async with 语法来获取信号量，执行完毕后会自动释放
    async with semaphore:
        print(f"Slot acquired for loj user: {username}. Starting browser task...")
        try:
            # 4. 使用 asyncio.to_thread 将同步的阻塞函数放到线程池中运行
            # 这可以防止浏览器操作阻塞 FastAPI 的主事件循环
            res = await asyncio.to_thread(_get_loj_local_storage, username, password)

            if res != None:
                res = json.loads(res)
            else:
                print(f"Login failed for loj user: {username}.")
                return {"status": "failed", "error": "Login failed, please check credentials.", "result": res}

            # 检查登录是否成功
            if "token" not in res or res["token"] == None or res["token"] == "":
                print(f"Login failed for loj user: {username}.")
                return {"status": "failed", "error": "Login failed, please check credentials.", "result": res}
            
            print(f"Successfully got local_storage for loj user: {username}.")
            return {"status": "success", "result": res}

        except Exception as e:
            print(f"An error occurred for loj user {username}: {e}")
            return {"status": "failed", "error": str(e), "result": None}

@app.post("/get_codeforces_cookie")
async def get_codeforces_cookie(username: str, password: str):
    # 2. 将 FastAPI 路由改为 async def，使其成为异步函数
    print(f"Received request for codeforces user: {username}. Waiting for a slot...")
    
    # 3. 使用 async with 语法来获取信号量，执行完毕后会自动释放
    async with semaphore:
        print(f"Slot acquired for codeforces user: {username}. Starting browser task...")
        try:
            # 4. 使用 asyncio.to_thread 将同步的阻塞函数放到线程池中运行
            # 这可以防止浏览器操作阻塞 FastAPI 的主事件循环
            res = await asyncio.to_thread(_get_codeforces_cookie, username, password)
            
            # 检查登录是否成功
            if res == None or "JSESSIONID" not in res or str(res.get("JSESSIONID")) == "":
                print(f"Login failed for codeforces user: {username}.")
                return {"status": "failed", "error": "Login failed, please check credentials or captcha.", "result": res}
            
            print(f"Successfully got cookie for codeforces user: {username}.")
            return {"status": "success", "result": res}

        except Exception as e:
            print(f"An error occurred for codeforces user {username}: {e}")
            return {"status": "failed", "error": str(e), "result": None}

@app.post("/get_atcoder_cookie")
async def get_atcoder_cookie(username: str, password: str):
    # 2. 将 FastAPI 路由改为 async def，使其成为异步函数
    print(f"Received request for atcoder user: {username}. Waiting for a slot...")
    
    # 3. 使用 async with 语法来获取信号量，执行完毕后会自动释放
    async with semaphore:
        print(f"Slot acquired for atcoder user: {username}. Starting browser task...")
        try:
            # 4. 使用 asyncio.to_thread 将同步的阻塞函数放到线程池中运行
            # 这可以防止浏览器操作阻塞 FastAPI 的主事件循环
            res = await asyncio.to_thread(_get_atcoder_cookie, username, password)
            
            # 检查登录是否成功
            if res == None or "REVEL_SESSION" not in res or str(res.get("REVEL_SESSION")) == "":
                print(f"Login failed for atcoder user: {username}.")
                return {"status": "failed", "error": "Login failed, please check credentials or captcha.", "result": res}
            
            print(f"Successfully got cookie for atcoder user: {username}.")
            return {"status": "success", "result": res}

        except Exception as e:
            print(f"An error occurred for atcoder user {username}: {e}")
            return {"status": "failed", "error": str(e), "result": None}


# 用于直接运行此文件
if __name__ == "__main__":
# #     # 建议使用 uvicorn 命令行来启动，例如: uvicorn your_file_name:app --workers 1 --host 0.0.0.0 --port 8000
    uvicorn.run(app, workers=1, host="0.0.0.0", port=8000)
