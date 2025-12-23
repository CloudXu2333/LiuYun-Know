"""
安全相关功能：JWT Token 生成/验证、密码加密
"""
import hashlib
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from app.config import settings

print("🔐 正在初始化密码加密...")
print("✅ 密码加密初始化成功（使用 bcrypt 直接实现）")


def _hash_password_for_bcrypt(password: str) -> bytes:
    """
    使用 SHA256 预处理密码，避免 bcrypt 72 字节限制
    
    Args:
        password: 原始密码
    
    Returns:
        SHA256 哈希后的字节串
    """
    return hashlib.sha256(password.encode('utf-8')).digest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码（先 SHA256 再 bcrypt）
    
    Args:
        plain_password: 明文密码
        hashed_password: 加密后的密码哈希
    
    Returns:
        密码是否匹配
    """
    try:
        # 先用 SHA256 预处理
        password_hash = _hash_password_for_bcrypt(plain_password)
        # 使用 bcrypt 验证
        return bcrypt.checkpw(password_hash, hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"⚠️ 密码验证失败: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    获取密码哈希值（先 SHA256 再 bcrypt）
    
    Args:
        password: 明文密码
    
    Returns:
        加密后的密码哈希字符串
    """
    # 先用 SHA256 预处理
    password_hash = _hash_password_for_bcrypt(password)
    # 使用 bcrypt 加密（12 轮，安全性高）
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_hash, salt)
    return hashed.decode('utf-8')


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
    
    Returns:
        JWT token 字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    创建刷新令牌
    
    Args:
        data: 要编码的数据
    
    Returns:
        JWT refresh token 字符串
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码 JWT token
    
    Args:
        token: JWT token 字符串
    
    Returns:
        解码后的数据字典，失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    验证 token 并检查类型
    
    Args:
        token: JWT token 字符串
        token_type: token 类型 (access 或 refresh)
    
    Returns:
        解码后的数据字典，失败返回 None
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    if payload.get("type") != token_type:
        return None
    
    return payload

