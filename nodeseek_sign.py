# -*- coding: utf-8 -*-

import os
import sys
import time
from curl_cffi import requests
from yescaptcha import YesCaptchaSolver, YesCaptchaSolverError
from turnstile_solver import TurnstileSolver, TurnstileSolverError

# 环境变量
CLIENTT_KEY = os.environ.get("CLIENTT_KEY", "")
API_BASE_URL = os.environ.get("API_BASE_URL", "")
NS_RANDOM = os.environ.get("NS_RANDOM", "true")
NS_COOKIE = os.environ.get("NS_COOKIE", "")
USER = os.environ.get("USER", "")
PASS = os.environ.get("PASS", "")
SOLVER_TYPE = os.environ.get("SOLVER_TYPE", "turnstile")
PROXY = os.environ.get("PROXY", "")  # 代理地址，格式如：http://username:password@127.0.0.1:7890 或 http://127.0.0.1:7890
USE_PROXY = os.environ.get("USE_PROXY", "false").lower() == "true"  # 是否使用代理，默认为false

# ---------------- 通知模块动态加载 ----------------
hadsend = False
send = None

def load_send():
    global send
    global hadsend
    cur_path = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(cur_path)
    if os.path.exists(cur_path + "/notify.py"):
        try:
            from notify import send
            hadsend = True
        except:
            print("加载notify.py的通知服务失败，请检查~")
            hadsend = False
    else:
        print("加载通知服务失败,缺少notify.py文件")
        hadsend = False

load_send()

# ---------------- 环境检测函数 ----------------
def detect_environment():
    """检测当前运行环境"""
    # 检测是否在青龙环境中
    ql_path_markers = ['/ql/data/', '/ql/config/', '/ql/', '/.ql/']
    in_ql_env = False
    
    for path in ql_path_markers:
        if os.path.exists(path):
            in_ql_env = True
            break
    
    # 检测是否在GitHub Actions环境中
    in_github_env = os.environ.get("GITHUB_ACTIONS") == "true" or (os.environ.get("GH_PAT") and os.environ.get("GITHUB_REPOSITORY"))
    
    if in_ql_env:
        return "qinglong"
    elif in_github_env:
        return "github"
    else:
        return "unknown"

# ---------------- GitHub 变量写入函数 ----------------
def save_cookie_to_github_var(var_name: str, cookie: str):
    import requests as py_requests
    token = os.environ.get("GH_PAT")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("GH_PAT 或 GITHUB_REPOSITORY 未设置，跳过GitHub变量更新")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    url_check = f"https://api.github.com/repos/{repo}/actions/variables/{var_name}"
    url_create = f"https://api.github.com/repos/{repo}/actions/variables"

    data = {"name": var_name, "value": cookie}

    response = py_requests.patch(url_check, headers=headers, json=data)
    if response.status_code == 204:
        print(f"GitHub: {var_name} 更新成功")
        return True
    elif response.status_code == 404:
        print(f"GitHub: {var_name} 不存在，尝试创建...")
        response = py_requests.post(url_create, headers=headers, json=data)
        if response.status_code == 201:
            print(f"GitHub: {var_name} 创建成功")
            return True
        else:
            print(f"GitHub创建失败: {response.status_code}, {response.text}")
            return False
    else:
        print(f"GitHub设置失败: {response.status_code}, {response.text}")
        return False

# ---------------- 青龙面板变量删除函数 ----------------
def delete_ql_env(var_name: str):
    """删除青龙面板中的指定环境变量"""
    try:
        print(f"查询要删除的环境变量: {var_name}")
        env_result = QLAPI.getEnvs({"searchValue": var_name})
        
        env_ids = []
        if env_result.get("code") == 200 and env_result.get("data"):
            for env in env_result.get("data"):
                if env.get("name") == var_name:
                    env_ids.append(env.get("id"))
        
        if env_ids:
            print(f"找到 {len(env_ids)} 个环境变量需要删除: {env_ids}")
            delete_result = QLAPI.deleteEnvs({"ids": env_ids})
            if delete_result.get("code") == 200:
                print(f"成功删除环境变量: {var_name}")
                return True
            else:
                print(f"删除环境变量失败: {delete_result}")
                return False
        else:
            print(f"未找到环境变量: {var_name}")
            return True
    except (TurnstileSolverError, YesCaptchaSolverError) as e:
        print(f"验证码解析错误: {e}")
        return None
    except Exception as e:
        print(f"删除环境变量异常: {str(e)}")
        return False

