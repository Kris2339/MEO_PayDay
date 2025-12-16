import io
import json
import os
import pandas as pd
import streamlit as st
import requests
import base64
from datetime import datetime

st.set_page_config(page_title="엑셀 입출고 분류기", layout="centered")
st.title("📦 정산용 입출고 내역 자동 분류기")

# --- GitHub 설정 ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")  # Streamlit Secrets에서 가져오기
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "")     # 예: "username/repo-name"
GITHUB_FILE_PATH = "market_products.json"           # GitHub 저장 경로

# --- GitHub API 함수 ---
def get_file_from_github():
    """GitHub에서 파일 가져오기"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return []
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()
            file_content = base64.b64decode(content['content']).decode('utf-8')
            return json.loads(file_content)
        elif response.status_code == 404:
            # 파일이 없으면 빈 리스트 반환
            return []
        else:
            st.warning(f"GitHub에서 데이터를 가져오는데 실패했습니다: {response.status_code}")
            return []
    except Exception as e:
        st.warning(f"GitHub 연결 오류: {e}")
        return []

def save_file_to_github(products, sha=None):
    """GitHub에 파일 저장하기"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        st.error("⚠️ GitHub 설정이 필요합니다. Streamlit Secrets에 GITHUB_TOKEN과 GITHUB_REPO를 추가하세요.")
        return False
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # JSON을 base64로 인코딩
    content = json.dumps(products, ensure_ascii=False, indent=2)
    content_bytes = content.encode('utf-8')
    content_base64 = base64.b64encode(content_bytes).decode('utf-8')
    
    # 현재 파일의 SHA 가져오기 (업데이트를 위해 필요)
    if sha is None:
        try:
            get_response = requests.get(url, headers=headers)
            if get_response.status_code == 200:
                sha = get_response.json()['sha']
        except:
            pass
    
    # 커밋 데이터
    data = {
        "message": f"마켓 상품명 업데이트 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": content_base64,
        "branch": "main"  # 또는 "master" (본인의 기본 브랜치에 맞게)
    }
    
    if sha:
        data["sha"] = sha
    
    try:
        response = requests.put(url, headers=headers, json=data)
        if response.status_code in [200, 201]:
            return True
        else:
            st.error(f"GitHub 저장 실패: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        st.error(f"GitHub 저장 오류: {e}")
        return False

# --- 마켓 상품명 관리 ---
# 초기 로드 (GitHub에서 가져오기)
if 'market_products' not in st.session_state:
    st.session_state.market_products = get_file_from_github()
if 'github_sha' not in st.session_state:
    st.session_state.github_sha = None

st.write("### 1) 마켓 상품명 관리")

# GitHub 연결 상태 표시
if GITHUB_TOKEN and GITHUB_REPO:
    st.success(f"✅ GitHub 연결됨: `{GITHUB_REPO}`")
else:
    st.warning("⚠️ GitHub 설정이 필요합니다. 로컬에서만 작동합니다.")
    with st.expander("📖 GitHub 설정 방법 보기"):
        st.markdown("""
        ### Streamlit Cloud에서 GitHub 연동 설정
        
        1. **Streamlit Cloud 대시보드** 접속
        2. 앱 선택 → **Settings** → **Secrets**
        3. 다음 내용 입력:
        ```toml
        GITHUB_TOKEN = "ghp_your_token_here"
        GITHUB_REPO = "username/repository-name"
        ```
        4. **Save** 클릭
        
        ### 로컬에서 테스트할 때
        프로젝트 폴더에 `.streamlit/secrets.toml` 파일 생성 후 같은 내용 입력
        """)

# 탭으로 구분: 추가 / 목록 관리
tab1, tab2 = st.tabs(["➕ 상품명 추가", "📋 등록된 상품명"])

with tab1:
    st.write("**새로운 마켓 상품명을 한 줄에 하나씩 입력하세요** (여러 개 동시 입력 가능)")
    new_products_text = st.text_area(
        "상품명 입력",
        height=150,
        placeholder="예시:\n테라핏 앰플\n캐비진저\n테라드림 수면영양제"
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("✅ 추가하기", type="primary"):
            if new_products_text.strip():
                # 줄 단위로 분리하여 추가
                new_items = [
                    line.strip() 
                    for line in new_products_text.split('\n') 
                    if line.strip()
                ]
                
                # 중복 제거하면서 추가
                added_count = 0
                for item in new_items:
                    if item not in st.session_state.market_products:
                        st.session_state.market_products.append(item)
                        added_count += 1
                
                if added_count > 0:
                    # GitHub에 저장
                    with st.spinner("GitHub에 저장 중..."):
                        if save_file_to_github(st.session_state.market_products, st.session_state.github_sha):
                            st.success(f"✅ {added_count}개 상품명이 추가되고 GitHub에 저장되었습니다!")
                            # SHA 업데이트를 위해 다시 로드
                            st.session_state.market_products = get_file_from_github()
                            st.rerun()
                        else:
                            st.error("❌ GitHub 저장에 실패했습니다. 로컬에만 저장됩니다.")
                else:
                    st.info("ℹ️ 모두 이미 등록된 상품명입니다.")
            else:
                st.warning("⚠️ 상품명을 입력해주세요.")

with tab2:
    if st.session_state.market_products:
        st.write(f"**현재 등록된 마켓 상품명: {len(st.session_state.market_products)}개**")
        
        # 버튼들
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("🔄 새로고침"):
                st.session_state.market_products = get_file_from_github()
                st.success("GitHub에서 최신 데이터를 불러왔습니다!")
                st.rerun()
        
        with col2:
            if st.button("🗑️ 전체 삭제"):
                st.session_state.market_products = []
                with st.spinner("GitHub에 저장 중..."):
                    save_file_to_github([])
                st.rerun()
        
        # 엑셀 내보내기
        st.write("---")
        export_df = pd.DataFrame(st.session_state.market_products, columns=['마켓 상품명'])
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            export_df.to_excel(writer, index=False, sheet_name='마켓상품명')
        buffer.seek(0)
        st.download_button(
            label="📥 엑셀로 내보내기",
            data=buffer.getvalue(),
            file_name="마켓상품명.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_market"
        )
        
        # 상품명 목록 표시 (개별 삭제 가능)
        st.write("---")
        st.write("**등록된 상품명 목록:**")
        for idx, product in enumerate(st.session_state.market_products):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"{idx+1}. {product}")
            with col2:
                if st.button("❌", key=f"del_{idx}"):
                    st.session_state.market_products.pop(idx)
                    with st.spinner("GitHub에 저장 중..."):
                        save_file_to_github(st.session_state.market_products, st.session_state.github_sha)
                    st.rerun()
    else:
        st.info("📝 등록된 마켓 상품명이 없습니다. '상품명 추가' 탭에서 추가해주세요.")

# 마켓 상품명 리스트 가져오기
market_sales_list = st.session_state.market_products

st.divider()

# --- 2. 입출고 엑셀 파일들 업로드 ---
st.write("### 2) 입출고 엑셀 파일들 업로드 (다중 선택 가능)")
uploaded_files = st.file_uploader(
    "출고·입고 엑셀(.xls/.xlsx) 파일을 모두 선택하세요",
    type=["xls", "xlsx"],
    accept_multiple_files=True
)

# --- 3. '정리 여부' 확인 ---
if not market_sales_list:
    st.warning("⚠️ 먼저 마켓 상품명을 추가해주세요.")
    st.stop()

if not uploaded_files:
    st.info("▶ 입출고 파일을 업로드한 뒤, 분류 작업을 시작할 수 있습니다.")
    st.stop()

response = st.radio(
    "마켓 출고건들은 상품명을 정리하셨나요?",
    ["정리함", "아직 안함"]
)
if response == "아직 안함":
    st.warning("❗ 마켓 출고건을 정리한 뒤 다시 실행해주세요.")
    st.stop()

# --- 4. 컬럼 그룹 정의 ---
column_group_out = [
    '출고일', '구분', '판매처', '상품명', '가용출고수량',
    '비고', '수령자', '판매처상품명', '판매처옵션명', '출고방식']

column_group_in = [
    "입고일", "구분", "공급처", "상품명", "가용입고수량",
    "비고", "옵션코드", "입고단가","박스수량"]

# --- 5. 분류 함수 정의 ---
def classify(row, market_list):
    구분 = str(row.get('구분', '')).strip()
    비고 = str(row.get('비고', ''))

    # 비고 우선 체크
    if "밀크런" in 비고:
        return "로켓"
    if "로켓그로스" in 비고:
        return "로켓"
    if "파스토" in 비고:
        return "로켓"
    if "스타배송" in 비고:
        return "로켓"
    if "컬리" in 비고:
        return "로켓"
    if "올리브영" in 비고:
        return "B2B"
    if "신라면세점" in 비고:
        return "B2B"
    if "큐텐" in 비고:
        return "B2B"
    if "수출" in 비고:
        return "B2B"

    if 구분 == "(-)조정":
        if "세트" in 비고:
            return "세트용 출고"
        else:
            return "출고조정"

    if 구분 == "(+)조정":
        if "세트" in 비고:
            return "세트용 입고"
        elif "가구매" in 비고:
            return "가구매 입고"
        else:
            return "입고조정"

    if 구분 == "정상입고":
        if "세트" in 비고:
            return "세트용 입고"
        else:
            return "정상입고"

    if 구분 == "반품입고":
        return "반품입고"

    if 구분 == "정상출고":
        판매처 = str(row.get('판매처', '')).strip()
        판매처상품명 = str(row.get('판매처상품명', '')).strip()
        판매처옵션명 = str(row.get('판매처옵션명', ''))
        출고방식 = str(row.get('출고방식', '')).strip()

        # 기본값으로 시작
        result = "일반"

        # 우선순위: 아래 조건이 위 조건을 덮어씀

        # 11. 미분류 조건
        if (판매처 == '아임웹_미오' and '전화구매' not in 판매처옵션명) or 판매처 == '':
            result = "미분류"

        # 10. 수기발주
        if "수기발주" in 판매처:
            result = "수기"

        # 9. 불량 재발송 (판매처옵션명)
        if '제품 불량 재발송' in 판매처옵션명:
            result = "불량"

        # 8. 고알레 (판매처상품명 또는 판매처옵션명)
        if "고알레" in 판매처상품명 or "고알레" in 판매처옵션명:
            result = "고알레"

        # 7. 인터 (판매처옵션명)
        if "인터" in 판매처옵션명:
            result = "인터"

        # 6. 일반 (판매처옵션명)
        if "일반" in 판매처옵션명:
            result = "일반"

        # 5. B2B (판매처옵션명)
        if any(keyword in 판매처옵션명 for keyword in ['올리브영', '신라면세점', '큐텐', '수출']):
            result = "B2B"

        # 4. 마켓 상품명 리스트
        if 판매처상품명 in market_list:
            result = "마켓"

        # 3. 마케팅 (판매처옵션명)
        if any(x in 판매처옵션명 for x in ['마케팅', '시딩', '개인구매', '사은품']):
            result = "마케팅"

        # 2. 로켓 (판매처옵션명)
        if any(keyword in 판매처옵션명 for keyword in ['밀크런', '로켓그로스', '파스토', '스타배송', '컬리']):
            result = "로켓"

        # 1. 쿠팡 로켓 (판매처 직접 체크)
        if "*쿠팡(쉽먼트)" in 판매처 or "2.쿠팡(쉽먼트)" in 판매처:
            result = "로켓"

        # 0. 세트용 출고 (출고방식 비어있음 + 비고에 세트)
        if 출고방식 == "" and "세트" in 비고:
            result = "세트용 출고"

        return result

    return 구분

# --- 6. 업로드된 파일들 처리 ---
df_out_list = []
df_in_list = []
errors = []

for uploaded_file in uploaded_files:
    try:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        if file_ext == 'xls':
            df = pd.read_excel(uploaded_file, engine='xlrd')
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
    except Exception as e:
        errors.append(f"파일 읽기 실패: {uploaded_file.name} ({e})")
        continue

    df.columns = df.columns.str.strip()

    if '가용입고' in df.columns and '가용입고수량' not in df.columns:
        df.rename(columns={'가용입고': '가용입고수량'}, inplace=True)

    is_out_file = '출고일' in df.columns
    is_in_file = '입고일' in df.columns

    if is_out_file:
        df_filtered = df[df['구분'].isin(["정상출고", "(-)조정"])].copy()
        existing_cols = [c for c in column_group_out if c in df_filtered.columns]
        df_filtered = df_filtered[existing_cols]
        df_filtered['출고일'] = pd.to_datetime(
            df_filtered['출고일'], errors='coerce'
        ).dt.strftime('%Y-%m-%d')

        df_filtered.insert(0, '분류제안', '')
        df_filtered.insert(1, '분류확정', '')

        for col in column_group_out:
            if col not in df_filtered.columns:
                df_filtered[col] = ""

        df_filtered['분류제안'] = df_filtered.apply(
            lambda row: classify(row, market_sales_list), axis=1
        )
        df_filtered = df_filtered[df_filtered['분류제안'].notna()]

        df_filtered = df_filtered[['분류제안', '분류확정'] + column_group_out]
        df_out_list.append(df_filtered)

    elif is_in_file:
        df_filtered = df[df['구분'].isin(["반품입고", "정상입고", "(+)조정"])].copy()
        existing_cols = [c for c in column_group_in if c in df_filtered.columns]
        df_filtered = df_filtered[existing_cols]
        df_filtered['입고일'] = pd.to_datetime(
            df_filtered['입고일'], errors='coerce'
        ).dt.strftime('%Y-%m-%d')

        df_filtered.insert(0, '분류제안', '')
        df_filtered.insert(1, '분류확정', '')

        for col in column_group_in:
            if col not in df_filtered.columns:
                df_filtered[col] = ""

        rename_dict = {
            "입고일": "출고일",
            "공급처": "판매처",
            "가용입고수량": "가용출고수량",
            "옵션명": "판매처옵션명"
        }
        df_filtered.rename(columns=rename_dict, inplace=True)

        for col in column_group_out:
            if col not in df_filtered.columns:
                df_filtered[col] = ""

        df_filtered['분류제안'] = df_filtered.apply(
            lambda row: classify(row, market_sales_list), axis=1
        )
        df_filtered = df_filtered[df_filtered['분류제안'].notna()]

        df_filtered = df_filtered[['분류제안', '분류확정'] + column_group_out]
        df_in_list.append(df_filtered)

    else:
        errors.append(f"처리 대상 아님: {uploaded_file.name} (입출고용 키 컬럼 없음)")
        continue

if errors:
    st.warning("일부 파일 처리 시 오류 발생:")
    for err in errors:
        st.write(f"- {err}")

if df_out_list:
    out_df = pd.concat(df_out_list, ignore_index=True, sort=False)
else:
    out_df = pd.DataFrame(columns=['분류제안'])
if df_in_list:
    in_df = pd.concat(df_in_list, ignore_index=True, sort=False)
else:
    in_df = pd.DataFrame(columns=['분류제안'])

final_df = pd.concat([out_df, in_df], ignore_index=True, sort=False)

if final_df.empty:
    st.error("▶ 업로드된 파일 중 유효한 출고/입고 데이터가 없습니다.")
    st.stop()

# --- 7. 결과 다운로드 제공 ---
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    final_df.to_excel(writer, index=False, sheet_name='최종분류')
buffer.seek(0)

st.success("✅ 분류가 완료되었습니다!")
st.download_button(
    label="📥 최종분류결과.xlsx 다운로드",
    data=buffer.getvalue(),
    file_name="최종분류결과.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- 8. 추가 요약 정보 ---
with st.expander("▶ 출고/입고 요약 보기"):
    st.write("#### [출고 파일 요약]")
    if not out_df.empty:
        st.write(f"- 총 건수: {len(out_df)}")
        st.write("- 분류별 건수:")
        st.write(out_df['분류제안'].value_counts().to_frame("건수"))
    else:
        st.write("- 출고 데이터가 없습니다.")

    st.write("\n#### [입고 파일 요약]")
    if not in_df.empty:
        st.write(f"- 총 건수: {len(in_df)}")
        st.write("- 분류별 건수:")
        st.write(in_df['분류제안'].value_counts().to_frame("건수"))
    else:
        st.write("- 입고 데이터가 없습니다.")
