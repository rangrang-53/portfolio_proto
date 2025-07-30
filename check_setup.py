#!/usr/bin/env python3
"""
환경 설정 확인 스크립트

이 스크립트는 PDF QA 시스템을 실행하기 위한 환경 설정이 올바른지 확인합니다.
"""

import os
from dotenv import load_dotenv

def check_env_file():
    """환경 변수 파일 확인"""
    print("🔍 환경 설정 확인 중...")
    print("=" * 50)
    
    # .env 파일 존재 확인
    if not os.path.exists('.env'):
        print("❌ .env 파일이 없습니다.")
        print("💡 해결 방법:")
        print("   cp env_example.txt .env")
        print("   그리고 .env 파일에 실제 API 키들을 입력하세요.")
        return False
    
    print("✅ .env 파일이 존재합니다.")
    return True

def check_api_keys():
    """API 키들 확인"""
    load_dotenv()
    
    # 필요한 환경 변수들
    required_vars = {
        'GEMINI_API_KEY': 'Google AI (Gemini) API 키',
        'PINECONE_API_KEY': 'Pinecone API 키',
        'PINECONE_ENVIRONMENT': 'Pinecone 환경'
    }
    
    missing_vars = []
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if not value:
            missing_vars.append(f"  - {var_name}: {description}")
        else:
            # API 키가 설정되어 있지만 실제 값인지 확인
            if value.startswith('your_') or value == '':
                print(f"⚠️  {var_name}: 설정되어 있지만 실제 값이 아닙니다.")
            else:
                print(f"✅ {var_name}: 설정됨")
    
    if missing_vars:
        print("\n❌ 다음 환경 변수들이 설정되지 않았습니다:")
        for var in missing_vars:
            print(var)
        print("\n💡 .env 파일을 편집하여 실제 API 키들을 입력하세요.")
        return False
    
    print("\n✅ 모든 필수 환경 변수가 설정되었습니다.")
    return True

def check_dependencies():
    """필요한 패키지들 확인"""
    print("\n📦 패키지 의존성 확인 중...")
    
    required_packages = [
        'pypdf',
        'sentence_transformers',
        'pinecone',
        'google.genai',
        'dotenv',
        'fastapi',
        'uvicorn',
        'pydantic',
        'tiktoken'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n❌ 다음 패키지들이 설치되지 않았습니다: {', '.join(missing_packages)}")
        print("💡 해결 방법:")
        print("   pip install -r requirements.txt")
        return False
    
    print("\n✅ 모든 필요한 패키지가 설치되어 있습니다.")
    return True

def main():
    """메인 함수"""
    print("🚀 PDF QA 시스템 환경 설정 확인")
    print("=" * 50)
    
    # 환경 파일 확인
    env_ok = check_env_file()
    if not env_ok:
        return
    
    # API 키 확인
    api_ok = check_api_keys()
    if not api_ok:
        return
    
    # 패키지 확인
    deps_ok = check_dependencies()
    if not deps_ok:
        return
    
    print("\n🎉 모든 설정이 완료되었습니다!")
    print("\n💡 이제 다음 명령어로 시스템을 실행할 수 있습니다:")
    print("   python example_usage.py  # 간단한 사용 예시")
    print("   python api.py           # API 서버 실행")
    print("   python test_system.py   # 시스템 테스트")

if __name__ == "__main__":
    main() 