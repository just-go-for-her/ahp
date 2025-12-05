import streamlit as st
import google.generativeai as genai

# --------------------------------------------------------------------------
# 1. 설정 및 API 키 고정
# --------------------------------------------------------------------------
st.set_page_config(page_title="AI 논리 진단기 Pro", page_icon="🧠", layout="wide")

# [보안 주의] 실제 서비스 배포 시에는 이 키를 Streamlit Secrets에 숨기는 것이 좋습니다.
FIXED_API_KEY = "AIzaSyDadB0UwZh6Hxa3IT4dGoOak1CTCHqtI2o" 

# Gemini 설정
try:
    genai.configure(api_key=FIXED_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"API 키 설정 오류: {e}")

# --------------------------------------------------------------------------
# 2. 세션 상태 초기화 (동적 입력창 관리를 위해 필수)
# --------------------------------------------------------------------------
if 'main_count' not in st.session_state:
    st.session_state.main_count = 1  # 1차 기준 개수 (처음엔 1개)

if 'sub_counts' not in st.session_state:
    st.session_state.sub_counts = {} # 각 기준별 하위 항목 개수 저장소

# --------------------------------------------------------------------------
# 3. AI 분석 함수 (직관적인 출력을 위해 프롬프트 개선)
# --------------------------------------------------------------------------
def analyze_structure(goal, parent, children):
    if not children:
        return {"status": "MISSING", "reason": "하위 항목이 입력되지 않았습니다."}
    
    # 직관적인 출력을 위해 AI에게 '단답형/등급'으로 요청
    prompt = f"""
    당신은 논리 구조 진단 전문가입니다.
    
    [분석 대상]
    - 목표/상위개념: {goal} -> {parent}
    - 하위요소들: {children}
    
    [요청사항]
    위 구조가 'MECE(누락/중복 없음)'하고 '논리적'인지 판단하여 아래 형식으로 짧게 답변하세요.
    서술형으로 길게 쓰지 마세요.
    
    [답변 형식]
    등급: [양호/주의/위험] 중 하나
    핵심진단: (15자 이내로 짧게 요약)
    문제점: (발견된 경우만 1줄 작성, 없으면 '없음')
    제안: (수정이 필요하다면 1줄 제안)
    """
    
    try:
        response = model.generate_content(prompt)
        return {"text": response.text}
    except Exception as e:
        return {"text": f"통신 오류: {e}"}

# --------------------------------------------------------------------------
# 4. 화면 UI 구성
# --------------------------------------------------------------------------
st.title("🧠 AHP 논리 구조 진단기 (Pro Ver.)")
st.markdown("API 키가 내장되어 있습니다. 바로 구조를 설계하세요.")
st.divider()

# [Step 1] 목표 설정
col_goal, _ = st.columns([2, 1])
with col_goal:
    goal = st.text_input("🎯 1. 최종 목표는 무엇인가요?", placeholder="예: 차세대 국방 AI 시스템 도입")

if goal:
    st.divider()
    st.subheader(f"2. '{goal}'의 평가 기준 설정")
    st.caption("필요한 만큼 '+ 항목 추가' 버튼을 눌러 늘려가세요.")

    # [Step 2] 1차 기준 입력 (동적 생성)
    main_criteria = []
    
    # 입력된 개수만큼 반복해서 입력창 생성
    for i in range(st.session_state.main_count):
        col_input, col_del = st.columns([4, 1])
        with col_input:
            val = st.text_input(f"기준 {i+1}", key=f"main_{i}", placeholder=f"기준 항목 {i+1}")
            if val:
                main_criteria.append(val)
    
    # (+ 항목 추가) 버튼
    if st.button("➕ 1차 기준 추가하기", type="secondary"):
        st.session_state.main_count += 1
        st.rerun() # 화면 새로고침

    # [Step 3] 하위 항목 가지치기
    structure_data = {}
    
    if main_criteria:
        st.divider()
        st.subheader("3. 세부 항목 가지치기")
        
        for idx, criterion in enumerate(main_criteria):
            with st.expander(f"📂 '{criterion}'의 하위 요소 구성", expanded=True):
                # 해당 기준의 하위 항목 개수 가져오기 (없으면 초기값 1)
                if criterion not in st.session_state.sub_counts:
                    st.session_state.sub_counts[criterion] = 1
                
                current_sub_count = st.session_state.sub_counts[criterion]
                sub_items = []
                
                # 하위 항목 입력창 생성
                for j in range(current_sub_count):
                    s_val = st.text_input(
                        f"ㄴ {criterion}의 세부요소 {j+1}", 
                        key=f"sub_{criterion}_{j}",
                        placeholder="세부 항목 입력"
                    )
                    if s_val:
                        sub_items.append(s_val)
                
                # (+ 하위 항목 추가) 버튼
                if st.button(f"➕ '{criterion}' 세부 항목 추가", key=f"btn_add_{criterion}"):
                    st.session_state.sub_counts[criterion] += 1
                    st.rerun()
                
                structure_data[criterion] = sub_items

        # [Step 4] AI 진단 실행
        st.divider()
        st.header("4. AI 논리 진단 결과")
        
        if st.button("🚀 논리 진단 시작 (AI Analysis)", type="primary", use_container_width=True):
            with st.spinner("AI가 구조의 논리성을 분석하고 있습니다..."):
                
                # 결과 표시 (카드 형태)
                st.markdown("### 📊 진단 리포트")
                
                # 1차 기준 전체 진단
                st.info(f"**전체 구조 진단**: 상위 기준 {len(main_criteria)}개 / 세부 항목 총 {sum(len(v) for v in structure_data.values())}개")
                
                # 각 항목별 AI 분석 결과 출력
                for parent, children in structure_data.items():
                    result = analyze_structure(goal, parent, children)
                    text_res = result.get("text", "")
                    
                    # 시각적 박스 스타일링
                    if "위험" in text_res:
                        box_color = "red"
                        icon = "🚨"
                    elif "주의" in text_res:
                        box_color = "orange"
                        icon = "⚠️"
                    else:
                        box_color = "green"
                        icon = "✅"
                    
                    # 결과 출력
                    with st.container():
                        st.markdown(f"""
                        <div style="border: 2px solid {box_color}; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                            <h4 style="margin:0;">{icon} <b>{parent}</b> 분석 결과</h4>
                            <div style="margin-top: 10px; white-space: pre-line;">
                                {text_res}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    else:
        st.info("위에서 1차 기준을 먼저 입력해주세요.")
