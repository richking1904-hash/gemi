import os
import requests
import supabase
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 서버 설정 (환경 변수에서 호출하도록 수정)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_TABLE = "gemi_chat_cache"

supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ.get("OPENROUTER_API_KEY"))

# 👑 [포트폴리오 사각 라운드 박스 피드형 공정] 2열을 폐기하고 1열 콤팩트 카드 피드로 완전 개조합니다.
def generate_webcard_code(gui_payload: dict) -> dict:
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

    # 템플릿 렌더링 (메인 명함용 뼈대 빌드업)
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
    
    # 외부 테마 주입 파이프라인 엔진 가동
    portfolio_theme = gui_payload.get("portfolio_theme", "[명함 테마와 동기화]")
    custom_css_content = ""
    custom_layout_html = ""

    # 테마 키워드 매핑 매치
    theme_key = "sync"
    if "Big Picture" in portfolio_theme:
        theme_key = "big"
    elif "Ethereal" in portfolio_theme:
        theme_key = "ethereal"
    elif "Paradigm Shift" in portfolio_theme:
        theme_key = "paradigm"

    # 외부 css 로드 파일 구역 (factory_modules 내부 순정 경로 유지)
    if theme_key != "sync":
        css_file_name = f"{theme_key}.css"
        css_path = os.path.join("factory_modules", "external_themes", css_file_name)
        if not os.path.exists(css_path):
            css_path = os.path.join("external_themes", css_file_name)
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as css_f:
                custom_css_content = css_f.read()

    # 👑 [세로 카드 피드형 1열 구조 빌더 설계]
    # - 꼬임의 주범이었던 2열 그리드를 완전히 들어내고, 형규님 오더대로 '중앙 사각 라운드 카드'가 아래로 반복해서 쌓이는 구조로 개조했습니다.
    feed_cards_html = ""   

    for idx, item in enumerate(portfolio_items):
        img_url = item.get("image_url", "").strip()
        desc_text = item.get("description", "").strip()
        
        if not img_url:
            img_url = default_img
            
        raw_name = item.get("image_name", "")
        project_title = os.path.splitext(raw_name)[0] if raw_name else f"Project Piece {idx+1}"
        if project_title.startswith("port_"):
            project_title = project_title.replace("port_", "", 1)

        # 👑 개별 카드가 완벽한 라운드 박스 형태를 띠며, 내부에 안착한 이미지가 비율에 맞게 절대 잘리지 않도록 고정합니다.
        if desc_text:
            card_html = (
                "<div class='centered-card-item mb-10' style='width:100%; max-width:410px; background-color:#1a1c1e; border:1px solid rgba(255,255,255,0.1); border-radius:32px; overflow:hidden; box-shadow:0 30px 60px rgba(0,0,0,0.6); display:flex; flex-direction:column; margin:0 auto 40px auto;'>"
                "  <div style='width:100%; position:relative; overflow:hidden;'>"
                "    <img src='" + img_url + "' style='width:100% !important; height:auto !important; max-height:none !important; object-fit:contain !important; display:block;'>"
                "  </div>"
                "  <div style='padding:20px; background:#1a1c1e; text-align:center; border-t:1px solid rgba(255,255,255,0.05);'>"
                "    <h4 class='text-[14px] font-bold text-[#C5A059] tracking-wide serif italic'>" + project_title + "</h4>"
                "    <p class='text-[11px] text-stone-400 font-light leading-relaxed mt-1.5 break-keep' style='max-width:300px; margin:6px auto 0 auto;'>" + desc_text + "</p>"
                "  </div>"
                "</div>"
            )
        else:
            card_html = (
                "<div class='centered-card-item mb-8' style='width:100%; max-width:410px; background-color:#1a1c1e; border:1px solid rgba(255,255,255,0.1); border-radius:32px; overflow:hidden; box-shadow:0 30px 60px rgba(0,0,0,0.6); margin:0 auto 32px auto;'>"
                "  <img src='" + img_url + "' style='width:100% !important; height:auto !important; max-height:none !important; object-fit:contain !important; display:block;'>"
                "</div>"
            )
        feed_cards_html += card_html

    if not feed_cards_html:
        feed_cards_html = "<div class='centered-card-item' style='width:100%; max-width:410px; background-color:#1a1c1e; border:1px solid rgba(255,255,255,0.1); border-radius:32px; overflow:hidden; margin:0 auto;'><img src='" + default_img + "' style='width:100%; height:auto;'></div>"

    # 메인 웹명함 내부 SPA 스위칭용 스켈레톤 마스킹
    main_card_layout_html = (
        "<div id='promoPage' class='hidden w-full h-full flex flex-col relative bg-[#1a1c1e]'>"
        "    <div class='px-5 py-4 border-b border-white/5 bg-[#1a1c1e] flex justify-between items-center z-10'>"
        "        <span class='text-xs font-bold tracking-[3px] text-[#C5A059] serif uppercase'>Selected Pieces</span>"
        "        <button onclick=\"switchPage('mainPage')\" class='text-[10px] text-stone-500 hover:text-white uppercase tracking-wider font-bold'>Close</button>"
        "    </div>"
        "    <div class='sub-page-content overflow-y-auto px-5 py-4' style='max-height: 90vh; scrollbar-width: none; -ms-overflow-style: none;'>"
        "        <div class='flex flex-col space-y-6 items-center'>" + feed_cards_html + "</div>"
        "    </div>"
        "</div>"
    )

    # 2. 외부 테마용 레이아웃 분기 빌더
    if theme_key == "big":
        custom_layout_html = feed_cards_html
    elif theme_key == "ethereal":
        custom_layout_html = feed_cards_html
    elif theme_key == "paradigm":
        custom_layout_html = feed_cards_html

    if theme_key == "sync":
        custom_layout_html = feed_cards_html

    # 👑 [세로 누적 피드형 팝업 최종 완공 규격]
    # - 바깥 도화지는 풀스크롤로 뚫어두어 마우스 휠이나 터치로 스크롤을 내릴 때마다 예쁜 사각 라운드 카드 형태가 툭툭 등장합니다.
    # - 상단 뒤로가기 링크 바는 화면 위쪽에 늘 깔끔하게 정착되어 있습니다.
    final_portfolio_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{brand_name} - Portfolio Feed</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,wght@0,400;1,700&family=Noto+Sans+KR:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --gold: #C5A059; --dark-bg: #121314; }}
        body {{ background-color: var(--dark-bg); font-family: 'Noto Sans KR', sans-serif; min-height: 100vh; margin: 0; padding: 80px 15px 40px 15px; overflow-y: auto !important; }}
        .serif {{ font-family: 'Bodoni Moda', serif; }}
        
        {custom_css_content}
    </style>
