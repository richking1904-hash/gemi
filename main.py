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

def auto_git_push_hybrid(url_name, final_html_code):
    clean_url = "".join(c.lower() for c in url_name if c.isalnum() or c in ["-", "_"]).strip()
    
    if not clean_url:
        final_deployed_url = "https://gemi-webcard.vercel.app"
    else:
        final_deployed_url = f"https://{clean_url}.vercel.app"

    try:
        output_dir = "dist"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_html_code)

        subprocess.run(["git", "add", "."], check=True)
        
        if not clean_url:
            print("\n🚚 5단계: [기존 주소 덮어쓰기] 메인 웹명함 업데이트 전송 시작...")
            subprocess.run(["git", "commit", "-m", "feat: 메인 주소 덮어쓰기 빌드"], check=False)
            subprocess.run(["git", "branch", "-M", "main"], check=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
        else:
            print(f"\n🚚 5단계: [새로운 독립 웹사이트 생성] 주소명: {final_deployed_url} 배포 준비...")
            subprocess.run(["git", "commit", "-m", f"feat: 새 독립 사이트 배포 ({clean_url})"], check=False)
            subprocess.run(["git", "branch", "-M", "main"], check=False)
            subprocess.run(["git", "checkout", "-b", clean_url], check=False)
            subprocess.run(["git", "push", "origin", clean_url], check=True)
            subprocess.run(["git", "checkout", "main"], check=False)
            
        show_completion_dialog(final_deployed_url)
        return True
        
    except Exception as e:
        print(f"❌ [Auto Git] 배포 중 에러 발생: {e}")
        return False

def show_completion_dialog(url):
    msg = f"축하합니다! GeMi 모바일 웹명함 공정이 완벽하게 끝났습니다.\n\n🌐 완성된 주소:\n{url}\n\n[확인]을 누르시면 인터넷 창이 자동으로 열립니다."
    messagebox.showinfo("🎉 GeMi Factory 공정 완공 완료!", msg)
    webbrowser.open(url)

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

    print("\n🤖 3단계: Gemini AI 완전 동적 코딩 가동...")
    final_html_code = generate_webcard_code(gui_payload)
    
    if not final_html_code:
        print("❌ [Main] AI 소스코드 생성에 실패했습니다.")
        return

    auto_git_push_hybrid(custom_url_name, final_html_code)
    print("\n🏁 [GeMi Factory] 모든 하이브리드 공정이 종료되었습니다!")

if __name__ == "__main__":
    main_pipeline()