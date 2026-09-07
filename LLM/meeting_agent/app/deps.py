from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWTError

from app.security import decode_access_token
from app.models import User

# 读取请求头，取出 Bearer 后面的 token 字符串，是FastAPI安全组件
security_scheme = HTTPBearer()

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> User:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise PyJWTError()
    except PyJWTError:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="无效的身份凭证")
    
    user = await User.filter(username=username).first()
    if user is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="用户不存在")
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    # 预留激活状态扩展
    return current_user