</head>
<body class="antialiased text-stone-200">
    
    <div style="position: fixed; top: 15px; left: 50%; transform: translateX(-50%); z-index: 200; width: 100%; max-width: 410px; padding: 0 15px;">
        <a href="../index.html" style="display: block; width: 100%; text-align: center; background: #1a1c1e; border: 1px solid var(--gold); border-radius: 14px; padding: 12px; color: var(--gold); text-decoration: none; font-size: 11px; font-weight: bold; tracking-widest: 2px; box-shadow: 0 10px 25px rgba(0,0,0,0.6); font-family: 'Noto Sans KR', sans-serif;">
            ← BACK TO WEB CARD (명함 홈으로 이동)
        </a>
    </div>

    <div style="width: 100%; max-width: 410px; margin: 0 auto; height: auto;">
        {custom_layout_html}
    </div>
</body>
</html>"""

    # 명함 본진 소스코드 마스킹
    rendered_code = template_code
    rendered_code = rendered_code.replace("${user_name}", director_name)
    rendered_code = rendered_code.replace("${brand_name}", brand_name)
    rendered_code = rendered_code.replace("${INTRODUCTION}", refined_intro)
    rendered_code = rendered_code.replace("${GUIDELINE_TXT_URL}", guideline_text)
    rendered_code = rendered_code.replace("${main_image_url}", main_image_url if main_image_url else default_img)
    
    rendered_code = rendered_code.replace("${PORTFOLIO_CUSTOM_CSS}", "")
    rendered_code = rendered_code.replace("${PORTFOLIO_PAGE_LAYOUT}", main_card_layout_html)
    rendered_code = rendered_code.replace("${PORTFOLIO_LEFT_COLUMN}", "")
    rendered_code = rendered_code.replace("${PORTFOLIO_RIGHT_COLUMN}", "")

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
    rendered_code = rendered_code.replace("${FAQ2_DISPLAY}", "display: block;" if f1_q else "display: none !important;")
    rendered_code = rendered_code.replace("${FAQ3_DISPLAY}", "display: block;" if f3_q else "display: none !important;")

    return {
        "main_html": rendered_code,
        "portfolio_html": final_portfolio_html
    }