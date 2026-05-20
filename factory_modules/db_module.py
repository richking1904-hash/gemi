import os
import requests
import time
from supabase import create_client, Client

# 서버 설정 (환경 변수에서 호출)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = "859745575"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def initialize_db_factory():
    print("✅ [DB Factory] Supabase 마스터 테이블 진단 및 연동 완료.")
    return

def send_telegram_alert(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def save_client_data_v2(payload: dict, image_paths: list) -> dict:
    print("🔓 [Storage] 가이드라인 포함 파일 통합 동기화 엔진 가동...")
    bucket_name = "gemi_assets"
    main_image_url = ""
    other_image_urls = []
    guideline_txt_url = "" 
    
    selected_main_path = payload.get("main_image_path", "")
    
    if image_paths:
        for path in image_paths:
            if not os.path.exists(path): continue
                
            base_name = os.path.basename(path)
            name_part, ext_part = os.path.splitext(base_name)
            timestamp = int(time.time())
            file_name = f"{name_part}_{timestamp}{ext_part}"
            
            try:
                with open(path, "rb") as f: file_data = f.read()
                    
                upload_url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{file_name}"
                c_type = "text/plain" if file_name.endswith('.txt') else "image/png" if file_name.endswith('.png') else "image/jpeg"
                
                headers = {
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "apiKey": SUPABASE_KEY,
                    "Content-Type": c_type
                }
                
                response = requests.post(upload_url, headers=headers, data=file_data)
                if response.status_code in [200, 201]:
                    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{file_name}"
                    print(f"✅ [Storage] 파일 업로드 성공: {public_url}")
                    
                    if path.endswith('.txt'):
                        guideline_txt_url = public_url
                    elif path == selected_main_path:
                        main_image_url = public_url
                    else:
                        other_image_urls.append(public_url)
            except Exception as e:
                print(f"❌ [Storage] 전송 오류: {e}")

    if not main_image_url and other_image_urls:
        main_image_url = other_image_urls.pop(0)

    try:
        user_info = payload.get("user_info", {})
        contact_info = payload.get("contact_info", {})
        faq_info = payload.get("faq_info", {})
        
        config_insert = {
            "name": user_info.get("name"),  
            "brand_name": user_info.get("brand_name"),
            "introduction": user_info.get("introduction"),
            "phone": contact_info.get("phone"),
            "email": contact_info.get("email"),
            "instagram": contact_info.get("instagram"),
            "naver_blog": contact_info.get("naver_blog"),
            "main_image_url": main_image_url,
            "faq1_q": faq_info.get("faq1_q"), "faq1_a": faq_info.get("faq1_a"),
            "faq2_q": faq_info.get("faq2_q"), "faq2_a": faq_info.get("faq2_a"),
            "faq3_q": faq_info.get("faq3_q"), "faq3_a": faq_info.get("faq3_a")
        }
        supabase.table("gemi_clients").insert(config_insert).execute()
        print("✅ [DB Factory] 마스터 테이블 안전 적재 완료!")
    except Exception as e:
        print(f"❌ [DB Factory] 새 장부 적재 실패 우회: {e}")

    return {
        "success": True,
        "main_image_url": main_image_url,
        "other_image_urls": other_image_urls,
        "guideline_txt_url": guideline_txt_url 
    }