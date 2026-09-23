"""B站请求层：统一的 session、超时、重试、风控识别与 Wbi 签名。

所有爬虫脚本都应通过本模块发请求，避免各脚本重复实现网络逻辑。
仅使用 B站公开 Web API（不依赖任何已关停的第三方逆向库）。

2023 年起 B站 搜索等核心接口强制要求 Wbi 签名（w_rid/wts 参数），
需要签名的接口请在调用 request_json / safe_request_json 时传 wbi_sign=True。
"""

import hashlib
import random
import time
import urllib.parse

import requests

from cookie_loader import load_cookie

# 共享会话：复用 TCP 连接，统一基础请求头
# Cookie 采用惰性加载（首次请求时才读取），import 本模块不再有副作用
_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
})

# 网络与重试参数
_TIMEOUT = 10
_MAX_RETRIES = 3
_RETRY_BACKOFF = 2  # 指数退避基数（秒）

# B站 风控相关错误码（触发时会自动退避重试）
_RISK_CODES = {
    -412: "请求被拦截（风控）",
    -352: "触发验证码挑战（风控），建议降低频率或重新登录",
    -799: "请求过于频繁，请稍后重试",
}


class BiliRequestError(Exception):
    """请求层统一异常：网络失败或接口返回非 0 业务码。"""

    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


def _ensure_cookie() -> None:
    """首次请求前加载 Cookie（import 本模块时不再触发读取/退出）。"""
    if "Cookie" not in _SESSION.headers:
        _SESSION.headers["Cookie"] = load_cookie()


# ---------------------------------------------------------------- Wbi 签名
# 参考 B站 前端 getMixinKey 的固定混淆表
_MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]
_NAV_URL = "https://api.bilibili.com/x/web-interface/nav"
_WBI_TTL = 3600  # 签名密钥缓存 1 小时
_wbi_cache = {"mixin_key": None, "ts": 0.0}


def get_wbi_keys() -> str:
    """获取（并缓存）Wbi 签名所需的 mixin key。

    nav 接口在未登录时也返回 wbi_img 字段，因此这里不做业务码校验。
    """
    now = time.time()
    if _wbi_cache["mixin_key"] and now - _wbi_cache["ts"] < _WBI_TTL:
        return _wbi_cache["mixin_key"]

    data = request_json(_NAV_URL, check_code=False)
    wbi_img = (data.get("data") or {}).get("wbi_img") or {}
    img_key = (wbi_img.get("img_url") or "").rsplit("/", 1)[-1].split(".")[0]
    sub_key = (wbi_img.get("sub_url") or "").rsplit("/", 1)[-1].split(".")[0]
    if not img_key or not sub_key:
        raise BiliRequestError("无法获取 Wbi 签名密钥（nav 接口返回异常）")

    raw = img_key + sub_key
    mixin_key = "".join(raw[i] for i in _MIXIN_KEY_ENC_TAB if i < len(raw))[:32]
    _wbi_cache["mixin_key"] = mixin_key
    _wbi_cache["ts"] = now
    return mixin_key


def sign_wbi_params(params: dict) -> dict:
    """对请求参数做 Wbi 签名，返回附加了 wts/w_rid 的新参数字典。"""
    mixin_key = get_wbi_keys()
    signed = dict(params)
    signed["wts"] = int(time.time())
    signed = dict(sorted(signed.items()))
    # 过滤 value 中的 "!'()*" 字符（与 B站 前端实现一致）
    signed = {
        k: "".join(c for c in str(v) if c not in "!'()*")
        for k, v in signed.items()
    }
    query = urllib.parse.urlencode(signed)
    signed["w_rid"] = hashlib.md5((query + mixin_key).encode()).hexdigest()
    return signed


def _handle_business_code(data):
    """校验接口业务码，非 0 时抛出带含义的异常。"""
    code = data.get("code")
    if code == 0:
        return
    if code in _RISK_CODES:
        raise BiliRequestError(_RISK_CODES[code], code)
    if code == -101:
        raise BiliRequestError("未登录或登录态失效，请重新运行 bilibili_login.py", code)
    raise BiliRequestError(data.get("message", f"接口返回错误码 {code}"), code)


def request_json(url, params=None, headers=None, *, check_code=True, wbi_sign=False):
    """带超时、指数退避重试与风控退避的 JSON 请求。

    :param check_code: True 时自动校验业务 code，非 0 抛 BiliRequestError；
                       设为 False 可拿到原始 data 自行判断（如仅需判断登录态）。
    :param wbi_sign: True 时对参数做 Wbi 签名（搜索等 2023+ 接口必需）。
    :return: 解析后的 JSON dict；网络最终失败时抛 BiliRequestError。
    """
    _ensure_cookie()
    last_err = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            req_params = sign_wbi_params(params or {}) if wbi_sign else params
            resp = _SESSION.get(
                url, params=req_params, headers=headers, timeout=_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            last_err = e
            if attempt < _MAX_RETRIES:
                delay = _RETRY_BACKOFF ** (attempt - 1) + random.uniform(0, 1)
                print(f"请求失败(第{attempt}次)，{delay:.1f}秒后重试: {e}")
                time.sleep(delay)
                continue
            raise BiliRequestError(f"请求最终失败: {e}") from e
        except ValueError as e:
            last_err = e
            if attempt < _MAX_RETRIES:
                delay = _RETRY_BACKOFF ** (attempt - 1) + random.uniform(0, 1)
                print(f"响应解析失败(第{attempt}次)，{delay:.1f}秒后重试: {e}")
                time.sleep(delay)
                continue
            raise BiliRequestError(f"响应非 JSON: {e}") from e

        if check_code:
            try:
                _handle_business_code(data)
            except BiliRequestError as e:
                if e.code in _RISK_CODES and attempt < _MAX_RETRIES:
                    # 风控码：退避更久后重签重试，继续请求只会加重风控
                    delay = _RETRY_BACKOFF ** attempt + random.uniform(1, 3)
                    print(f"触发风控({e.code})，{delay:.1f}秒后重试: {e}")
                    time.sleep(delay)
                    last_err = e
                    continue
                raise
        return data

    raise BiliRequestError(f"请求未成功: {last_err}")


def safe_request_json(url, params=None, headers=None, *, check_code=True, wbi_sign=False):
    """request_json 的容错版本：任何失败都返回 None，不抛异常。

    适合"单个视频/评论失败不应中断整体任务"的场景。
    """
    try:
        return request_json(
            url, params=params, headers=headers, check_code=check_code, wbi_sign=wbi_sign
        )
    except BiliRequestError as e:
        print(f"请求出错: {e}")
        return None
