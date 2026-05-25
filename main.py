import os
from dotenv import load_dotenv # 이 줄 추가!
import requests
import subprocess
import webbrowser
from tkinter import messagebox
from supabase import create_client, Client

from factory_modules.gui_module import export_gui_data
from factory_modules.db_module import save_client_data_v2, initialize_db_factory
from factory_modules.ai_module import generate_webcard_code

# 👑 [정밀 보정 구역] 누락되었던 환경 변수 활성화 함수를 가동합니다.
load_dotenv()

# 서버 설정 (환경 변수에서 호출하도록 수정)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_supabase_tables_automatically():
    print("📡 [Supabase] 테이블 상태 검사 및 자동 인프라 구축 중...")
    try:
        initialize_db_factory()
        print("✅ [Supabase] 마스터 테이블 진단 완료.")
    except Exception as e:
        print(f"ℹ️ [Supabase] 진단 중 참조 오류 발생: {e}")

# 👑 [서버 우체통 실시간 완전 자동 조립 가동 엔진]
# - 리모컨에 입력된 영문 브랜드명을 추적하여 chat.py에 독립 우체통 코드가 없을 경우 맨 아래에 자동으로 코드를 작성합니다.
def auto_append_chat_server_code(brand_url_name):
    clean_name = brand_url_name.strip().lower()
    if not clean_name or clean_name in ["gemi", "stellar", "jeonga"]:
        return

    chat_file_path = "chat.py"
    if not os.path.exists(chat_file_path):
        return

    # 이미 우체통이 생성되어 있는지 중복 검사
    with open(chat_file_path, "r", encoding="utf-8") as f:
        chat_content = f.read()

    target_route = f"'/api/submit-{clean_name}-inquiry'"
    if target_route in chat_content or f'"/api/submit-{clean_name}-inquiry"' in chat_content:
        print(f"ℹ️ [Server Factory] chat.py 내부에 {clean_name} 우체통이 이미 존재하여 조립을 패스합니다.")
        return

    print(f"⚡ [Server Factory] {clean_name} 전용 백엔드 우체통 독립 개통 공정 시작...")
    
    server_code_block = f"""

# 🛡️ [리모컨 자동 생성] {clean_name} 전용 독립 우체통 신설
@app.route('/api/submit-{clean_name}-inquiry', methods=['POST', 'OPTIONS'])
def submit_{clean_name}_inquiry():
    if request.method == 'OPTIONS':
        return jsonify({{"success": True}}), 200
        
    try:
        body = request.get_json(silent=True) or {{}}
        if not body:
            body = request.form.to_dict()

        c_name = body.get("customer_name", "").strip()
        c_contact = body.get("customer_contact", "").strip()
        i_type = body.get("inquiry_type", "").strip()
        msg = body.get("message", "").strip()
        
        brand_name = "{clean_name}"
        
        budget_val = "미기재 또는 상세 내용 참고"
        if "[예산:" in msg:
            try:
                parts = msg.split("]", 1)
                budget_val = parts[0].replace("[예산:", "").strip()
                msg = parts[1].strip()
            except Exception:
                pass

        if not c_name or not c_contact:
            return jsonify({{"success": False, "error": "필수 입력 데이터가 누락되었습니다."}}), 400

        print(f"🚀 [{clean_name} 전용 알림 엔진 작동] 브랜드 고정: {{brand_name}}")

        alert_text = (
            f"🔔 *[{{brand_name}} 명함 신규 견적 문의]*\\n\\n"
            f"👤 *고객/기업명:* {{c_name}}\\n"
            f"📞 *연락처:* {{c_contact}}\\n"
            f"📂 *프로젝트 유형:* {{i_type}}\\n"
            f"💰 *희망 예산 범위:* {{budget_val}}\\n"
            f"📝 *상세 요청사항:* {{msg}}"
        )
        
        send_telegram_alert(alert_text, brand_name=brand_name)
        
        supabase.table("gemi_customer_inquiry").insert({{
            "brand_name": brand_name, 
            "customer_name": c_name,
            "customer_contact": c_contact,
            "inquiry_type": i_type,
            "message": f"[예산: {{budget_val}}] {{msg}}"
        }}).execute()
        
        return jsonify({{"success": True, "message": "{clean_name} Inquiry submitted and saved successfully"}}), 200
        
    except Exception as e:
        print(f"❌ [{clean_name} Inquiry Error]: {{str(e)}}")
        return jsonify({{"success": False, "error": str(e)}}), 500
"""
    with open(chat_file_path, "a", encoding="utf-8") as f:
        f.write(server_code_block)
    print(f"✅ [Server Factory] chat.py 백엔드 인프라 확장 조립 완공 완료.")

