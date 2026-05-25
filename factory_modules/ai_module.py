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



# 👑 [큰 틀 웹명함 크기 동기화 및 상단 이름 중간 배치 공정] 명함 고유 핏을 복원하고 타이틀을 재정렬합니다.

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



    # 테마 키워드 매핑 매치 (👑 오타 완벽 제거 공정 완료)

    theme_key = "sync"

    if "Big Picture" in portfolio_theme:

        theme_key = "big"

    elif "Ethereal" in portfolio_theme:

        theme_key = "ethereal"

    elif "Paradigm Shift" in portfolio_theme:

        theme_key = "paradigm"



    # 외부 css 로드 파일 구역

    if theme_key != "sync":

        css_file_name = f"{theme_key}.css"

        css_path = os.path.join("factory_modules", "external_themes", css_file_name)

        if not os.path.exists(css_path):

            css_path = os.path.join("external_themes", css_file_name)

        if os.path.exists(css_path):

            with open(css_path, "r", encoding="utf-8") as css_f:

                custom_css_content = css_f.read()



    # 세로 카드 피드형 1열 구조 빌더 (내부 사각틀 스펙은 그대로 유지)

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



        if desc_text:

            card_html = (

                "<div class='centered-card-item' style='width:100%; box-sizing:border-box; background-color:#1a1c1e; border:1px solid rgba(255,255,255,0.1); border-radius:32px; overflow:hidden; box-shadow:0 30px 60px rgba(0,0,0,0.6); display:flex; flex-direction:column; margin-bottom:24px;'>"

                "  <div style='width:100%; position:relative; overflow:hidden; padding:0;'>"

                "    <img src='" + img_url + "' style='width:100% !important; height:auto !important; max-height:none !important; object-fit:contain !important; display:block; margin:0 auto;'>"

                "  </div>"

                "  <div style='padding:16px; background:#1a1c1e; text-align:center; border-top:1px solid rgba(255,255,255,0.05);'>"

                "    <h4 class='text-[13px] font-bold text-[#C5A059] tracking-wide serif italic'>" + project_title + "</h4>"

                "    <p class='text-[10px] text-stone-400 font-light leading-relaxed mt-1 break-keep' style='max-width:280px; margin:4px auto 0 auto;'>" + desc_text + "</p>"

                "  </div>"

                "</div>"

            )

        else:

            card_html = (

                "<div class='centered-card-item' style='width:100%; box-sizing:border-box; background-color:#1a1c1e; border:1px solid rgba(255,255,255,0.1); border-radius:32px; overflow:hidden; box-shadow:0 30px 60px rgba(0,0,0,0.6); margin-bottom:20px; padding:0;'>"

                "  <img src='" + img_url + "' style='width:100% !important; height:auto !important; max-height:none !important; object-fit:contain !important; display:block; margin:0 auto;'>"

                "</div>"

            )

        feed_cards_html += card_html



    if not feed_cards_html:

        feed_cards_html = "<div class='centered-card-item' style='width:100%; background-color:#1a1c1e; border:1px solid rgba(255,255,255,0.1); border-radius:32px; overflow:hidden; margin:0 auto;'><img src='" + default_img + "' style='width:100%; height:auto;'></div>"



    # 👑 [개미 아카이브 지붕 유지] 움직임 없이 외곽틀 위에 우아하게 수평 고정되는 브랜드 텍스트

    portfolio_main_title_html = (

        "<div style='text-align:center; padding:10px 0 2px 0; background:transparent; width:100%; max-width:410px; margin:0 auto;'>"

        "    <p class='text-[#C5A059] text-[10px] font-bold uppercase tracking-[5px]' style='margin:0;'>" + brand_name + " ARCHIVE</p>"

        "</div>"

    )



    # 👑 [리모컨 외부 CSS 'Big Picture' 연동 전용 컬러 칩 변형 구역]

    # - 구조 변형을 완전히 배제하고, 마음에 들어 하신 오리지널 2중 사각 라운드 구도를 100% 똑같이 사수합니다.

    # - 👑 [2번 안 최종 주입]: 온기가 도는 프리미엄 웜 그레이(#2a2b2d) 배경과 차콜 그레이(#333537) 카드판 영역을 구축하여 본진 명함과의 완벽한 일관성 핏을 완성했습니다.

    if theme_key == "big":

        big_style_cards_html = ""

        for idx, item in enumerate(portfolio_items):

            img_url = item.get("image_url", "").strip() or default_img

            desc_text = item.get("description", "").strip()

            raw_name = item.get("image_name", "")

            project_title = os.path.splitext(raw_name)[0] if raw_name else f"Project Piece {idx+1}"

            if project_title.startswith("port_"):

                project_title = project_title.replace("port_", "", 1)



            if desc_text:

                card_html = (

                    "<div class='centered-card-item' style='width:100%; box-sizing:border-box; background-color:#333537; border:1px solid rgba(255,255,255,0.06); border-radius:32px; overflow:hidden; box-shadow:0 30px 60px rgba(0,0,0,0.5); display:flex; flex-direction:column; margin-bottom:24px;'>"

                    "  <div style='width:100%; position:relative; overflow:hidden; padding:0;'>"

                    "    <img src='" + img_url + "' style='width:100% !important; height:auto !important; max-height:none !important; object-fit:contain !important; display:block; margin:0 auto;'>"

                    "  </div>"

                    "  <div style='padding:16px; background:#333537; text-align:center; border-top:1px solid rgba(255,255,255,0.04);'>"

                    "    <h4 class='text-[13px] font-bold text-[#C5A059] tracking-wide serif italic'>" + project_title + "</h4>"

                    "    <p class='text-[10px] text-stone-300 font-light leading-relaxed mt-1 break-keep' style='max-width:280px; margin:4px auto 0 auto;'>" + desc_text + "</p>"

                    "  </div>"

                    "</div>"

                )

            else:

                card_html = (

                    "<div class='centered-card-item' style='width:100%; box-sizing:border-box; background-color:#333537; border:1px solid rgba(255,255,255,0.06); border-radius:32px; overflow:hidden; box-shadow:0 30px 60px rgba(0,0,0,0.5); margin-bottom:20px; padding:0;'>"

                    "  <img src='" + img_url + "' style='width:100% !important; height:auto !important; max-height:none !important; object-fit:contain !important; display:block; margin:0 auto;'>"

                    "</div>"

                )

            big_style_cards_html += card_html

        custom_layout_html = big_style_cards_html

    else:

        custom_layout_html = feed_cards_html



    # 👑 [오리지날 본진 직통 초고속 매싱 레이아웃]

    main_card_layout_html = (

        "<div id='promoPage' class='hidden w-full h-full flex flex-col relative bg-[#1a1c1e]'>"

        "    <div style='display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 14px 20px 12px 20px; border-bottom: 1px solid rgba(255,255,255,0.05); background: #1a1c1e; z-index: 100;'>"

        "        <span style='font-size: 10px; font-weight: bold; tracking-spacing: 2px; color: #C5A059; text-align: left;' class='serif uppercase'>Selected Pieces</span>"

        "        <span style='font-size: 14px; font-weight: 700; color: #fff; text-align: center; font-family: \"Noto Sans KR\", sans-serif; tracking-wide: 1px; line-height: 1;'>" + director_name + "</span>"

        "        <button onclick=\"switchPage('mainPage')\" style='font-size: 10px; font-weight: bold; color: #888; text-decoration: none; text-transform: uppercase; tracking-wider: 1px; text-align: right; background: none; border: none; cursor: pointer;' onmouseover=\"this.style.color='#fff'\" onmouseout=\"this.style.color='#888'\">Close ✕</button>"

        "    </div>"

        "    <div class='sub-page-content overflow-y-auto px-5 py-4' style='max-height: 90vh; scrollbar-width: none; -ms-overflow-style: none;'>"

        "        <div class='flex flex-col space-y-6 items-center'>" + feed_cards_html + "</div>"

        "    </div>"

        "</div>"

    )



    # 완공 명함 동기화 핏 빌더 (배포 파일 생성 규격 보존)

    final_portfolio_html = f"""<!DOCTYPE html>

<html lang="ko">

<head>

    <meta charset="UTF-8">

    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

    <title>{brand_name} - Portfolio Archive</title>

    <script src="https://cdn.tailwindcss.com"></script>

    <link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,wght@0,400;1,700&family=Noto+Sans+KR:wght@300;400;700&display=swap" rel="stylesheet">

    <style>

        :root {{ --gold: #C5A059; --dark-bg: {"#2a2b2d" if theme_key == "big" else "#121314"}; }}

        body {{ background-color: var(--dark-bg); font-family: 'Noto Sans KR', sans-serif; min-height: 100vh; margin: 0; padding: 20px 15px 30px 15px; display: flex; align-items: center; justify-content: center; flex-direction: column; overflow-y: auto !important; }}

        .serif {{ font-family: 'Bodoni Moda', serif; }}

        .centered-card {{

            width: 100%;

            max-width: 410px;

            height: 82vh;

            max-height: 780px !important;

            background-color: {"#333537" if theme_key == "big" else "#1a1c1e"};

            border: 1px solid {"rgba(255, 255, 255, 0.06)" if theme_key == "big" else "rgba(255, 255, 255, 0.1)"};

            border-radius: 32px;

            box-shadow: 0 40px 80px rgba(0, 0, 0, 0.8);

            overflow: hidden;

            display: flex;

            flex-direction: column;

            position: relative;

            margin-top: 8px;

        }}

        .sub-page-content {{ flex: 1; padding: 16px; background: packing: {"#333537" if theme_key == "big" else "#1a1c1e"}; }}

        .sub-page-content::-webkit-scrollbar {{ display: none; }}

        {custom_css_content}

    </style>

</head>

<body class="antialiased text-stone-200" style="box-sizing: border-box;">

    {portfolio_main_title_html}

    <div class="centered-card">

        <div style="display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 14px 20px 12px 20px; border-bottom: 1px solid {"rgba(255,255,255,0.04)" if theme_key == "big" else "rgba(255,255,255,0.05)"}; background: {"#333537" if theme_key == "big" else "#1a1c1e"}; z-index: 100;">

            <span style="font-size: 10px; font-weight: bold; tracking-content: 2px; color: var(--gold); text-align: left;" class="serif uppercase">Selected Pieces</span>

            <span style="font-size: 14px; font-weight: 700; color: #fff; text-align: center; font-family: 'Noto Sans KR', sans-serif; tracking-wide: 1px; line-height: 1;">{director_name}</span>

            <a href="../index.html" style="font-size: 10px; font-weight: bold; color: #888; text-decoration: none; text-transform: uppercase; tracking-wider: 1px; text-align: right;" onmouseover="this.style.color='#fff'" onmouseout="this.style.color='#888'">Close ✕</a>

        </div>

        <div class="sub-page-content overflow-y-auto" style="scrollbar-width: none; -ms-overflow-style: none;">

            <div class="flex flex-col space-y-5 items-center">{custom_layout_html}</div>

        </div>

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



    # 👑 [하이브리드 포트폴리오 버튼 자동 치환 및 분기 엔진 주입 세팅]

    if theme_key == "sync":

        portfolio_btn_html = '<button onclick="switchPage(\'promoPage\')" class="bg-stone-800 text-stone-200 font-bold text-[11px] py-3 rounded-2xl border border-white/5 tracking-widest uppercase hover:bg-stone-700 transition-colors text-center block w-full">Portfolio</button>'

    else:

        portfolio_btn_html = '<a href="./pages/portfolio.html" target="_blank" class="bg-stone-800 text-stone-200 font-bold text-[11px] py-3 rounded-2xl border border-white/5 tracking-widest uppercase hover:bg-stone-700 transition-colors text-center block w-full">Portfolio</a>'

    

    rendered_code = rendered_code.replace("${PORTFOLIO_BUTTON}", portfolio_btn_html)



    # 연락처 및 기타 정보

    rendered_code = rendered_code.replace("${PHONE}", contact_info.get("phone", ""))

    rendered_code = rendered_code.replace("${EMAIL}", contact_info.get("email", ""))

    

    # 👑 [4대 SNS 프리미엄 동적 치환 마스킹 파이프라인 엔진 가동]

    # - 리모컨 GUI에서 정밀하게 가공되어 적재된 4대 핵심 데이터를 순서대로 안전하게 매싱합니다.

    sns1_url = contact_info.get("instagram", "").strip() or "#"

    sns2_url = contact_info.get("naver_blog", "").strip() or "#"

    sns3_url = contact_info.get("kakao_url", "").strip() or "#"

    sns4_url = contact_info.get("telegram_url", "").strip() or "#" # 형규님 매핑 규칙: 유튜브 주소 바인딩

    

    rendered_code = rendered_code.replace("${SNS1_TYPE}", "INSTAGRAM")

    rendered_code = rendered_code.replace("${SNS1_URL}", sns1_url)

    rendered_code = rendered_code.replace("${SNS1_DISPLAY}", "display: flex;" if sns1_url != "#" else "display: none !important;")



    rendered_code = rendered_code.replace("${SNS2_TYPE}", "NAVER_BLOG")

    rendered_code = rendered_code.replace("${SNS2_URL}", sns2_url)

    rendered_code = rendered_code.replace("${SNS2_DISPLAY}", "display: flex;" if sns2_url != "#" else "display: none !important;")



    rendered_code = rendered_code.replace("${SNS3_TYPE}", "KAKAO_TALK")

    rendered_code = rendered_code.replace("${SNS3_URL}", sns3_url)

    rendered_code = rendered_code.replace("${SNS3_DISPLAY}", "display: flex;" if sns3_url != "#" else "display: none !important;")



    rendered_code = rendered_code.replace("${SNS4_TYPE}", "YOUTUBE")

    rendered_code = rendered_code.replace("${SNS4_URL}", sns4_url)

    rendered_code = rendered_code.replace("${SNS4_DISPLAY}", "display: flex;" if sns4_url != "#" else "display: none !important;")



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



    # 👑 [신설: 주소 자동화 칩 주입 엔진 파이프라인]

    # - 템플릿 코드에 파놓은 ${brand_url_name} 구멍을 실시간 브랜드 영문명(소문자)으로 자동 바꿔치기합니다.

    rendered_code = rendered_code.replace("${brand_url_name}", brand_name.strip().lower())



    # 👑 [수정의 핵심 가벨 포인트] 

    # 리모컨 설정 테마가 오리지널('sync') 상태이면 'portfolio_html'을 빈 문자열("")로 반환하여 별도 물리 파일 생성을 완벽히 차단하고,

    # 외부 테마일 때만 정상적으로 'final_portfolio_html' 소스코드를 태워 배송 공정으로 넘깁니다.

    return {

        "main_html": rendered_code,

        "portfolio_html": "" if theme_key == "sync" else final_portfolio_html

    }