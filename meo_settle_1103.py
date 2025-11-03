import io
import json
import pandas as pd
import streamlit as st

st.set_page_config(page_title="엑셀 입출고 분류기", layout="centered")
st.title("📦 정산용 입출고 내역 자동 분류기")

# --- 마켓 상품명 관리 (누적 저장) ---
# session_state에 마켓 상품명 리스트 저장
if 'market_products' not in st.session_state:
    # 로컬 스토리지 대신 간단히 리스트로 관리 (앱 재시작시 초기화됨)
    st.session_state.market_products = []

st.write("### 1) 마켓 상품명 관리")

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
                    st.success(f"✅ {added_count}개 상품명이 추가되었습니다!")
                    st.rerun()
                else:
                    st.info("ℹ️ 모두 이미 등록된 상품명입니다.")
            else:
                st.warning("⚠️ 상품명을 입력해주세요.")

with tab2:
    if st.session_state.market_products:
        st.write(f"**현재 등록된 마켓 상품명: {len(st.session_state.market_products)}개**")
        
        # 전체 삭제 버튼
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🗑️ 전체 삭제"):
                st.session_state.market_products = []
                st.rerun()
        
        # 상품명 목록 표시 (개별 삭제 가능)
        for idx, product in enumerate(st.session_state.market_products):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"{idx+1}. {product}")
            with col2:
                if st.button("❌", key=f"del_{idx}"):
                    st.session_state.market_products.pop(idx)
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
    '비고', '수령자', '판매처상품명','판매처옵션명']

column_group_in = [
    "입고일", "구분", "공급처", "상품명", "가용입고수량",
    "비고", "옵션코드", "입고단가","박스수량"]

# --- 5. 분류 함수 정의 ---
def classify(row, market_list):
    구분 = str(row.get('구분', '')).strip()
    비고 = str(row.get('비고', ''))

    if "밀크런" in 비고:
        return "로켓"
    if "로켓그로스" in 비고:
        return "로켓"
    if "파스토" in 비고:
        return "로켓"
    if "스타배송" in 비고:
        return "로켓"
    if "올리브영" in 비고:
        return "올리브영"
    if "컬리" in 비고:
        return "일반"
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
        출고방식 = str(row.get('출고방식', '')).strip()
        if 출고방식 == "" and "세트" in 비고:
            return "세트용 출고"
        판매처상품명 = str(row.get('판매처상품명', '')).strip()
        판매처옵션명 = str(row.get('판매처옵션명', ''))
        판매처 = str(row.get('판매처', '')).strip()
        if 판매처 == "*쿠팡(쉽먼트)_미오":
            return "로켓"
        elif 판매처상품명 in market_list:
            return "마켓"
        elif '온누리인터' in 판매처옵션명:
            return "인터"
        elif '큐텐' in 판매처옵션명:
            return "큐텐"
        elif '고알레' in 판매처상품명:
            return "고알레"
        elif any(x in 판매처옵션명 for x in ['마케팅', '시딩', '개인구매','사은품']):
            return "마케팅"
        elif '제품 불량 재발송' in 판매처옵션명:
            return "불량"
        elif '수기발주' in 판매처:
            return "수기"
        elif (판매처 == '아임웹_미오' and '전화구매' not in 판매처옵션명) or (판매처 == ''):
            return "미분류"
        else:
            return "일반"
    return 구분

# --- 6. 업로드된 파일들 처리 ---
df_out_list = []
df_in_list = []
errors = []

for uploaded_file in uploaded_files:
    try:
        df = pd.read_excel(uploaded_file)
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