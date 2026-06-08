"""用户服务层 - 处理用户相关的业务逻辑"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from jose import jwt

from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRegisterRequest, UserUpdateRequest

STANDARD_USER_ROLE = "student"
LEGACY_USER_ROLE = "user"


def get_password_hash(password: str) -> str:
    """
    对密码进行哈希处理
    
    Args:
        password: 原始密码
        
    Returns:
        哈希后的密码
    """
    import bcrypt

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 原始密码
        hashed_password: 哈希后的密码
        
    Returns:
        密码是否匹配
    """
    try:
        import bcrypt

        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT access token
    
    Args:
        data: 要编码到 token 中的数据
        expires_delta: token 过期时间，如果不提供则使用默认配置
        
    Returns:
        编码后的 JWT token 字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


class UserService:
    """用户服务类"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def register(self, user_data: UserRegisterRequest) -> User:
        """
        用户注册
        
        Args:
            user_data: 用户注册数据
            
        Returns:
            新创建的用户对象
            
        Raises:
            ValueError: 如果用户名或邮箱已存在
        """
        # 检查用户名是否已存在
        existing_user = await self.user_repo.get_by_username(user_data.username)
        if existing_user:
            raise ValueError("用户名已存在")
        
        # 检查邮箱是否已存在
        existing_email = await self.user_repo.get_by_email(user_data.email)
        if existing_email:
            raise ValueError("邮箱已被注册")
        
        # 创建新用户
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            phone=user_data.phone,
            role=STANDARD_USER_ROLE,  # 默认角色为普通用户
            is_active=True
        )
        
        await self.user_repo.create(new_user)
        return new_user
    
    async def login(self, username: str, password: str) -> Tuple[str, User]:
        """
        用户登录
        
        Args:
            username: 用户名或邮箱
            password: 密码
            
        Returns:
            (access_token, user) 元组
            
        Raises:
            ValueError: 如果用户名/邮箱不存在或密码错误
        """
        # 尝试通过用户名或邮箱查找用户
        user = await self.user_repo.get_by_username(username)
        if not user:
            user = await self.user_repo.get_by_email(username)
        
        if not user:
            raise ValueError("用户名或邮箱不存在")
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            raise ValueError("密码错误")
        
        # 检查用户是否激活
        if not user.is_active:
            raise ValueError("账户状态不可用")
        
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        await self.user_repo.update(user, {})
        
        # 生成 access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "role": user.role
            },
            expires_delta=access_token_expires
        )
        
        return access_token, user
    
    async def update_user(self, user: User, user_data: UserUpdateRequest) -> User:
        """
        更新用户信息
        
        Args:
            user: 用户对象
            user_data: 更新数据
            
        Returns:
            更新后的用户对象
        """
        if user_data.email is None:
            # None 表示清空邮箱
            user.email = None
        elif user_data.email != user.email:
            existing_email = await self.user_repo.get_by_email(user_data.email)
            if existing_email and existing_email.id != user.id:
                raise ValueError("邮箱已被注册")
            user.email = user_data.email

        if user_data.phone is None:
            # None 表示清空手机号
            user.phone = None

        if user_data.new_password is not None:
            if not user_data.current_password:
                raise ValueError("修改密码时必须填写当前密码")
            if not verify_password(user_data.current_password, user.password_hash):
                raise ValueError("当前密码不正确")
            user.password_hash = get_password_hash(user_data.new_password)
        
        # 保存更新
        await self.user_repo.update(user, {})
        return user
    
    async def switch_role(self, user_id: int, target_role: str) -> dict:
        """
        切换用户角色

        Args:
            user_id: 用户 ID
            target_role: 目标角色

        Returns:
            包含角色信息的字典

        Raises:
            ValueError: 如果切换不被允许
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")

        normalized_target_role = (
            STANDARD_USER_ROLE if target_role == LEGACY_USER_ROLE else target_role
        )

        if normalized_target_role not in [STANDARD_USER_ROLE, "admin"]:
            raise ValueError("不支持的角色切换")

        old_role = user.role
        user.role = normalized_target_role
        await self.user_repo.update(user, {})

        return {
            "role": user.role,
            "old_role": old_role
        }