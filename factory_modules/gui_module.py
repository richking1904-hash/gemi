import customtkinter as ctk
from tkinter import filedialog
import os
import requests
from dotenv import load_dotenv

# 👑 [브릿지 연동을 위한 모듈 로드]
from factory_modules.db_module import update_telegram_settings
from tkinter import messagebox

load_dotenv()

# 환경 변수에서 설정값 호출
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

dropped_files = []
final_payload = None

# 동적 포트폴리오 항목들을 관리할 마스터 리스트
portfolio_items = []

def browse_files_manual():
    global dropped_files
    file_paths = filedialog.askopenfilenames(
        title="포트폴리오 이미지 또는 자료 선택 (다중 선택 가능)",
        filetypes=[("지원하는 모든 파일", "*.png *.jpg *.jpeg *.gif *.xlsx *.pdf *.txt"),
                   ("이미지 파일", "*.png *.jpg *.jpeg *.gif"),
                   ("텍스트 가이드라인", "*.txt")]
    )
    if file_paths:
        for path in file_paths:
            if path not in dropped_files:
                dropped_files.append(path)
        drop_zone_label.configure(text=f"📊 총 {len(dropped_files)}개의 자산이 안전하게 로드되었습니다.", text_color="#64B5F6")
       
        # 👑 [동기화 마스터 패치]
        # 통합 자산 버튼을 누르면 대문 이미지뿐만 아니라, 아래 동적 생성된 포트폴리오 모든 칸의 드롭다운 메뉴에도 파일 이름이 실시간 동기화됩니다.
        file_names = [os.path.basename(f) for f in dropped_files]
        main_image_combobox.configure(values=file_names)
       
        # 포트폴리오 칸들의 드롭다운 목록도 한꺼번에 갱신
        img_nodes = [f for f in file_names if not f.endswith('.txt')]
        for item in portfolio_items:
            item._combobox.configure(values=img_nodes)
            # 만약 기존 선택값이 비어있었다면 첫 이미지로 자동 임시 세팅
            if item._combobox.get() == "먼저 하단 자산을 추가해 주세요" and img_nodes:
                item._combobox.set(img_nodes[0])
       
        if img_nodes:
            main_image_combobox.set(img_nodes[-1])
        elif file_names:
            main_image_combobox.set(file_names[-1])
           
        status_label.configure(text=f"➕ {len(file_paths)}개의 파일이 시스템 자산에 추가되었습니다.", text_color="#A5D6A7")

def reset_file_list():
    global dropped_files
    dropped_files.clear()
    drop_zone_label.configure(text="아래 버튼을 눌러 파일들을 추가하세요\n(png, jpg, txt 다중 선택 지원)", text_color="#888888")
   
    main_image_combobox.configure(values=["먼저 파일을 추가해 주세요"])
    main_image_combobox.set("먼저 파일을 추가해 주세요")
   
    for item in portfolio_items:
        item._combobox.configure(values=["먼저 하단 자산을 추가해 주세요"])
        item._combobox.set("먼저 하단 자산을 추가해 주세요")
       
    status_label.configure(text="🧹 로드된 파일 목록이 초기화되었습니다.", text_color="#FFB74D")

