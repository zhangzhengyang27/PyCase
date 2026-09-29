"""异常处理：分层捕获与自定义异常。"""
import json


class AppError(Exception):
    """业务异常基类。"""


class ConfigNotFound(AppError):
    pass


class BadConfigValue(AppError):
    pass


def load_config(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ConfigNotFound(f"配置解析失败: {e}") from e
    if "retries" not in data:
        raise BadConfigValue("缺少 retries 字段")
    if not isinstance(data["retries"], int):
        raise BadConfigValue("retries 必须是整数")
    return data


# 正常路径
print(load_config('{"retries": 3}'))

# 两种失败路径
for bad in ['{"name": "x"}', "not-json"]:
    try:
        load_config(bad)
    except ConfigNotFound as e:
        print("配置错误:", e)
    except BadConfigValue as e:
        print("字段错误:", e)
    finally:
        print("  (finally 总会执行)")