# ---------------- 青龙面板变量更新函数 ----------------
def save_cookie_to_ql(var_name: str, cookie: str):
    """保存Cookie到青龙面板环境变量"""
    
    try:
        delete_result = delete_ql_env(var_name)
        if not delete_result:
            print("删除已有变量失败，但仍将尝试创建新变量")
        
        create_data = {
            "envs": [
                {
                    "name": var_name,
                    "value": cookie,
                    "remarks": "NodeSeek签到自动创建",
                    "status": 2  # 启用状态
                }
            ]
        }
        
        create_result = QLAPI.createEnv(create_data)
        if create_result.get("code") == 200:
            print(f"青龙面板环境变量 {var_name} 创建成功")
            return True
        else:
            print(f"青龙面板环境变量创建失败: {create_result}")
            return False
    except Exception as e:
        print(f"青龙面板环境变量操作异常: {str(e)}")
        return False

# ---------------- 统一变量保存函数 ----------------
def save_cookie(var_name: str, cookie: str):
    """根据当前环境保存Cookie到相应位置"""
    env_type = detect_environment()
    
    if env_type == "qinglong":
        print("检测到青龙环境，保存变量到青龙面板...")
        return save_cookie_to_ql(var_name, cookie)
    elif env_type == "github":
        print("检测到GitHub环境，保存变量到GitHub Actions...")
        return save_cookie_to_github_var(var_name, cookie)
    else:
        print("未检测到支持的环境，跳过变量保存")
        return False

# ---------------- 登录逻辑 ----------------
def session_login(user, password, solver_type=SOLVER_TYPE, api_base_url=API_BASE_URL, client_key=CLIENTT_KEY):
    try:
        if solver_type.lower() == "yescaptcha":
            print("正在使用 YesCaptcha 解决验证码...")
            solver = YesCaptchaSolver(
                api_base_url=api_base_url or "https://api.yescaptcha.com",
                client_key=client_key
            )
        else:  # 默认使用 turnstile_solver
            print("正在使用 TurnstileSolver 解决验证码...")
            solver = TurnstileSolver(
                api_base_url=api_base_url,
                client_key=client_key
            )

        token = solver.solve(
            url="https://www.nodeseek.com/signIn.html",
            sitekey="0x4AAAAAAAaNy7leGjewpVyR",
            verbose=True
        )
        if not token:
            print("验证码解析失败")
            return None
    except Exception as e:
        print(f"验证码错误: {e}")
        return None

    session = requests.Session(impersonate="chrome110")
    
    if USE_PROXY and PROXY:
        print(f"使用代理: {PROXY}")
        session.proxies = {"http": PROXY, "https": PROXY}
    
    try:
        session.get("https://www.nodeseek.com/signIn.html")
    except:
        print("访问登录页面失败")

    data = {
        "username": user,
        "password": password,
        "token": token,
        "source": "turnstile"
    }
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        'sec-ch-ua': "\"Not A(Brand\";v=\"99\", \"Microsoft Edge\";v=\"121\", \"Chromium\";v=\"121\"",
        'sec-ch-ua-mobile': "?0",
        'sec-ch-ua-platform': "\"Windows\"",
        'origin': "https://www.nodeseek.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.nodeseek.com/signIn.html",
        'accept-language': "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        'Content-Type': "application/json"
    }
    try:
        response = session.post("https://www.nodeseek.com/api/account/signIn", json=data, headers=headers)
        resp_json = response.json()
        if resp_json.get("success"):
            print("登录成功")
            cookies = session.cookies.get_dict()
            cookie_string = '; '.join([f"{k}={v}" for k, v in cookies.items()])
            return cookie_string
        else:
            print("登录失败:", resp_json.get("message"))
            return None
    except Exception as e:
        print("登录异常:", e)
        print("实际响应内容:", response.text if 'response' in locals() else "没有响应")
        return None