# 👑 포트폴리오 아이템을 우측 프레임에 동적으로 추가하는 함수 (드롭다운 버전)
def add_portfolio_item_ui():
    item_idx = len(portfolio_items) + 1
   
    # 개별 포트폴리오를 감싸는 서브 프레임 테두리
    item_frame = ctk.CTkFrame(portfolio_scroll_inner, fg_color="#1E1E1E", border_width=1, border_color="#333333")
    item_frame.pack(fill="x", pady=6, padx=5)
   
    # 상단 헤더 라인
    header_label = ctk.CTkLabel(item_frame, text=f"🖼️ 포트폴리오 프로젝트 {item_idx}번", font=("Helvetica", 11, "bold"), text_color="#C5A059")
    header_label.pack(anchor="w", padx=10, pady=(6, 2))
   
    # 👑 [개조 핵심] 파일 탐색기 버튼을 지우고 대표사진 지정과 똑같은 "선택 드롭다운(ComboBox)" 배치
    ctk.CTkLabel(item_frame, text="📸 작품 이미지 파일 선택:", font=("Helvetica", 10), text_color="#AAAAAA").pack(anchor="w", padx=10)
   
    # 현재 로드된 이미지 에셋이 있다면 가져오고 없으면 안내 문구 출력
    file_names = [os.path.basename(f) for f in dropped_files]
    img_nodes = [f for f in file_names if not f.endswith('.txt')]
    initial_values = img_nodes if img_nodes else ["먼저 하단 자산을 추가해 주세요"]
   
    item_combobox = ctk.CTkComboBox(item_frame, values=initial_values, width=380, fg_color="#2A2A2A")
    item_combobox.pack(fill="x", padx=10, pady=(2, 6))
    if img_nodes:
        item_combobox.set(img_nodes[0])
    else:
        item_combobox.set("먼저 하단 자산을 추가해 주세요")
   
    # 2단계: 기획 서사 입력란
    ctk.CTkLabel(item_frame, text="✍️ 디자인 기획 서사 및 의도 (서사 생략 시 미니멀 갤러리로 자동 전환):", font=("Helvetica", 10), text_color="#AAAAAA").pack(anchor="w", padx=10, pady=(4, 0))
    desc_textbox = ctk.CTkTextbox(item_frame, height=45, fg_color="#121314", border_width=1, border_color="#2A2A2A", font=("Noto Sans KR", 10))
    desc_textbox.pack(fill="x", padx=10, pady=(2, 8))
   
    # 데이터 매칭용 속성 바인딩 수집 장부 개조
    item_frame._combobox = item_combobox
    item_frame._desc_widget = desc_textbox
    portfolio_items.append(item_frame)

# 👑 [신설 구역] 리모컨에서 직접 텔레그램 동적 연동 함수를 호출하는 파이프라인 브릿지
def on_telegram_save_click():
    b_name = brand_name_entry.get().strip()
    tg_token = tg_token_entry.get().strip()
    tg_id = tg_id_entry.get().strip()
    
    if not b_name:
        messagebox.showwarning("필수 입력 누락", "텔레그램 설정을 바인딩하기 위해선 상단의 '브랜드명'이 필수적으로 기입되어야 합니다.")
        return
    if not tg_token or not tg_id:
        messagebox.showwarning("입력 누락", "동적 알림 연동을 위한 텔레그램 봇 토큰과 사용자 ID(Chat ID)를 입력해주세요.")
        return
        
    status_label.configure(text=f"✈️ Supabase 장부에 [{b_name}]의 텔레그램 연동 설정을 동적 업데이트 중...", text_color="#64B5F6")
    app.update_idletasks()
    
    # 앞서 업데이트한 db_module의 함수 호출 및 결과 검증
    success = update_telegram_settings(b_name, tg_token, tg_id)
    if success:
        messagebox.showinfo("연동 완료", f"🎉 [{b_name}] 브랜드의 실시간 텔레그램 알림 무선 채널이 완벽하게 업데이트되었습니다!")
        status_label.configure(text=f"✅ [{b_name}] 텔레그램 파이프라인 개통 성공.", text_color="#A5D6A7")
    else:
        messagebox.showerror("연동 실패", "Supabase 데이터베이스 통신 중 오류가 발생했습니다. 콘솔 창 로그를 확인하세요.")
        status_label.configure(text="❌ 텔레그램 장부 업로드 실패.", text_color="#FF5252")