# 👑 [배송 엔진 고도화 패치 - JSON 프리 서브경로 안전 배포 버전 완공]
# - 버셀의 dist 고정 설정을 100% 사수하면서, 브랜치를 가르지 않고 main 브랜치 하위 폴더 구조로 깃허브에 안전 배송합니다.
def auto_git_push_hybrid(url_name, html_payload):
    clean_url = "".join(c.lower() for c in url_name if c.isalnum() or c in ["-", "_"]).strip()
    
    # 👑 버셀 고정 주소 규칙 반영 및 서브 경로 도메인 주소 판정
    if not clean_url:
        final_deployed_url = "https://gemistudio.vercel.app"
        output_dir = "dist"
    else:
        # 주소가 있으면 도메인 뒤에 /주소이름이 붙는 형태로 테스터 최종 주소를 확정합니다.
        final_deployed_url = f"https://gemistudio.vercel.app/{clean_url}"
        output_dir = os.path.join("dist", clean_url)

    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # 1호 산출물: 지정된 격리 폴더 내부에 메인 웹명함 배송
        main_path = os.path.join(output_dir, "index.html")
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(html_payload.get("main_html", ""))

        # 2호 산출물: 지정된 격리 폴더 내부의 pages 폴더 경로에 서브 포트폴리오 배송
        pages_dir = os.path.join(output_dir, "pages")
        os.makedirs(pages_dir, exist_ok=True)
        portfolio_path = os.path.join(pages_dir, "portfolio.html")
        with open(portfolio_path, "w", encoding="utf-8") as f:
            f.write(html_payload.get("portfolio_html", ""))

        print(f"📦 [팩토리 서브폴더 완공] 물리 파일 분리 저장 완료:\n  -> {main_path}\n  -> {portfolio_path}")

        # 👑 [서버 소스 자동 추적 연동 장치 가동] 배송 출발 직전 chat.py 우체통 동적 업데이트 자동 집도
        auto_append_chat_server_code(clean_url)

        # 👑 [깃 안전 공정]: 유령 브랜치 조작을 전부 청소하고, 무조건 main 브랜치 단일 통로로 안전하게 푸시합니다.
        subprocess.run(["git", "add", "."], check=True)
        
        if not clean_url:
            print("\n🚚 5단계: [기존 주소 덮어쓰기] 메인 웹명함 업데이트 전송 시작...")
            subprocess.run(["git", "commit", "-m", "feat: 메인 주소 덮어쓰기 빌드"], check=False)
        else:
            print(f"\n🚚 5단계: [서브 폴더 확장 빌드] 주소명: {final_deployed_url} 전송 시작...")
            subprocess.run(["git", "commit", "-m", f"feat: 새 독립 서브 사이트 추가 ({clean_url}) 및 백엔드 라우터 자동 완공"], check=False)
        
        # 👑 브랜치 변경이나 도망 없이 무조건 메인 본선선박(main)에 실어서 원격 깃허브로 밀어 넣습니다.
        subprocess.run(["git", "branch", "-M", "main"], check=False)
        subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
            
        show_completion_dialog(final_deployed_url)
        return True
        
    except Exception as e:
        print(f"❌ [Auto Git] 서브 폴더 배포 중 에러 발생: {e}")
        return False

# 👑 [UX 정밀 교정 구역] 
# 기존의 일방통행형 showinfo 대신 askokcancel을 사용하여 [확인]을 누를 때만 브라우저가 열리게 고쳤습니다.
def show_completion_dialog(url):
    msg = f"축하합니다! GeMi 모바일 웹명함 공정이 완벽하게 끝났습니다.\n\n🌐 완성된 주소:\n{url}\n\n[확인]을 누르시면 internet 창이 자동으로 열리며,\n[취소] 또는 우측 상단 [X] 단추를 누르면 이동하지 않고 창만 닫힙니다."
    
    # 사용자가 [확인]을 누르면 True, [취소]나 [X]를 누르면 False가 반환됩니다.
    confirm_move = messagebox.askokcancel("🎉 GeMi Factory 공정 완공 완료!", msg)
    
    if confirm_move:
        webbrowser.open(url)
    else:
        print("ℹ️ 디렉터 요청에 의해 배포 주소 브라우저 자동 연결을 패스합니다.")

def main_pipeline():
    print("🏭 [GeMi 마스터 스위치] 모바일 반응형 웹명함 공장 가동 시작...")
    init_supabase_tables_automatically()
    
    print("🖥️ [GUI] 리모컨 입력 창을 화면에 표시합니다...")
    gui_payload = export_gui_data()
    
    if not gui_payload:
        print("❌ [Main] 리모컨이 입력 없이 닫혀 빌드를 중단합니다.")
        return

    user_info = gui_payload.get("user_info", {})
    custom_url_name = user_info.get("custom_url_name", "").strip()

    local_images = gui_payload["assets"]["all_dropped_files"]
    print("\n📦 2단계: Supabase 스토리지 업로드 파이프라인 가동...")
    upload_result = save_client_data_v2(gui_payload, local_images)
    
    # 이미지 주소와 메모장 가이드라인 주소를 무전 자산 패키지에 동시 정착
    gui_payload["main_image_url"] = upload_result.get("main_image_url", "")
    gui_payload["other_image_urls"] = upload_result.get("other_image_urls", [])
    gui_payload["guideline_txt_url"] = upload_result.get("guideline_txt_url", "")
    
    # 👑 [유실 차단 연결 브릿지 안착]
    # db_module에서 가공되어 나온 '이미지 스토리지 주소 + 기획 서사' 매칭 세트 목록을 
    # AI 엔진이 정상적으로 읽어 갈 수 있도록 동적 데이터 주머니(payload)에 유실 없이 합쳐줍니다.
    gui_payload["portfolio_items"] = upload_result.get("portfolio_items", [])

    print("\n🤖 3단계: Gemini AI 완전 동적 코딩 가동...")
    # 👑 [엔진 수령 라인 교정] 이제 단일 문자열이 아니라 마스터 딕셔너리 데이터 세트를 리턴받습니다.
    html_payload = generate_webcard_code(gui_payload)
    
    if not html_payload or not html_payload.get("main_html"):
        print("❌ [Main] AI 소스코드 생성에 실패했습니다.")
        return

    # 👑 보정된 딕셔너리 데이터 세트를 그대로 배송 담당 함수로 인계합니다.
    auto_git_push_hybrid(custom_url_name, html_payload)
    print("\n🏁 [GeMi Factory] 모든 하이브리드 공정이 종료되었습니다!")

if __name__ == "__main__":
    main_pipeline()