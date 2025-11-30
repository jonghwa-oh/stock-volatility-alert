"""
한국투자증권 API 키 암호화 관리
"""
import os
from pathlib import Path
from cryptography.fernet import Fernet
from database import StockDatabase


class KISCrypto:
    """한국투자증권 API 키 암호화/복호화"""
    
    def __init__(self):
        self.key_file = Path('data') / '.kis_key'
        self.cipher = None
        self._load_or_create_key()
    
    def _load_or_create_key(self):
        """암호화 키 로드 또는 생성"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            self.key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.key_file, 'wb') as f:
                f.write(key)
            print(f"✅ 암호화 키 생성: {self.key_file}")
        
        self.cipher = Fernet(key)
    
    def encrypt(self, text: str) -> str:
        """텍스트 암호화"""
        encrypted = self.cipher.encrypt(text.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_text: str) -> str:
        """텍스트 복호화"""
        decrypted = self.cipher.decrypt(encrypted_text.encode())
        return decrypted.decode()
    
    def save_kis_credentials(self, app_key: str, app_secret: str, account_no: str = None, account_code: str = "01"):
        """한국투자증권 인증 정보 저장"""
        db = StockDatabase()
        
        # 암호화
        encrypted_key = self.encrypt(app_key)
        encrypted_secret = self.encrypt(app_secret)
        
        # DB 저장
        db.save_setting('kis_app_key', encrypted_key, '한국투자증권 App Key (암호화)')
        db.save_setting('kis_app_secret', encrypted_secret, '한국투자증권 App Secret (암호화)')
        
        if account_no:
            encrypted_account = self.encrypt(account_no)
            db.save_setting('kis_account_no', encrypted_account, '계좌번호 앞 8자리 (암호화)')
        
        db.save_setting('kis_account_code', account_code, '계좌번호 뒤 2자리 (01=종합)')
        
        db.close()
        print("✅ 한국투자증권 인증 정보 저장 완료 (암호화)")
    
    def load_kis_credentials(self) -> dict:
        """한국투자증권 인증 정보 로드"""
        db = StockDatabase()
        
        encrypted_key = db.get_setting('kis_app_key')
        encrypted_secret = db.get_setting('kis_app_secret')
        encrypted_account = db.get_setting('kis_account_no')
        account_code = db.get_setting('kis_account_code', '01')
        
        db.close()
        
        if not encrypted_key or not encrypted_secret:
            raise ValueError(
                "한국투자증권 인증 정보가 없습니다!\n"
                "python init_kis_settings.py를 먼저 실행하세요."
            )
        
        # 복호화
        return {
            'app_key': self.decrypt(encrypted_key),
            'app_secret': self.decrypt(encrypted_secret),
            'account_no': self.decrypt(encrypted_account) if encrypted_account else None,
            'account_code': account_code
        }


if __name__ == "__main__":
    # 테스트
    crypto = KISCrypto()
    
    # 암호화 테스트
    original = "테스트 문자열 1234!@#$"
    encrypted = crypto.encrypt(original)
    decrypted = crypto.decrypt(encrypted)
    
    print(f"원본: {original}")
    print(f"암호화: {encrypted}")
    print(f"복호화: {decrypted}")
    print(f"일치: {original == decrypted}")

