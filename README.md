# 📦 정산용 입출고 내역 자동 분류기

입출고 엑셀 파일을 자동으로 분류하는 Streamlit 앱입니다.

## 🚀 기능

- 출고/입고 엑셀 파일 자동 분류
- 마켓 상품명 관리 (GitHub에 자동 저장)
- 다중 파일 업로드 지원
- 엑셀 결과 다운로드

## 📋 설치 방법

```bash
pip install -r requirements.txt
```

## ⚙️ 설정

### 1. GitHub Personal Access Token 발급
1. GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. `repo` 권한 전체 선택
4. 토큰 복사

### 2. Streamlit Secrets 설정

#### Streamlit Cloud 배포 시:
1. Streamlit Cloud 대시보드
2. 앱 선택 → Settings → Secrets
3. 다음 내용 입력:
```toml
GITHUB_TOKEN = "ghp_your_token_here"
GITHUB_REPO = "username/repository-name"
```

#### 로컬 테스트 시:
프로젝트 폴더에 `.streamlit/secrets.toml` 파일 생성:
```toml
GITHUB_TOKEN = "ghp_your_token_here"
GITHUB_REPO = "username/repository-name"
```

## 🏃 실행 방법

```bash
streamlit run meo_settle_github.py
```

## 📝 사용 방법

1. **마켓 상품명 추가**: 마켓 판매 상품명을 입력
2. **파일 업로드**: 입출고 엑셀 파일 업로드
3. **분류 확인**: 정리 여부 확인
4. **결과 다운로드**: 분류된 엑셀 파일 다운로드

## ⚠️ 주의사항

- `.streamlit/secrets.toml` 파일은 절대 GitHub에 커밋하지 마세요!
- GitHub 토큰은 주기적으로 갱신하세요
- 토큰이 노출되면 즉시 삭제하고 재발급하세요

## 📄 라이선스

MIT License
