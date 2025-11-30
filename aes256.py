"""
AES256 암호화/복호화 모듈
한국투자증권 WebSocket용
"""
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class AESCipher:
    """AES256 암호화/복호화"""
    
    def __init__(self, key: str):
        """
        Args:
            key: 32바이트 암호화 키 (AES256)
        """
        # 키를 32바이트로 맞춤
        if len(key) < 32:
            key = key.ljust(32, '\0')
        elif len(key) > 32:
            key = key[:32]
        
        self.key = key.encode('utf-8')
        self.block_size = AES.block_size
    
    def encrypt(self, plaintext: str) -> str:
        """
        평문을 AES256으로 암호화
        
        Args:
            plaintext: 평문
            
        Returns:
            str: Base64 인코딩된 암호문
        """
        # IV (Initialization Vector): 16바이트 0으로 초기화
        iv = b'\x00' * 16
        
        # AES 암호화 객체 생성
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        
        # 평문을 바이트로 변환하고 패딩
        plaintext_bytes = plaintext.encode('utf-8')
        padded = pad(plaintext_bytes, self.block_size)
        
        # 암호화
        ciphertext = cipher.encrypt(padded)
        
        # Base64 인코딩하여 반환
        return base64.b64encode(ciphertext).decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        """
        AES256으로 암호화된 텍스트를 복호화
        
        Args:
            ciphertext: Base64 인코딩된 암호문
            
        Returns:
            str: 복호화된 평문
        """
        # IV (Initialization Vector): 16바이트 0으로 초기화
        iv = b'\x00' * 16
        
        # AES 복호화 객체 생성
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        
        # Base64 디코딩
        ciphertext_bytes = base64.b64decode(ciphertext)
        
        # 복호화
        padded_plaintext = cipher.decrypt(ciphertext_bytes)
        
        # 패딩 제거
        plaintext_bytes = unpad(padded_plaintext, self.block_size)
        
        # 문자열로 변환하여 반환
        return plaintext_bytes.decode('utf-8')


if __name__ == "__main__":
    # 테스트
    print("🧪 AES256 암호화/복호화 테스트")
    print("=" * 50)
    
    # 테스트 키 (32바이트)
    key = "test1234567890test1234567890ab"
    cipher = AESCipher(key)
    
    # 테스트 평문
    plaintext = "Hello, KIS WebSocket!"
    print(f"평문: {plaintext}")
    
    # 암호화
    encrypted = cipher.encrypt(plaintext)
    print(f"암호문 (Base64): {encrypted}")
    
    # 복호화
    decrypted = cipher.decrypt(encrypted)
    print(f"복호문: {decrypted}")
    
    # 검증
    if plaintext == decrypted:
        print("\n✅ 암호화/복호화 성공!")
    else:
        print("\n❌ 암호화/복호화 실패!")

