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
    other_image_urls = gui_payload.get("other_image_urls", [])
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
    
    # 이미지 바인딩
    default_img = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe"
    rendered_code = rendered_code.replace("${main_image_url}", main_image_url if main_image_url else default_img)
    
    for i in range(4):
        img_url = other_image_urls[i] if i < len(other_image_urls) else default_img
        rendered_code = rendered_code.replace(f"${{SUB_IMAGE_URL_{i+1}}}", img_url)

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
    
    # SNS 표시 여부 설정 (URL이 있으면 flex, 없으면 none)
    rendered_code = rendered_code.replace("${SNS1_DISPLAY}", "display: flex;" if sns1_url != "#" else "display: none !important;")
    rendered_code = rendered_code.replace("${SNS2_DISPLAY}", "display: flex;" if sns2_url != "#" else "display: none !important;")

    # 👑 [수정 연결 완료] 리모컨에서 넘어온 FAQ 1, 2, 3 텍스트 추출 및 매칭 치환 파이프라인
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