def on_submit_click():
    global final_payload
    if not name_entry.get().strip() or not brand_name_entry.get().strip():
        status_label.configure(text="❌ 필수 정보(디렉터 이름, brand_name)를 입력해야 빌드가 시작됩니다.", text_color="#FF5252")
        return

    input_url = url_name_entry.get().strip()
    clean_url = "".join(c.lower() for c in input_url if c.isalnum() or c in ["-", "_"]).strip()

    if clean_url:
        status_label.configure(text="🔍 전 세계 Vercel 주소 장부에서 중복 여부를 실시간 조회 중...", text_color="#FFB74D")
        app.update_idletasks()
        check_url = f"https://{clean_url}.vercel.app"
        try:
            response = requests.head(check_url, timeout=3)
            if response.status_code < 400:
                status_label.configure(text=f"❌ 중복 주소! [{clean_url}]은 이미 다른 사람이 쓰고 있습니다.", text_color="#FF5252")
                return
        except Exception:
            pass

    selected_main_name = main_image_combobox.get()
    main_image_full_path = ""
    for path in dropped_files:
        if os.path.basename(path) == selected_main_name:
            main_image_full_path = path
            break

    # 👑 [동적 드롭다운 데이터 역추적 패치]
    final_portfolio_list = []
    for item in portfolio_items:
        chosen_file_name = item._combobox.get()
        desc_t = item._desc_widget.get("1.0", "end").strip()
       
        # 드롭다운에서 선택된 파일 이름을 가지고 진짜 컴퓨터 내부 절대 경로(Absolute Path)를 역 추적합니다.
        img_p = ""
        if chosen_file_name and chosen_file_name != "먼저 하단 자산을 추가해 주세요":
            for path in dropped_files:
                if os.path.basename(path) == chosen_file_name:
                    img_p = path
                    break
                   
        if img_p or desc_t:
            final_portfolio_list.append({
                "image_path": img_p,
                "image_name": chosen_file_name if img_p else "",
                "description": desc_t
            })

    # 👑 [슈파베이스 데이터베이스 다이렉트 연동 전용 매싱 장부 개조 완성]
    # - 기존의 가변형 구조를 지우고 슈파베이스 gemi_clients 테이블의 4대 핵심 컬럼과 1:1로 완벽 동기화 시켰습니다.
    final_payload = {
        "user_info": {
            "name": name_entry.get().strip(),
            "brand_name": brand_name_entry.get().strip(),
            "introduction": introduction_entry.get().strip(),
            "custom_url_name": clean_url
        },
        "contact_info": {
            "phone": phone_entry.get().strip(),
            "email": email_entry.get().strip(),
            "instagram": instagram_entry.get().strip(),
            "naver_blog": naver_blog_entry.get().strip(),
            "kakao_url": kakao_entry.get().strip(),
            "telegram_url": youtube_entry.get().strip()  # 형규님 규칙: 텔레그램 컬럼 자리에 유튜브 주소 안전 적재
        },
        "faq_info": {
            "faq1_q": faq_q1_entry.get().strip(), "faq1_a": faq_a1_entry.get().strip(),
            "faq2_q": faq_q2_entry.get().strip(), "faq2_a": faq_a2_entry.get().strip(),
            "faq3_q": faq_q3_entry.get().strip(), "faq3_a": faq_a3_entry.get().strip()
        },
        "design_preference": {
            "style": design_style_combobox.get()
        },
        # 👑 [신설 조립 연동 파이프라인] 리모컨에서 지정한 외부 포트폴리오 테마 칩 데이터를 패키지에 바인딩
        "portfolio_theme": portfolio_style_combobox.get(),
        "portfolio_items": final_portfolio_list,
        "assets": {
            "all_dropped_files": dropped_files,
            "main_image_path": main_image_full_path
        },
        "main_image_path": main_image_full_path,
        "ai_custom_requests": {
            "special_notes": "가이드라인 파일 기반 원격 지능형 스트리밍 버전 가동"
        }
    }
    app.quit()
    app.destroy()

def export_gui_data():
    global app, final_payload
    app.mainloop()
    return final_payload