# ---------------- 签到逻辑 ----------------
def sign(ns_cookie, ns_random=NS_RANDOM):
    if not ns_cookie:
        print("请先设置Cookie")
        return "no_cookie", "未设置Cookie"
        
    # 从环境变量读取随机签到设置
    is_random = ns_random.lower() == "true"
    url = f"https://www.nodeseek.com/api/attendance{'?random=true' if is_random else '?random=false'}"
    
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        'sec-ch-ua': "\"Not A(Brand\";v=\"99\", \"Microsoft Edge\";v=\"121\", \"Chromium\";v=\"121\"",
        'sec-ch-ua-mobile': "?0",
        'sec-ch-ua-platform': "\"Windows\"",
        'origin': "https://www.nodeseek.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.nodeseek.com/board",
        'accept-language': "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        'Cookie': ns_cookie
    }

    try:
        start_time = time.time()
        if USE_PROXY and PROXY:
            print(f"使用代理: {PROXY}")
            response = requests.post(url, headers=headers, impersonate="chrome110", proxies={"http": PROXY, "https": PROXY})
        else:
            response = requests.post(url, headers=headers, impersonate="chrome110")
        response_time = round(time.time() - start_time, 2)
        
        response_data = response.json()
        print(response_data)
        message = response_data.get('message', '')
        success = response_data.get('success')
        gain = response_data.get('gain', 0)
        current = response_data.get('current', 0)
        
        # 构建详细的状态信息
        status_info = {
            'response_time': f"{response_time}秒",
            'random_mode': "已开启" if is_random else "已关闭",
            'proxy_status': f"已启用 ({PROXY})" if USE_PROXY and PROXY else "未使用"
        }
        
        status_text = "\n".join([
            f"请求耗时：{status_info['response_time']}",
            f"随机签到：{status_info['random_mode']}",
            f"代理状态：{status_info['proxy_status']}"
        ])
        
        if success is True:
            result_message = f"签到成功！获得{gain}个鸡腿，当前共有{current}个鸡腿\n{status_text}"
            print(result_message)
            return "success", result_message
        elif message and "已完成签到" in message:
            result_message = f"今日已签到：{message}\n{status_text}"
            print(result_message)
            return "already_signed", result_message
        elif message == "USER NOT FOUND" or (response_data.get('status') == 404):
            result_message = f"Cookie已失效：USER NOT FOUND\n{status_text}"
            print(result_message)
            return "invalid_cookie", result_message
        else:
            result_message = f"签到失败，原因：{message}\n{status_text}"
            print(result_message)
            return "fail", result_message
    except requests.exceptions.ProxyError as e:
        error_message = f"代理服务器连接失败：{str(e)}\n代理地址：{PROXY}"
        print(error_message)
        return "error", error_message
    except requests.exceptions.ConnectionError as e:
        error_message = "网络连接失败，请检查网络状态"
        print(error_message)
        return "error", error_message
    except requests.exceptions.Timeout as e:
        error_message = "请求超时，请稍后重试"
        print(error_message)
        return "error", error_message
    except Exception as e:
        error_message = f"发生异常: {str(e)}\n实际响应内容: {response.text if 'response' in locals() else '没有响应'}"
        print(error_message)
        return "error", error_message

# ---------------- 通知格式化 ----------------
def format_notification(title, content):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    # 获取运行环境信息
    env_info = {
        'python_version': sys.version.split()[0],
        'os_platform': sys.platform,
        'proxy_enabled': "是" if USE_PROXY else "否",
        'random_sign': "是" if NS_RANDOM.lower() == "true" else "否"
    }
    
    # 确保content中的换行符是真实的换行符
    content = content.replace('\\n', '\n')
    
    return f"""
╭──────────── NodeSeek 签到通知 ────────────╮
│                                          │
│ 🕒 时间：{current_time}
│ 📌 状态：{title}
│ 📝 详情：{content}
│                                          │
├─────────────── 运行环境 ───────────────────┤
│ 🐍 Python版本：{env_info['python_version']}
│ 💻 操作系统：{env_info['os_platform']}
│ 🌐 启用代理：{env_info['proxy_enabled']}
│ 🎲 随机签到：{env_info['random_sign']}
│                                          │
╰──────────────────────────────────────────╯"""

