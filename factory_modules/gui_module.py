import customtkinter as ctk
from tkinter import filedialog
import os
import requests

# 환경 변수에서 설정값 호출 (API 키를 코드 내에 직접 적지 않음)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

dropped_files = []
final_payload = None

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
        drop_zone_label.configure(text=f"📊 총 {len(dropped_files)}개의 파일이 안전하게 로드되었습니다.", text_color="#64B5F6")
        file_names = [os.path.basename(f) for f in dropped_files]
        main_image_combobox.configure(values=file_names)
        
        img_nodes = [f for f in file_names if not f.endswith('.txt')]
        if img_nodes:
            main_image_combobox.set(img_nodes[-1])
        elif file_names:
            main_image_combobox.set(file_names[-1])
            
        status_label.configure(text=f"➕ {len(file_paths)}개의 파일이 정상적으로 추가되었습니다.", text_color="#A5D6A7")

def reset_file_list():
    global dropped_files
    dropped_files.clear()
    drop_zone_label.configure(text="아래 버튼을 눌러 파일들을 추가하세요\n(png, jpg, txt 다중 선택 지원)", text_color="#888888")
    main_image_combobox.configure(values=["먼저 파일을 추가해 주세요"])
    main_image_combobox.set("먼저 파일을 추가해 주세요")
    status_label.configure(text="🧹 로드된 파일 목록이 초기화되었습니다.", text_color="#FFB74D")

def on_submit_click():
    global final_payload
    if not name_entry.get().strip() or not brand_name_entry.get().strip():
        status_label.configure(text="❌ 필수 정보(디렉터 이름, 브랜드명)를 입력해야 빌드가 시작됩니다.", text_color="#FF5252")
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
            "sns1_type": sns1_combobox.get(),
            "sns1_url": sns1_entry.get().strip(),
            "sns2_type": sns2_combobox.get(),
            "sns2_url": sns2_entry.get().strip()
        },
        "faq_info": {
            "faq1_q": faq_q1_entry.get().strip(),
            "faq1_a": faq_a1_entry.get().strip(),
            "faq2_q": faq_q2_entry.get().strip(),
            "faq2_a": faq_a2_entry.get().strip(),
            "faq3_q": faq_q3_entry.get().strip(),
            "faq3_a": faq_a3_entry.get().strip()
        },
        "design_preference": {
            "style": design_style_combobox.get()
        },
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

app = ctk.CTk()
app.title("GeMi WebCard Director v1.0")
app.geometry("620x800")
ctk.set_appearance_mode("dark")
scroll_frame = ctk.CTkScrollableFrame(app, width=590, height=760, fg_color="transparent")
scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)
ctk.CTkLabel(scroll_frame, text="GeMi WebCard Director v1.0", font=("Helvetica", 22)).pack(pady=10)

ctk.CTkLabel(scroll_frame, text="디렉터 이름 (필수):").pack(anchor="w", padx=25)
name_entry = ctk.CTkEntry(scroll_frame, width=500, fg_color="#2A2A2A"); name_entry.pack(pady=5)
ctk.CTkLabel(scroll_frame, text="브랜드명 (필수):").pack(anchor="w", padx=25)
brand_name_entry = ctk.CTkEntry(scroll_frame, width=500, fg_color="#2A2A2A"); brand_name_entry.pack(pady=5)
ctk.CTkLabel(scroll_frame, text="브랜드 한줄 소개:").pack(anchor="w", padx=25)
introduction_entry = ctk.CTkEntry(scroll_frame, width=500, fg_color="#2A2A2A"); introduction_entry.pack(pady=5)
ctk.CTkLabel(scroll_frame, text="🌐 원하는 웹사이트 주소 이름 (선택):", text_color="#64B5F6").pack(anchor="w", padx=25)
url_name_entry = ctk.CTkEntry(scroll_frame, width=500, fg_color="#1E293B", border_color="#3B82F6"); url_name_entry.pack(pady=5)

contact_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent"); contact_frame.pack(fill="x", padx=25, pady=5)
ctk.CTkLabel(contact_frame, text="📞 휴대폰 번호:").grid(row=0, column=0, sticky="w")
ctk.CTkLabel(contact_frame, text="✉️ 이메일 주소:").grid(row=0, column=1, sticky="w", padx=20)
phone_entry = ctk.CTkEntry(contact_frame, width=240, fg_color="#2A2A2A"); phone_entry.grid(row=1, column=0)
email_entry = ctk.CTkEntry(contact_frame, width=240, fg_color="#2A2A2A"); email_entry.grid(row=1, column=1, padx=20)