# 대시보드 스케일에 맞춘 프리미엄 와이드 규격 세팅
app = ctk.CTk()
app.title("GeMi WebCard Director Studio v2.5")
app.geometry("960x700")
ctk.set_appearance_mode("dark")

# 상단 타이틀 배너 영역
title_label = ctk.CTkLabel(app, text="GeMi 명함 공장 프리미엄 대시보드 리모컨", font=("Helvetica", 20, "bold"), text_color="#C5A059")
title_label.pack(pady=(12, 5))

# 가로 2분할을 지탱하는 좌/우 분리형 캔버스 프레임 구축
master_split_frame = ctk.CTkFrame(app, fg_color="transparent")
master_split_frame.pack(fill="both", expand=True, padx=15, pady=5)

left_panel = ctk.CTkScrollableFrame(master_split_frame, width=440, fg_color="#17191a", border_width=1, border_color="#2A2D2E")
left_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))

right_panel = ctk.CTkFrame(master_split_frame, width=440, fg_color="#17191a", border_width=1, border_color="#2A2D2E")
right_panel.pack(side="right", fill="both", expand=True, padx=(8, 0))

# ------------------------------------------------------------------
# ◀️ 좌측 프레임 공정라인: 디렉터 마스터 프로필 정보 및 에셋 제어실
# ------------------------------------------------------------------
ctk.CTkLabel(left_panel, text="👤 디렉터 기초 정보 관리", font=("Helvetica", 13, "bold"), text_color="#C5A059").pack(anchor="w", pady=(5, 10))

ctk.CTkLabel(left_panel, text="디렉터 이름 (필수):").pack(anchor="w")
name_entry = ctk.CTkEntry(left_panel, width=400, fg_color="#2A2A2A")
name_entry.pack(pady=(2, 8)); name_entry.insert(0, "장형규")

ctk.CTkLabel(left_panel, text="브랜드명 (필수):").pack(anchor="w")
brand_name_entry = ctk.CTkEntry(left_panel, width=400, fg_color="#2A2A2A")
brand_name_entry.pack(pady=(2, 8)); brand_name_entry.insert(0, "GeMi")

ctk.CTkLabel(left_panel, text="브랜드 한줄 소개:").pack(anchor="w")
introduction_entry = ctk.CTkEntry(left_panel, width=400, fg_color="#2A2A2A")
introduction_entry.pack(pady=(2, 10)); introduction_entry.insert(0, "Quiet Luxury 감성의 프리미엄 브랜드 및 graphic 디자인 스튜디오")

# [A안 반영 구역] 프로필 하단에 대문 대표 이미지 지정 콤보박스
ctk.CTkLabel(left_panel, text="👑 명함 대문 대표 이미지 지정:", text_color="#C5A059", font=("Helvetica", 11, "bold")).pack(anchor="w", pady=(5, 0))
main_image_combobox = ctk.CTkComboBox(left_panel, values=["먼저 하단 버튼으로 파일을 추가해 주세요"], width=400, fg_color="#2A2A2A")
main_image_combobox.pack(pady=(2, 12))

ctk.CTkLabel(left_panel, text="🌐 원하는 웹사이트 주소 이름 (선택):", text_color="#64B5F6").pack(anchor="w")
url_name_entry = ctk.CTkEntry(left_panel, width=400, fg_color="#1E293B", border_color="#3B82F6")
url_name_entry.pack(pady=(2, 12))

# 연락처 하위 세부 라인 그리드 정렬
contact_grid = ctk.CTkFrame(left_panel, fg_color="transparent")
contact_grid.pack(fill="x", pady=5)
ctk.CTkLabel(contact_grid, text="📞 휴대폰 번호:").grid(row=0, column=0, sticky="w")
ctk.CTkLabel(contact_grid, text="✉️ 이메일 주소:", text_color="#b0b0b0").grid(row=0, column=1, sticky="w", padx=15)
phone_entry = ctk.CTkEntry(contact_grid, width=190, fg_color="#2A2A2A")
phone_entry.grid(row=1, column=0, pady=2); phone_entry.insert(0, "010-0000-0000")
email_entry = ctk.CTkEntry(contact_grid, width=190, fg_color="#2A2A2A")
email_entry.grid(row=1, column=1, padx=15, pady=2); email_entry.insert(0, "gemi_design@naver.com")

