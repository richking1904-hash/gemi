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
    
    # 가이드라인을 Base64로 인코딩하여 JS 문법 오류 완벽 차단
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
    
    # 하이브리드 가변형 포트폴리오 소스코드 마스터 빌더
    portfolio_items = gui_payload.get("portfolio_items", [])
    
    left_column_html = ""   # 홀수 번호 카드가 누적될 왼쪽 열
    right_column_html = ""  # 짝수 번호 카드가 누적될 오른쪽 열

    for idx, item in enumerate(portfolio_items):
        img_url = item.get("image_url", "").strip()
        desc_text = item.get("description", "").strip()
        
        if not img_url:
            img_url = default_img
            
        # 파일 경로에서 이름 추출 및 가공
        raw_name = item.get("image_name", "")
        project_title = os.path.splitext(raw_name)[0] if raw_name else f"Project Piece {idx+1}"
        if project_title.startswith("port_"):
            project_title = project_title.replace("port_", "", 1)

        # 👑 [매거진형 아키텍처 정밀 구현 구역]
        # 문법 크래시를 유발하던 onclick 자바스크립트 문자열 처리를 100% 영구 소멸시켰습니다.
        # HTML과 Tailwind CSS 스타일의 순수한 조합으로만 갤러리 피드를 안전하게 적재합니다.
        if desc_text:
            # 1. 서사가 있다면: 사진 아래에 프로젝트 제목을 올리고, 그 밑에 기획 의도 서사를 잡지처럼 차분하게 출력
            card_html = (
                "<div class='group mb-6'>"
                "<img src='" + img_url + "' class='rounded-2xl border border-white/5 shadow-2xl transition-all mb-2'>"
                "<h4 class='text-[12px] font-bold text-[#C5A059] tracking-wide px-1 serif italic'>" + project_title + "</h4>"
                "<p class='text-[10px] text-stone-400 font-light leading-relaxed px-1 mt-1 break-keep'>" + desc_text + "</p>"
                "</div>"
            )
        else:
            # 2. 서사가 없다면: 글자 이름표를 완벽하게 배제하고 오직 고화질 미니멀 격자 프레임 자체로만 정렬
            card_html = (
                "<div class='group mb-4'>"
                "<img src='" + img_url + "' class='rounded-2xl border border-white/5 shadow-2xl transition-all'>"
                "</div>"
            )

        if (idx + 1) % 2 != 0:
            left_column_html += card_html
        else:
            right_column_html += card_html

    if not left_column_html and not right_column_html:
        left_column_html = "<div class='group mb-4'><img src='" + default_img + "' class='rounded-2xl border border-white/5 shadow-2xl'></div>"

    # 템플릿 코드 치환
    rendered_code = rendered_code.replace("${PORTFOLIO_LEFT_COLUMN}", left_column_html)
    rendered_code = rendered_code.replace("${PORTFOLIO_RIGHT_COLUMN}", right_column_html)

    # 연락처 및 기타 정보
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
    
    rendered_code = rendered_code.replace("${SNS1_DISPLAY}", "display: flex;" if sns1_url != "#" else "display: none !important;")
    rendered_code = rendered_code.replace("${SNS2_DISPLAY}", "display: flex;" if sns2_url != "#" else "display: none !important;")

    # FAQ 1, 2, 3 텍스트 치환
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

    has_any_faq = f1_q or f2_q or f3_q
    rendered_code = rendered_code.replace("${FAQ_DISPLAY}", "display: block;" if has_any_faq else "display: none !important;")
    rendered_code = rendered_code.replace("${FAQ1_DISPLAY}", "display: block;" if f1_q else "display: none !important;")
    rendered_code = rendered_code.replace("${FAQ2_DISPLAY}", "display: block;" if f2_q else "display: none !important;")
    rendered_code = rendered_code.replace("${FAQ3_DISPLAY}", "display: block;" if f3_q else "display: none !important;")

    return rendered_code