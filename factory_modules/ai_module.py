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

# 👑 [4단 분리 듀얼 엔진] 메인 명함과 새 창용 상세 기획서 문서를 분리 빌드하여 dict로 리턴합니다.
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
    
    # 👑 [신설 공정] 외부 테마 주입 파이프라인 엔진 가동
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

    # 1. 기존 [명함 테마와 동기화] 무드 전용 마스터 루프 빌더
    # 명함 내부 SPA 뷰어 레이아웃을 그대로 유지하되, 카드 하단에 새 창으로 상세보기를 띄울 링크 버튼을 안착시킵니다.
    left_column_html = ""   # 홀수 번호 카드가 누적될 왼쪽 열
    right_column_html = ""  # 짝수 번호 카드가 누적될 오른쪽 열

    for idx, item in enumerate(portfolio_items):
        img_url = item.get("image_url", "").strip()
        desc_text = item.get("description", "").strip()
        
        if not img_url:
            img_url = default_img
            
        raw_name = item.get("image_name", "")
        project_title = os.path.splitext(raw_name)[0] if raw_name else f"Project Piece {idx+1}"
        if project_title.startswith("port_"):
            project_title = project_title.replace("port_", "", 1)

        # 👑 [4단 링크 주입] 각 작품 카드 하단에 새 창으로 독립 CSS 템플릿을 호출하는 "상세 기획서" 단추 장착
        detail_button_html = (
            "<a href='./pages/portfolio.html' target='_blank' "
            "class='inline-block mt-2 text-[9px] text-[#C5A059] border border-[#C5A059]/30 rounded-lg px-2 py-1 hover:bg-[#C5A059]/10 transition-all tracking-wider font-medium serif uppercase'>"
            "View Concept Document ↗</a>"
        )

        if desc_text:
            card_html = (
                "<div class='group mb-6'>"
                "<img src='" + img_url + "' class='rounded-2xl border border-white/5 shadow-2xl transition-all mb-2'>"
                "<h4 class='text-[12px] font-bold text-[#C5A059] tracking-wide px-1 serif italic'>" + project_title + "</h4>"
                "<p class='text-[10px] text-stone-400 font-light leading-relaxed px-1 mt-1 break-keep'>" + desc_text + "</p>"
                + detail_button_html +
                "</div>"
            )
        else:
            card_html = (
                "<div class='group mb-4'>"
                "<img src='" + img_url + "' class='rounded-2xl border border-white/5 shadow-2xl transition-all'>"
                + detail_button_html +
                "</div>"
            )

        if (idx + 1) % 2 != 0:
            left_column_html += card_html
        else:
            right_column_html += card_html

    if not left_column_html and not right_column_html:
        left_column_html = "<div class='group mb-4'><img src='" + default_img + "' class='rounded-2xl border border-white/5 shadow-2xl'></div>"

    main_card_layout_html = (
        "<div id='promoPage' class='hidden w-full h-full flex flex-col relative'>"
        "    <div class='px-6 py-4 border-b border-white/5 bg-[#1a1c1e] flex justify-between items-center'>"
        "        <span class='text-xs font-bold tracking-[3px] text-[#C5A059] serif uppercase'>Selected Pieces</span>"
        "        <button onclick=\"switchPage('mainPage')\" class='text-[10px] text-stone-500 hover:text-white uppercase tracking-wider'>Close</button>"
        "    </div>"
        "    <div class='sub-page-content'>"
        "        <div class='grid grid-cols-2 gap-4'>"
        "            <div class='space-y-4'>" + left_column_html + "</div>"
        "            <div class='space-y-4 pt-8'>" + right_column_html + "</div>"
        "        </div>"
        "    </div>"
        "</div>"
    )

    # 2. 외부 [Big Picture] 순정 카드 핏 정밀 조립 레이어
    if theme_key == "big":
        cards_html = ""
        for idx, item in enumerate(portfolio_items):
            img_url = item.get("image_url", "").strip() or default_img
            desc_text = item.get("description", "").strip()
            raw_name = item.get("image_name", "")
            project_title = os.path.splitext(raw_name)[0] if raw_name else f"Project Piece {idx+1}"
            if project_title.startswith("port_"):
                project_title = project_title.replace("port_", "", 1)

            cards_html += (
                "<div class='bp-magazine-item'>"
                "    <div class='bp-image-container'><img src='" + img_url + "'></div>"
                "    <div class='bp-text-container'>"
                "        <h4 class='bp-item-title'>" + project_title + "</h4>"
                "        <p class='bp-item-desc'>" + desc_text + "</p>"
                "    </div>"
                "</div>"
            )
        
        custom_layout_html = (
            "<div id='promoPage' class=''>"
            "    <div class='bp-premium-header'>"
            "        <h2>" + brand_name + " Portfolio</h2>"
            "        <p class='bp-brand-sub'>Selected Pieces</p>"
            "        <p class='bp-description'>디렉터 " + director_name + "님이 전개하는 고품격 비주얼 디자인 아카이브입니다.</p>"
            "    </div>"
            "    <div class='bp-card-feed-zone'>"
            "        <div class='bp-magazine-layout'>" + cards_html + "</div>"
            "    </div>"
            "</div>"
        )

    # 3. 외부 [Ethereal] 전용 가로 패닝 스크롤 레이아웃 빌더
    elif theme_key == "ethereal":
        cards_html = ""
        for idx, item in enumerate(portfolio_items):
            img_url = item.get("image_url", "").strip() or default_img
            desc_text = item.get("description", "").strip()
            raw_name = item.get("image_name", "")
            project_title = os.path.splitext(raw_name)[0] if raw_name else f"Project Piece {idx+1}"
            if project_title.startswith("port_"):
                project_title = project_title.replace("port_", "", 1)

            cards_html += (
                "<div class='eth-project-card'>"
                "    <div class='eth-img-frame'><img src='" + img_url + "'></div>"
                "    <div class='eth-meta-box'>"
                "        <h4 class='eth-project-title'>" + project_title + "</h4>"
                "        <p class='eth-project-desc'>" + desc_text + "</p>"
                "    </div>"
                "</div>"
            )

        custom_layout_html = (
            "<div id='promoPage' class='w-full h-full flex flex-col relative'>"
            "    <div class='eth-header-bar'>"
            "        <span class='eth-brand-title'>" + brand_name + " ARCHIVE</span>"
            "    </div>"
            "    <div class='eth-gallery-track'>" + cards_html + "</div>"
            "</div>"
        )

    # 4. 외부 [Paradigm Shift] 전용 비대칭 매거진 월 레이아웃 빌더
    elif theme_key == "paradigm":
        cards_html = ""
        for idx, item in enumerate(portfolio_items):
            img_url = item.get("image_url", "").strip() or default_img
            desc_text = item.get("description", "").strip()
            raw_name = item.get("image_name", "")
            project_title = os.path.splitext(raw_name)[0] if raw_name else f"Project Piece {idx+1}"
            if project_title.startswith("port_"):
                project_title = project_title.replace("port_", "", 1)

            cards_html += (
                "<div class='para-card'>"
                "    <div class='para-img-box'><img src='" + img_url + "'></div>"
                "    <div class='para-meta-box'>"
                "        <h4 class='para-title'>" + project_title + "</h4>"
                "        <p class='para-desc'>" + desc_text + "</p>"
                "    </div>"
                "</div>"
            )

        custom_layout_html = (
            "<div id='promoPage' class='w-full h-full flex flex-col relative'>"
            "    <div class='para-close-bar'>"
            "        <span class='para-brand-label'>" + brand_name + " CONCEPT</span>"
            "    </div>"
            "    <div class='para-container'>"
            "        <div class='para-sidebar'>"
            "            <div class='para-sidebar-inner'>"
            "                <h2>Selected<br>Works</h2>"
            "            </div>"
            "        </div>"
            "    </div>"
            "    <div class='para-main-feed'>"
            "        <div class='para-grid'>" + cards_html + "</div>"
            "    </div>"
            "</div>"
        )

    # 테마 동기화 모드일 때 예외 처리 레이아웃 보정
    if theme_key == "sync":
        custom_layout_html = main_card_layout_html.replace("hidden ", "")

    # 👑 [독립 포트폴리오용 순정 액자 코드 패키징]
    # 새 창용 서브 페이지에는 Tailwind 스크립트를 삭제하여 순정 외부 CSS의 컬러가 깨지지 않도록 철저히 격리했습니다.
    final_portfolio_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{brand_name} - Concept Portfolio</title>
    <link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,wght@0,400;1,700&family=Noto+Sans+KR:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --gold: #C5A059; --dark-bg: #121314; }}
        body {{ background-color: var(--dark-bg); font-family: 'Noto Sans KR', sans-serif; min-height: 100vh; margin: 0; padding: 20px; color: #e2e8f0; }}
        .serif {{ font-family: 'Bodoni Moda', serif; }}
        .sub-page-content {{ padding: 10px; background: #121314; }}
        {custom_css_content}
    </style>
</head>
<body class="antialiased">
    <div style="max-w: 800px; margin: 0 auto;">
        {custom_layout_html}
    </div>
</body>
</html>"""

    # 메인 명함 소스코드 최종 마스킹 (메인 명함 뼈대에는 순정 2단 컬럼 구조의 레이아웃 주입)
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
    rendered_code = rendered_code.replace("${FAQ2_DISPLAY}", "display: block;" if f2_q else "display: none !important;")
    rendered_code = rendered_code.replace("${FAQ3_DISPLAY}", "display: block;" if f3_q else "display: none !important;")

    # 👑 마스터 딕셔너리로 두 개의 완공 소스코드를 묶어서 패킹 인계합니다.
    return {
        "main_html": rendered_code,
        "portfolio_html": final_portfolio_html
    }