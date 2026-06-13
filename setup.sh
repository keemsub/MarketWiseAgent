#!/bin/bash

# 미국 증시 뉴스 분석 Agent 설치 스크립트

echo "🚀 미국 증시 뉴스 분석 Agent 설치 중..."
echo ""

# 1. Python 버전 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3가 설치되지 않았습니다."
    echo "   Python 3.7 이상을 설치해주세요."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION 감지됨"
echo ""

# 2. 가상환경 생성 (선택사항)
read -p "가상환경을 생성하시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "가상환경 생성 중..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 가상환경이 활성화되었습니다."
    echo ""
fi

# 3. 의존성 설치
echo "📦 의존성 설치 중..."
pip install -r requirements.txt
echo "✅ 의존성 설치 완료"
echo ""

# 4. .env 파일 생성
if [ ! -f .env ]; then
    echo "⚙️ .env 파일 생성 중..."
    cp .env.example .env
    echo "✅ .env 파일이 생성되었습니다."
    echo "   .env 파일을 열어서 API 키를 입력해주세요."
else
    echo "✅ .env 파일이 이미 존재합니다."
fi
echo ""

# 5. 스크립트 실행 권한 설정
chmod +x main.py
echo "✅ 실행 권한이 설정되었습니다."
echo ""

# 6. 완료 메시지
echo "=================================================="
echo "✅ 설치가 완료되었습니다!"
echo "=================================================="
echo ""
echo "다음 단계:"
echo "1. .env 파일을 편집하여 API 키를 입력하세요:"
echo "   nano .env  (또는 원하는 에디터 사용)"
echo ""
echo "2. Agent를 실행하세요:"
echo "   python3 main.py"
echo ""
echo "자세한 내용은 README.md를 참고하세요."
echo ""