# 👑 [리모컨 전용 4대 SNS 입력창 확장 안착 구역]
# - 형규님이 정하신 4대 공식 채널의 전용 독립 입력 필드를 콤보박스 없이 정갈한 4선 전용 트랙으로 늘렸습니다.
ctk.CTkLabel(left_panel, text="📷 인스타그램 주소 (Instagram):", text_color="#AAAAAA").pack(anchor="w", pady=(6,0))
instagram_entry = ctk.CTkEntry(left_panel, width=400, fg_color="#2A2A2A")
instagram_entry.pack(pady=(2, 4)); instagram_entry.insert(0, "https://instagram.com/")

ctk.CTkLabel(left_panel, text="💚 네이버 블로그 주소 (Naver Blog):", text_color="#AAAAAA").pack(anchor="w", pady=(4,0))
naver_blog_entry = ctk.CTkEntry(left_panel, width=400, fg_color="#2A2A2A")
naver_blog_entry.pack(pady=(2, 4)); naver_blog_entry.insert(0, "https://blog.naver.com/")

ctk.CTkLabel(left_panel, text="💛 카카오톡 채널 주소 (KakaoTalk):", text_color="#AAAAAA").pack(anchor="w", pady=(4,0))
kakao_entry = ctk.CTkEntry(left_panel, width=400, fg_color="#2A2A2A")
kakao_entry.pack(pady=(2, 4)); kakao_entry.insert(0, "https://pf.kakao.com/")

ctk.CTkLabel(left_panel, text="❤️ 유튜브 채널 주소 (YouTube):", text_color="#AAAAAA").pack(anchor="w", pady=(4,0))
youtube_entry = ctk.CTkEntry(left_panel, width=400, fg_color="#2A2A2A")
youtube_entry.pack(pady=(2, 8)); youtube_entry.insert(0, "https://youtube.com/")

# 무드 프리셋 스타일러
ctk.CTkLabel(left_panel, text="✨ 명함 기본 무드 스타일 지정:").pack(anchor="w", pady=(8,0))
design_style_combobox = ctk.CTkComboBox(left_panel, values=["[차분한 미니멀]", "[고급스러운 호텔 타월 감성]", "[모던 스튜디오]", "[네추럴 그린]"], width=400, fg_color="#2A2A2A")
design_style_combobox.pack(pady=(2, 12)); design_style_combobox.set("[차분한 미니멀]")

# 👑 [A안 반영 구역 독립 이식 완성] 텔레그램 실시간 무선 알림 동적 세팅을 위한 하이엔드 입력 섹션 프레임
tg_section_frame = ctk.CTkFrame(left_panel, fg_color="#1E1E1E", border_width=1, border_color="#333333")
tg_section_frame.pack(fill="x", pady=(10, 15), padx=5)

ctk.CTkLabel(tg_section_frame, text="✈️ 테스터 전용 실시간 텔레그램 알림 세팅", font=("Helvetica", 12, "bold"), text_color="#C5A059").pack(anchor="w", padx=10, pady=(8, 4))

ctk.CTkLabel(tg_section_frame, text="텔레그램 봇 토큰 (Bot Token):", font=("Helvetica", 10), text_color="#AAAAAA").pack(anchor="w", padx=10)
tg_token_entry = ctk.CTkEntry(tg_section_frame, width=380, fg_color="#2A2A2A", placeholder_text="봇 토큰 문자열을 입력하세요")
tg_token_entry.pack(pady=(2, 6), padx=10)

