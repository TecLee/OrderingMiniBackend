from schemas.common import APIResponse


def ok(data=None, message: str = "ok") -> APIResponse:
    return APIResponse(code=0, message=message, data=data)


def error(code: int = 50000, message: str = "服务器内部错误") -> APIResponse:
    return APIResponse(code=code, message=message, data=None)
