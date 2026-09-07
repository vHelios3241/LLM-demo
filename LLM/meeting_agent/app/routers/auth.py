from fastapi import APIRouter, Request, HTTPException, Depends
from tortoise.exceptions import IntegrityError

from app.schemas import UserCreate, UserLogin, UserOut, Token
from app.security import hash_password, verify_password, create_access_token
from app.models import User
from app.deps import get_current_active_user

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/register", response_model=UserOut)
async def register(request: Request):
    data = await request.json()
    user_in = UserCreate(**data)
    
    # 预检：提升友好度并减少DB写压力
    if await User.filter(username=user_in.username).exists():
        raise HTTPException(status_code=400, detail="用户名已注册")
        
    hashed_pw = hash_password(user_in.password)
    try:
        user = await User.create(username=user_in.username, password_hash=hashed_pw)
    except IntegrityError:
        # 兜底：防并发下的唯一约束冲突
        raise HTTPException(status_code=400, detail="用户名已注册")
    return await UserOut.from_tortoise_orm(user)

@router.post("/login", response_model=Token)
async def login(request: Request):
    data = await request.json()
    user_in = UserLogin(**data)
    
    user = await User.filter(username=user_in.username).first()
    # 防枚举：不区分"用户不存在"与"密码错误"
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
        
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token)

@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return await UserOut.from_tortoise_orm(current_user)