ctk.CTkLabel(tg_section_frame, text="사용자 아이디 (Chat ID):", font=("Helvetica", 10), text_color="#AAAAAA").pack(anchor="w", padx=10)
tg_id_entry = ctk.CTkEntry(tg_section_frame, width=380, fg_color="#2A2A2A", placeholder_text="숫자로 된 Chat ID를 입력하세요")
tg_id_entry.pack(pady=(2, 10), padx=10)

btn_save_tg = ctk.CTkButton(tg_section_frame, text="✈️ 텔레그램 설정 동적 반영", font=("Helvetica", 11, "bold"), fg_color="#C5A059", text_color="#000000", hover_color="#b38f4b", command=on_telegram_save_click, width=380, height=28)
btn_save_tg.pack(pady=(0, 10), padx=10)


# ------------------------------------------------------------------
# ▶️ 우측 프레임 공정라인: AI 지능형 FAQ 단추 및 포트폴리오 가변 제어실
# ------------------------------------------------------------------
ctk.CTkLabel(right_panel, text="⚙️ AI FAQ 및 Portfolio 제어실", font=("Helvetica", 13, "bold"), text_color="#C5A059").pack(anchor="w", padx=15, pady=(10, 5))

# 우측 상단 고정: FAQ 셋업 구역
faq_box = ctk.CTkFrame(right_panel, fg_color="transparent")
faq_box.pack(fill="x", padx=15, pady=2)
faq_q1_entry = ctk.CTkEntry(faq_box, width=210, placeholder_text="질문 1", fg_color="#2A2A2A"); faq_q1_entry.grid(row=0, column=0, pady=2); faq_q1_entry.insert(0, "포트폴리오 제작 기간이 얼마나 걸리나요?")
faq_a1_entry = ctk.CTkEntry(faq_box, width=210, placeholder_text="답변 1", fg_color="#2A2A2A"); faq_a1_entry.grid(row=0, column=1, padx=10, pady=2); faq_a1_entry.insert(0, "기본형의 경우 약 2주, 맞춤형 기획 포트폴리오는 영업일 기준 3~4주 소요됩니다.")
faq_q2_entry = ctk.CTkEntry(faq_box, width=210, placeholder_text="질문 2", fg_color="#2A2A2A"); faq_q2_entry.grid(row=1, column=0, pady=2); faq_q2_entry.insert(0, "상세페이지 디자인 단가가 궁금합니다.")
faq_a2_entry = ctk.CTkEntry(faq_box, width=210, placeholder_text="답변 2", fg_color="#2A2A2A"); faq_a2_entry.grid(row=1, column=1, padx=10, pady=2); faq_a2_entry.insert(0, "기본형 단가는 50만원선에서 시작하며 기획 볼륨 등에 따라 조율됩니다.")
faq_q3_entry = ctk.CTkEntry(faq_box, width=210, placeholder_text="질문 3", fg_color="#2A2A2A"); faq_q3_entry.grid(row=2, column=0, pady=2); faq_q3_entry.insert(0, "작업 의뢰는 어떻게 신청하나요?")
faq_a3_entry = ctk.CTkEntry(faq_box, width=210, placeholder_text="답변 3", fg_color="#2A2A2A"); faq_a3_entry.grid(row=2, column=1, padx=10, pady=2); faq_a3_entry.insert(0, "Contact 메뉴에서 Brief 양식을 작성하시면 24시간 이내 연락을 드립니다.")

# 우측 하단: 무한 스크롤이 탑재된 포트폴리오 동적 추가 제어판
portfolio_container = ctk.CTkFrame(right_panel, fg_color="transparent")
portfolio_container.pack(fill="both", expand=True, padx=15, pady=(8, 10))

