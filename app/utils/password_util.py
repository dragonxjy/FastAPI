from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

# 加密
def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


# 密码验证:verify 返回值是布尔型
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)