# ---------------- 主流程 ----------------
if __name__ == "__main__":
    env_type = detect_environment()
    print(f"当前运行环境: {env_type}")
    
    accounts = []

    user = os.getenv("USER")
    password = os.getenv("PASS")
    if user and password:
        accounts.append({"user": user, "password": password})

    index = 1
    while True:
        user = os.getenv(f"USER{index}")
        password = os.getenv(f"PASS{index}")
        if user and password:
            accounts.append({"user": user, "password": password})
            index += 1
        else:
            break
    
    # 读取现有Cookie
    all_cookies = os.getenv("NS_COOKIE", "")
    # 同时支持&分隔符和换行符分隔
    if "&" in all_cookies:
        cookie_list = all_cookies.split("&")
    else:
        cookie_list = all_cookies.splitlines()
    cookie_list = [c.strip() for c in cookie_list if c.strip()]
    
    print(f"共发现 {len(accounts)} 个账户配置，{len(cookie_list)} 个现有Cookie")
    
    if len(cookie_list) > len(accounts):
        cookie_list = cookie_list[:len(accounts)]
    while len(cookie_list) < len(accounts):
        cookie_list.append("")
    
    cookies_updated = False
    
    for i, account in enumerate(accounts):
        account_index = i + 1
        user = account["user"]
        password = account["password"]
        cookie = cookie_list[i] if i < len(cookie_list) else ""
        
        display_user = user if user else f"账号{account_index}"
        
        print(f"\n==== 账号 {display_user} 开始签到 ====")
        
        if cookie:
            result, msg = sign(cookie, NS_RANDOM)
        else:
            result, msg = "invalid", "无Cookie"

        if result in ["success", "already_signed"]:
            print(f"账号 {display_user} 签到成功: {msg}")
            
            if hadsend:
                try:
                    send("NodeSeek 签到", format_notification(f"✓ 签到成功", f"账号 {display_user}: {msg}"))
                except Exception as e:
                    print(f"发送通知失败: {e}")
        else:
            print(f"签到失败或无效: {msg}")
            print("尝试重新登录...")
            if not user or not password:
                print(f"账号 {display_user} 无法登录: 缺少用户名或密码")
                continue
                
            new_cookie = session_login(user, password, SOLVER_TYPE, API_BASE_URL, CLIENTT_KEY)
            if new_cookie:
                print("登录成功，重新签到...")
                result, msg = sign(new_cookie, NS_RANDOM)
                if result in ["success", "already_signed"]:
                    print(f"账号 {display_user} 签到成功: {msg}")
                    cookies_updated = True
                    
                    if i < len(cookie_list):
                        cookie_list[i] = new_cookie
                    else:
                        cookie_list.append(new_cookie)
                    
                    if hadsend:
                        try:
                            send("NodeSeek 签到", format_notification("✓ 重新登录并签到成功", f"账号 {display_user}: {msg}\n新Cookie已生成，请及时更新"))
                        except Exception as e:
                            print(f"发送通知失败: {e}")
                else:
                    print(f"账号 {display_user} 签到失败: {msg}")
                    if hadsend:
                        try:
                            send("NodeSeek 签到", format_notification("✗ 重新登录后签到失败", f"账号 {display_user}: {msg}\n请检查账号状态"))
                        except Exception as e:
                            print(f"发送通知失败: {e}")
            else:
                print(f"账号 {display_user} 登录失败")
                if hadsend:
                    try:
                        send("NodeSeek 签到", format_notification("✗ 登录失败", f"账号 {display_user}: 无法获取新Cookie，请检查用户名和密码"))
                    except Exception as e:
                        print(f"发送通知失败: {e}")
    
    if cookies_updated and cookie_list:
        print("\n==== 处理完毕，保存更新后的Cookie ====")
        all_cookies_new = "&".join(cookie_list)
        try:
            save_cookie("NS_COOKIE", all_cookies_new)
            print("所有Cookie已成功保存")
        except Exception as e:
            print(f"Cookie变量保存异常: {e}")
