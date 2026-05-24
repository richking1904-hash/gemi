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

# 👑 [배송 엔진 고도화 패치 - 독립 폴더 격리 배포 버전 완공]
# - 새 주소명(url_name)이 입력되면 dist 폴더 하위에 해당 명칭의 폴더를 새로 파서 기존 본진 파일 유실을 원천 차단합니다.
def auto_git_push_hybrid(url_name, html_payload):
    clean_url = "".join(c.lower() for c in url_name if c.isalnum() or c in ["-", "_"]).strip()
    
    # 👑 [주소 교정 완료] 형규님의 진짜 버셀 도메인 주소인 gemistudio.vercel.app 규칙 반영
    if not clean_url:
        final_deployed_url = "https://gemistudio.vercel.app"
        # 👑 주소 입력창이 비어있으면 기존 본진 경로인 dist 루트를 사수합니다.
        output_dir = "dist"
    else:
        final_deployed_url = f"https://{clean_url}.vercel.app"
        # 👑 [가장 중요한 공정 핵심 개조]: 주소가 들어오면 dist/주소이름 구조로 독립된 새로운 물리 폴더를 강제 생성합니다!
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

        print(f"📦 [팩토리 독립폴더 격리완공] 물리 파일 분리 저장 완료:\n  -> {main_path}\n  -> {portfolio_path}")

        subprocess.run(["git", "add", "."], check=True)
        
        if not clean_url:
            print("\n🚚 5단계: [기존 주소 덮어쓰기] 메인 웹명함 업데이트 전송 시작...")
            subprocess.run(["git", "commit", "-m", "feat: 메인 주소 덮어쓰기 빌드"], check=False)
            subprocess.run(["git", "branch", "-M", "main"], check=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
        else:
            print(f"\n🚚 5단계: [새로운 독립 폴더 기반 배포] 주소명: {final_deployed_url} 브랜치 전송 준비...")
            subprocess.run(["git", "commit", "-m", f"feat: 새 독립 사이트 폴더 격리 빌드 ({clean_url})"], check=False)
            subprocess.run(["git", "branch", "-M", "main"], check=False)
            subprocess.run(["git", "checkout", "-b", clean_url], check=False)
            subprocess.run(["git", "push", "origin", clean_url], check=True)
            subprocess.run(["git", "checkout", "main"], check=False)
            
        show_completion_dialog(final_deployed_url)
        return True
        
    except Exception as e:
        print(f"❌ [Auto Git] 폴더 분리 및 배포 중 에러 발생: {e}")
        return False

# 👑 [UX 정밀 교정 구역] 
# 기존의 일방통행형 showinfo 대신 askokcancel을 사용하여 [확인]을 누를 때만 브라우저가 열리게 고쳤습니다.
def show_completion_dialog(url):
    msg = f"축하합니다! GeMi 모바일 웹명함 공정이 완벽하게 끝났습니다.\n\n🌐 완성된 주소:\n{url}\n\n[확인]을 누르시면 인터넷 창이 자동으로 열리며,\n[취소] 또는 우측 상단 [X] 단추를 누르면 이동하지 않고 창만 닫힙니다."
    
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