# 👑 [A안 독립 증설] 기존 테마 가치를 지키면서 포트폴리오 서브페이지만 바꿀 템플릿 드롭다운 배치
ctk.CTkLabel(portfolio_container, text="🎨 포트폴리오 서브 페이지 전용 템플릿 지정:", font=("Helvetica", 11, "bold"), text_color="#C5A059").pack(anchor="w", pady=(0, 2))
portfolio_style_combobox = ctk.CTkComboBox(
    portfolio_container,
    values=["[명함 테마와 동기화]", "Big Picture (HTML5 UP)", "Ethereal (HTML5 UP)", "Paradigm Shift (HTML5 UP)"],
    width=410, fg_color="#2A2A2A"
)
portfolio_style_combobox.pack(anchor="w", pady=(0, 10))
portfolio_style_combobox.set("[명함 테마와 동기화]")

# [+ 추가] 조작 헤더 버튼
portfolio_ctrl_bar = ctk.CTkFrame(portfolio_container, fg_color="transparent")
portfolio_ctrl_bar.pack(fill="x", pady=(0, 4))
ctk.CTkLabel(portfolio_ctrl_bar, text="📁 가변형 작품 목록 관리", font=("Helvetica", 11, "bold")).pack(side="left")

add_item_btn = ctk.CTkButton(portfolio_ctrl_bar, text="➕ 포트폴리오 항목 추가", width=140, height=24, font=("Helvetica", 11, "bold"), fg_color="#C5A059", text_color="#000000", hover_color="#b38f4b", command=add_portfolio_item_ui)
add_item_btn.pack(side="right")

# 작품 카드가 누적되어 쌓일 내부 스크롤 프레임 영역
portfolio_scroll_inner = ctk.CTkScrollableFrame(portfolio_container, fg_color="#121314", height=200, border_width=1, border_color="#1A1C1E")
portfolio_scroll_inner.pack(fill="both", expand=True)

# 초기 로드 시 기본적으로 2개의 프로젝트 기본 빈 슬롯을 생성해 둡니다.
add_portfolio_item_ui()
add_portfolio_item_ui()


# ------------------------------------------------------------------
# ⚙️ 하단 고정 컨트롤러 영역 (종합 에셋 스토리지 등록 창 및 마스터 스위치)
# ------------------------------------------------------------------
bottom_master_frame = ctk.CTkFrame(app, fg_color="#17191a", height=130, border_width=1, border_color="#2A2D2E")
bottom_master_frame.pack_propagate(False)
bottom_master_frame.pack(side="bottom", fill="x", padx=15, pady=(5, 15))

drop_zone_frame = ctk.CTkFrame(bottom_master_frame, width=900, height=42, fg_color="#101112")
drop_zone_frame.pack_propagate(False); drop_zone_frame.pack(pady=(8, 4), padx=15)
drop_zone_label = ctk.CTkLabel(drop_zone_frame, text="아래 버튼을 눌러 공장 시스템에 자산들을 연동해 주세요 (전체 이미지 묶음 및 guideline.txt)", font=("Helvetica", 10), text_color="#888888")
drop_zone_label.pack(expand=True)

btn_action_container = ctk.CTkFrame(bottom_master_frame, fg_color="transparent")
btn_action_container.pack(fill="x", padx=15, pady=2)

select_btn = ctk.CTkButton(btn_action_container, text="📁 자산 원격 스토리지 통합 적재하기", command=browse_files_manual, width=400, height=32)
select_btn.pack(side="left")

reset_btn = ctk.CTkButton(btn_action_container, text="🧹 자산 비우기", command=reset_file_list, width=110, height=32, fg_color="#3A3A3A", hover_color="#4A4A4A")
reset_btn.pack(side="left", padx=10)

status_label = ctk.CTkLabel(btn_action_container, text="공장 가동 준비 완료.", text_color="#888888", font=("Helvetica", 10))
status_label.pack(side="left", padx=5)

submit_button = ctk.CTkButton(bottom_master_frame, text="🚀 모바일 반응형 웹명함 하이브리드 빌드 및 배포", command=on_submit_click, width=900, height=36, font=("Arial", 12, "bold"), fg_color="#C5A059", text_color="#000000", hover_color="#b38f4b")
submit_button.pack(side="bottom", pady=(0, 8), padx=15)