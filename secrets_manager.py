"""
민감한 정보를 암호화하여 DB에 저장/조회하는 관리자
"""

from cryptography.fernet import Fernet
import sqlite3
import os
from pathlib import Path


class SecretsManager:
    """암호화된 민감한 정보 관리"""
    
    def __init__(self, db_path='data/secrets.db'):
        self.db_path = db_path
        self.cipher = self._get_cipher()
        self._init_db()
    
    def _get_cipher(self):
        """마스터 키로 암호화 객체 생성"""
        # 환경변수에서 마스터 키 로드
        key = os.getenv('MASTER_KEY')
        
        if not key:
            # .env 파일 확인
            env_file = Path('.env')
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('MASTER_KEY='):
                            key = line.strip().split('=', 1)[1]
                            break
        
        if not key:
            raise ValueError(
                "MASTER_KEY가 설정되지 않았습니다!\n"
                "1. .env 파일을 생성하거나\n"
                "2. 환경변수 MASTER_KEY를 설정하거나\n"
                "3. python setup_secrets.py를 실행하세요."
            )
        
        try:
            return Fernet(key.encode())
        except Exception as e:
            raise ValueError(f"잘못된 MASTER_KEY 형식입니다: {e}")
    
    def _init_db(self):
        """암호화된 설정 테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS secrets (
                key TEXT PRIMARY KEY,
                value BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def set_secret(self, key: str, value: str):
        """암호화하여 저장"""
        if not value:
            raise ValueError(f"빈 값은 저장할 수 없습니다: {key}")
        
        encrypted = self.cipher.encrypt(value.encode())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO secrets (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, encrypted))
        
        conn.commit()
        conn.close()
        print(f"✅ {key} 저장 완료")
    
    def get_secret(self, key: str, default=None) -> str:
        """복호화하여 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM secrets WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            try:
                decrypted = self.cipher.decrypt(result[0])
                return decrypted.decode()
            except Exception as e:
                print(f"⚠️  {key} 복호화 실패: {e}")
                return default
        return default
    
    def delete_secret(self, key: str):
        """설정 삭제"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM secrets WHERE key = ?', (key,))
        conn.commit()
        conn.close()
        print(f"✅ {key} 삭제 완료")
    
    def list_keys(self):
        """저장된 키 목록 (값은 안 보여줌)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT key, created_at, updated_at FROM secrets')
        results = cursor.fetchall()
        conn.close()
        return results


def generate_master_key():
    """새로운 마스터 키 생성"""
    return Fernet.generate_key().decode()


if __name__ == "__main__":
    # 테스트
    print("🔐 Secrets Manager 테스트")
    print("="*50)
    
    # 마스터 키 확인
    if not os.getenv('MASTER_KEY'):
        print("\n⚠️  MASTER_KEY가 설정되지 않았습니다.")
        print("\n새 마스터 키를 생성하려면:")
        print(f"MASTER_KEY={generate_master_key()}")
        print("\n위 키를 .env 파일에 저장하세요!")
    else:
        try:
            sm = SecretsManager()
            print("\n✅ Secrets Manager 초기화 성공")
            print(f"DB 위치: {sm.db_path}")
            
            # 저장된 키 목록
            keys = sm.list_keys()
            if keys:
                print(f"\n저장된 설정: {len(keys)}개")
                for key, created, updated in keys:
                    print(f"  • {key}")
            else:
                print("\n저장된 설정이 없습니다.")
                print("python setup_secrets.py를 실행하여 설정하세요.")
        except Exception as e:
            print(f"\n❌ 오류: {e}")

