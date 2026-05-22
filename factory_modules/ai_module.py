import os
import requests
import supabase
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv # 1. 추가

load_dotenv() # 2. 추가

# 서버 설정 (환경 변수에서 호출하도록 수정)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_TABLE = "gemi_chat_cache"

supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ.get("OPENROUTER_API_KEY"))

def generate_webcard_code(gui_payload: dict) -> str:
    user_info = gui_payload.get("user_info", {})
    contact_info = gui_payload.get("contact_info", {})
    faq_info = gui_payload.get("faq_info", {})
    design_preference = gui_payload.get("design_preference", {})
    ai_custom_requests = gui_payload.get("ai_custom_requests", {})

    main_image_url = gui_payload.get("main_image_url", "")
    guideline_txt_url = gui_payload.get("guideline_txt_url", "")
    
    # 👑 [수정] 가이드라인을 Base64로 인코딩하여 JS 문법 오류 완벽 차단
    guideline_text = "error"
    if guideline_txt_url:
        try:
            res = requests.get(guideline_txt_url, timeout=5)
            if res.status_code == 200:
                guideline_text = base64.b64encode(res.text.encode('utf-8')).decode('utf-8')
        except:
            guideline_text = "error"

    brand_name = user_info.get("brand_name", "GeMi")
    director_name = user_info.get("name", "장형규")
    introduction = user_info.get("introduction", "")

    template_path = os.path.join("factory_modules", "template.html")
    if not os.path.exists(template_path): template_path = "template.html"

    with open(template_path, "r", encoding="utf-8") as f: 
        template_code = f.read()

    # AI 카피라이팅 적용
    client_context = f"Brand: {brand_name}, Style: {design_preference.get('style')}, Note: {ai_custom_requests.get('special_notes')}"
    refined_intro = introduction
    try:
        response = openai_client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {"role": "system", "content": "You are a premium branding copywriter. Refine the given brand introduction into a luxury, minimalist presentation phrase (in Korean). Return ONLY the refined phrase without quotes."},
                {"role": "user", "content": f"원문: {introduction}\n컨셉: {client_context}"}
            ]
        )
        refined_intro = response.choices[0].message.content.strip()
    except: pass

    # 템플릿 렌더링
    rendered_code = template_code
    rendered_code = rendered_code.replace("${user_name}", director_name)
    rendered_code = rendered_code.replace("${brand_name}", brand_name)
    rendered_code = rendered_code.replace("${INTRODUCTION}", refined_intro)
    rendered_code = rendered_code.replace("${GUIDELINE_TXT_URL}", guideline_text)
    
    # 대문 이미지 바인딩
    default_img = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe"
    rendered_code = rendered_code.replace("${main_image_url}", main_image_url if main_image_url else default_img)
    
    # 👑 [신설: 하이브리드 가변형 포트폴리오 소스코드 마스터 빌더]
    # 장부(`db_module.py`)를 거쳐 고화질 스토리지 주소가 입력된 가변 작품 배열을 가져옵니다.
    portfolio_items = gui_payload.get("portfolio_items", [])
    
    left_column_html = ""   # 1, 3, 5... 홀수 번호 카드가 누적될 왼쪽 열
    right_column_html = ""  # 2, 4, 6... 짝수 번호 카드가 누적될 오른쪽 열

    for idx, item in enumerate(portfolio_items):
        img_url = item.get("image_url", "").strip()
        desc_text = item.get("description", "").strip()
        
        # 만약 사용자가 사진 선택을 누락했다면 언스플래시 프리미엄 템플릿 기본 컷으로 자동 방어
        if not img_url:
            img_url = default_img
            
        # 자바스크립트 함수 인자로 문자열이 안전하게 넘어갈 수 있도록 백틱 및 따옴표 기호 가공
        safe_desc = desc_text.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
        
        # 파일 경로에서 순수 이름만 추출하여 타이틀 명명 규칙 적용
        raw_name = item.get("image_name", "")
        project_title = os.path.splitext(raw_name)[0] if raw_name else f"Project Piece {idx+1}"
        if project_title.startswith("port_"):
            project_title = project_title.replace("port_", "", 1)
            
        # 👑 하이브리드 판별식: 서사(기획의도)의 존재 유무에 따라 HTML 테그 구조 정밀 변형
        if desc_text:
            # 서사가 있다면: 클릭 시 상세 오버레이 팝업창이 열리는 고급 하이브리드 카드 생성
            card_html = f"""
            <div class="cursor-pointer group" onclick="openProjectDetail('{project_title}', '{safe_desc}', '{img_url}')">
                <img src="{img_url}" class="rounded-2xl border border-white/5 shadow-2xl group-hover:border-[#C5A059] transition-all">
                <p class="text-[11px] text-stone-400 mt-1.5 text-center group-hover:text-white transition-colors">{project_title}</p>
            </div>
            """
        else:
            # 서사가 없다면: 터치 반응이 아예 없고 캡션도 노출되지 않는 정갈한 미니멀 순수 갤러리 카드 생성
            card_html = f"""
            <div class="group">
                <img src="{img_url}" class="rounded-2xl border border-white/5 shadow-2xl transition-all">
            </div>
            """

        # 좌우 비대칭 균형 밸런스에 맞춰 홀수/짝수 배치 분할 누적
        if (idx + 1) % 2 != 0:
            left_column_html += card_html
        else:
            right_column_html += card_html

    # 만약 사용자가 포nt폴리오를 단 한 개도 등록 안 했을 때를 위한 방어벽
    if not left_column_html and not right_column_html:
        left_column_html = f'<div class="group"><img src="{default_img}" class="rounded-2xl border border-white/5 shadow-2xl"></div>'

    # 템플릿의 고정된 구멍 대신 좌우 가변형 기둥 코드 구역으로 통째로 스왑 치환
    rendered_code = rendered_code.replace("${PORTFOLIO_LEFT_COLUMN}", left_column_html)
    rendered_code = rendered_code.replace("${PORTFOLIO_RIGHT_COLUMN}", right_column_html)

    # 연락처 및 기타 정보 (바인딩 로직 강화)
    rendered_code = rendered_code.replace("${PHONE}", contact_info.get("phone", ""))
    rendered_code = rendered_code.replace("${EMAIL}", contact_info.get("email", ""))
    
    # SNS 정보 처리
    sns1_type = contact_info.get("sns1_type", "SNS")
    sns1_url = contact_info.get("sns1_url", "#")
    sns2_type = contact_info.get("sns2_type", "SNS")
    sns2_url = contact_info.get("sns2_url", "#")
    
    rendered_code = rendered_code.replace("${SNS1_TYPE}", sns1_type)
    rendered_code = rendered_code.replace("${SNS1_URL}", sns1_url)
    rendered_code = rendered_code.replace("${SNS2_TYPE}", sns2_type)
    rendered_code = rendered_code.replace("${SNS2_URL}", sns2_url)
    
    # SNS 표시 여부 설정
    rendered_code = rendered_code.replace("${SNS1_DISPLAY}", "display: flex;" if sns1_url != "#" else "display: none !important;")
    rendered_code = rendered_code.replace("${SNS2_DISPLAY}", "display: flex;" if sns2_url != "#" else "display: none !important;")

    # FAQ 1, 2, 3 텍스트 추출 및 매칭 치환 파이프라인
    f1_q = faq_info.get("faq1_q", "").strip()
    f1_a = faq_info.get("faq1_a", "").strip()
    f2_q = faq_info.get("faq2_q", "").strip()
    f2_a = faq_info.get("faq2_a", "").strip()
    f3_q = faq_info.get("faq3_q", "").strip()
    f3_a = faq_info.get("faq3_a", "").strip()

    rendered_code = rendered_code.replace("${FAQ1_Q}", f1_q)
    rendered_code = rendered_code.replace("${FAQ1_A}", f1_a)
    rendered_code = rendered_code.replace("${FAQ2_Q}", f2_q)
    rendered_code = rendered_code.replace("${FAQ2_A}", f2_a)
    rendered_code = rendered_code.replace("${FAQ3_Q}", f3_q)
    rendered_code = rendered_code.replace("${FAQ3_A}", f3_a)

    # 자주 묻는 질문 텍스트 입력 여부에 따른 UI 세부 스위칭 필터링
    has_any_faq = f1_q or f2_q or f3_q
    rendered_code = rendered_code.replace("${FAQ_DISPLAY}", "display: block;" if has_any_faq else "display: none !important;")
    rendered_code = rendered_code.replace("${FAQ1_DISPLAY}", "display: block;" if f1_q else "display: none !important;")
    rendered_code = rendered_code.replace("${FAQ2_DISPLAY}", "display: block;" if f2_q else "display: none !important;")
    rendered_code = rendered_code.replace("${FAQ3_DISPLAY}", "display: block;" if f3_q else "display: none !important;")

    return rendered_code