sns_options = ["Instagram", "Naver Blog", "KakaoTalk", "Telegram", "YouTube"]
ctk.CTkLabel(scroll_frame, text="📱 SNS 채널 1 선택 및 주소(아이디):").pack(anchor="w", padx=25, pady=(5,0))
sns1_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent"); sns1_frame.pack(fill="x", padx=25, pady=2)
sns1_combobox = ctk.CTkComboBox(sns1_frame, values=sns_options, width=120, fg_color="#2A2A2A"); sns1_combobox.pack(side="left"); sns1_combobox.set("Instagram")
sns1_entry = ctk.CTkEntry(sns1_frame, width=370, fg_color="#2A2A2A", placeholder_text="링크 또는 ID 입력"); sns1_entry.pack(side="right")

ctk.CTkLabel(scroll_frame, text="🌐 SNS 채널 2 선택 및 주소(아이디):").pack(anchor="w", padx=25, pady=(5,0))
sns2_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent"); sns2_frame.pack(fill="x", padx=25, pady=2)
sns2_combobox = ctk.CTkComboBox(sns2_frame, values=sns_options, width=120, fg_color="#2A2A2A"); sns2_combobox.pack(side="left"); sns2_combobox.set("Naver Blog")
sns2_entry = ctk.CTkEntry(sns2_frame, width=370, fg_color="#2A2A2A", placeholder_text="링크 또는 ID 입력"); sns2_entry.pack(side="right")

design_style_combobox = ctk.CTkComboBox(scroll_frame, values=["[차분한 미니멀]", "[고급스러운 호텔 타월 감성]", "[모던 스튜디오]", "[네추럴 그린]"], width=500, fg_color="#2A2A2A")
design_style_combobox.pack(pady=15); design_style_combobox.set("[차분한 미니멀]")

faq_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent"); faq_frame.pack(fill="x", padx=25, pady=5)
faq_q1_entry = ctk.CTkEntry(faq_frame, width=240, placeholder_text="질문 1", fg_color="#2A2A2A"); faq_q1_entry.grid(row=0, column=0, pady=2)
faq_a1_entry = ctk.CTkEntry(faq_frame, width=240, placeholder_text="답변 1", fg_color="#2A2A2A"); faq_a1_entry.grid(row=0, column=1, padx=20, pady=2)
faq_q2_entry = ctk.CTkEntry(faq_frame, width=240, placeholder_text="질문 2", fg_color="#2A2A2A"); faq_q2_entry.grid(row=1, column=0, pady=2)
faq_a2_entry = ctk.CTkEntry(faq_frame, width=240, placeholder_text="답변 2", fg_color="#2A2A2A"); faq_a2_entry.grid(row=1, column=1, padx=20, pady=2)
faq_q3_entry = ctk.CTkEntry(faq_frame, width=240, placeholder_text="질문 3", fg_color="#2A2A2A"); faq_q3_entry.grid(row=2, column=0, pady=2)
faq_a3_entry = ctk.CTkEntry(faq_frame, width=240, placeholder_text="답변 3", fg_color="#2A2A2A"); faq_a3_entry.grid(row=2, column=1, padx=20, pady=2)

drop_zone_frame = ctk.CTkFrame(scroll_frame, width=500, height=65, fg_color="#1E1E1E", border_width=2); drop_zone_frame.pack_propagate(False); drop_zone_frame.pack(pady=10)
drop_zone_label = ctk.CTkLabel(drop_zone_frame, text="아래 버튼을 눌러 파일들을 추가하세요\n(이미지들과 guideline.txt 가이드라인 동시 선택 지원)", text_color="#A5D6A7")
drop_zone_label.pack(expand=True)

btn_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent"); btn_frame.pack(fill="x", padx=25)
select_btn = ctk.CTkButton(btn_frame, text="📁 자료 및 가이드라인(.txt) 통합 추가하기", command=browse_files_manual, width=360); select_btn.pack(side="left")
reset_btn = ctk.CTkButton(btn_frame, text="🧹 비우기", command=reset_file_list, width=130); reset_btn.pack(side="left", padx=10)

main_image_combobox = ctk.CTkComboBox(scroll_frame, values=["먼저 파일을 추가해 주세요"], width=500, fg_color="#2A2A2A"); main_image_combobox.pack(pady=10)

status_label = ctk.CTkLabel(scroll_frame, text="공장 가동 준비 완료.", text_color="#888888"); status_label.pack()
submit_button = ctk.CTkButton(scroll_frame, text="🚀 모바일 반응형 웹명함 빌드 및 자동 배포 시작", command=on_submit_click, width=500, height=45, font=("Arial", 14, "bold")); submit_button.pack(pady=10)