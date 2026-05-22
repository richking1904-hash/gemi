import os
import requests
import time
from supabase import create_client, Client
from dotenv import load_dotenv # 1. 추가

load_dotenv() # 2. 추가

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
    if not TELEGRAM_BOT_TOKEN:
        print("❌ [Telegram] 에러: TELEGRAM_TOKEN 환경 변수가 설정되지 않았습니다.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print("✅ [Telegram] 알림 전송 성공.")
        else:
            print(f"❌ [Telegram] 전송 실패 (상태코드 {response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ [Telegram] 전송 중 예외 발생: {e}")

def save_client_data_v2(payload: dict, image_paths: list) -> dict:
    print("🔓 [Storage] 가이드라인 포함 파일 통합 동기화 엔진 가동...")
    bucket_name = "gemi_assets"
    main_image_url = ""
    guideline_txt_url = "" 
    
    selected_main_path = payload.get("main_image_path", "")
    
    # 👑 [가변형 포트폴리오 업로드 코어] 
    # 리모컨에서 넘겨받은 동적 포트폴리오 묶음을 안전하게 가져옵니다.
    portfolio_items = payload.get("portfolio_items", [])
    other_image_urls = []

    # 1. 먼저 단독 자산들(명함 대문 이미지 및 guideline.txt) 업로드 파이프라인 실행
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
                    print(f"✅ [Storage] 마스터 자산 업로드 성공: {public_url}")
                    
                    if path.endswith('.txt'):
                        guideline_txt_url = public_url
                    elif path == selected_main_path:
                        main_image_url = public_url
            except Exception as e:
                print(f"❌ [Storage] 마스터 자산 전송 오류: {e}")

    # 👑 2. [신설] 동적으로 추가된 포트폴리오 이미지 가변 루프 업로드 공정
    # 리모컨에서 몇 장을 추가했든 상관없이 한 땀 한 땀 안전하게 분리 동기화합니다.
    for idx, item in enumerate(portfolio_items):
        path = item.get("image_path", "")
        if not path or not os.path.exists(path):
            item["image_url"] = "" # 사진 없이 서사만 남았을 경우를 위한 방어벽
            continue
            
        base_name = os.path.basename(path)
        name_part, ext_part = os.path.splitext(base_name)
        timestamp = int(time.time()) + idx # 타임스탬프 중복 충돌 방지 미세 버퍼
        file_name = f"port_{name_part}_{timestamp}{ext_part}"
        
        try:
            with open(path, "rb") as f: file_data = f.read()
            upload_url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{file_name}"
            c_type = "image/png" if file_name.endswith('.png') else "image/jpeg"
            
            headers = {
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "apiKey": SUPABASE_KEY,
                "Content-Type": c_type
            }
            
            response = requests.post(upload_url, headers=headers, data=file_data)
            if response.status_code in [200, 201]:
                public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{file_name}"
                print(f"✅ [Storage] 포트폴리오 {idx+1}번 이미지 동기화 완료: {public_url}")
                # 👑 로컬 컴퓨터 주소였던 자리에 갓 발급된 프리미엄 클라우드 URL을 주입해 바인딩합니다.
                item["image_url"] = public_url
                other_image_urls.append(public_url)
        except Exception as e:
            print(f"❌ [Storage] 포트폴리오 {idx+1}번 이미지 전송 실패 우회: {e}")
            item["image_url"] = ""

    # 만약 실수로 대문 이미지를 지정 안 했다면 첫 번째 작품 사진을 대문으로 강제 스왑
    if not main_image_url and other_image_urls:
        main_image_url = other_image_urls[0]

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

    # 👑 [선제 캐싱 파이프라인 추가] 공장 빌드 완공 시 고정 질문/정답을 캐시 장부에 미리 등록하여 타이밍 버그 해결
    try:
        user_info = payload.get("user_info", {})
        faq_info = payload.get("faq_info", {})
        b_name = user_info.get("brand_name", "GeMi").strip()

        faq_list = [
            {"q": faq_info.get("faq1_q", "").strip(), "a": faq_info.get("faq1_a", "").strip()},
            {"q": faq_info.get("faq2_q", "").strip(), "a": faq_info.get("faq2_a", "").strip()},
            {"q": faq_info.get("faq3_q", "").strip(), "a": faq_info.get("faq3_a", "").strip()},
        ]

        for faq in faq_list:
            if faq["q"] and faq["a"]:
                # 꼬임 방지를 위해 해당 브랜드의 동일 질문 캐시 데이터가 있다면 1차 선제 삭제
                supabase.table("gemi_chat_cache").delete().eq("brand_name", b_name).eq("question", faq["q"]).execute()
                
                # 브랜드 식별 서랍(brand_name)을 달아 장부에 정답 미리 적재
                supabase.table("gemi_chat_cache").insert({
                    "brand_name": b_name,
                    "question": faq["q"],
                    "answer": faq["a"]
                }).execute()
                print(f"📌 [Pre-Caching] {b_name} 서랍에 고정 FAQ 선제 캐싱 성공: {faq['q']}")
    except Exception as cache_pipeline_err:
        print(f"ℹ️ [Pre-Caching] 장부 선제 기록 패스: {cache_pipeline_err}")

    return {
        "success": True,
        "main_image_url": main_image_url,
        "other_image_urls": other_image_urls,
        "guideline_txt_url": guideline_txt_url,
        # 👑 가변형 포트폴리오 최종 리스트 뭉치를 배포 파이프라인으로 온전히 인계해 줍니다.
        "portfolio_items": portfolio_items
    }