import os
import requests
import time
from supabase import create_client, Client
from dotenv import load_dotenv
from cryptography.fernet import Fernet  # 🔐 암호화 라이브러리 추가

load_dotenv()

# 서버 설정 (환경 변수에서 호출)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = "859745575"

# 🔐 [보안 엔지니어링] 렌더 및 .env에 등록한 마스터 해독 열쇠 호출
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")

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
        
        # 👑 [4대 핵심 채널 슈파베이스 직결 바인딩 공정 완결]
        # - 기존 유실 버그를 잡기 위해 instagram, naver_blog 키값을 정확히 매칭했습니다.
        # - 새 채널인 카카오 주소를 kakao_url에, 유튜브 주소를 telegram_url 컬럼 서랍에 정밀 적재합니다.
        config_insert = {
            "name": user_info.get("name"),  
            "brand_name": user_info.get("brand_name"),
            "introduction": user_info.get("introduction"),
            "phone": contact_info.get("phone"),
            "email": contact_info.get("email"),
            "instagram": contact_info.get("instagram"),
            "naver_blog": contact_info.get("naver_blog"),
            "kakao_url": contact_info.get("kakao_url"),
            "telegram_url": contact_info.get("telegram_url"),  # 형규님 규칙: 유튜브 주소 적재
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


# 👑 [시큐리티 필터 개조 완료 구역] 
def check_existing_brand_config(brand_name: str) -> bool:
    """
    [신설 제약 엔진]: Supabase 창고에 이미 동일한 브랜드명이 소문자로 등록되어 있는지 사전 조회합니다.
    """
    if not brand_name:
        return False
    try:
        clean_name = brand_name.strip().lower()
        res = supabase.table("gemi_telegram_config").select("brand_name").eq("brand_name", clean_name).execute()
        if res.data and len(res.data) > 0:
            return True
        return False
    except Exception as e:
        print(f"ℹ️ [DB Check] 사전 조회 중 패스: {e}")
        return False


def update_telegram_settings(brand_name: str, token: str, chat_id: str, force_upsert: bool = False) -> bool:
    """
    사용자가 리모컨에 입력한 토큰과 ID를 발급받은 ENCRYPTION_KEY로 암호화하여 
    Supabase에 안전한 암호문 문자열 형태로 적재합니다. 
    (대소문자 강제 정제 조치 및 중복 방어 엔진 탑재 버전)
    """
    if not brand_name:
        print("❌ [DB Telegram] 에러: brand_name이 누락되었습니다.")
        return False

    if not ENCRYPTION_KEY:
        print("❌ [DB Telegram] 에러: 시스템에 ENCRYPTION_KEY 열쇠가 등록되지 않았습니다.")
        return False

    # 👑 [대소문자 철벽 방어 수술]: 들어온 문자열을 무조건 소문자로 일괄 클렌징
    clean_brand_name = brand_name.strip().lower()

    # GUI 연동용 안전장치: 강제 덮어쓰기가 아니고 장부에 이미 이름이 존재한다면 
    # 무작정 에러를 내지 않고 False를 반환하여 GUI가 팝업(Yes/No)을 띄우게 제어권을 넘김
    if not force_upsert and check_existing_brand_config(clean_brand_name):
        print(f"⚠️ [DB Block] [{clean_brand_name}] 장부가 이미 존재하여 동기화를 임시 제한합니다.")
        return False

    try:
        # 1. 암호화 연동 엔진 준비
        f = Fernet(ENCRYPTION_KEY.encode())
        
        # 2. 사용자가 입력한 날것의 텍스트를 암호문(gAAAAA...)으로 초정밀 세탁
        encrypted_token = f.encrypt(token.strip().encode('utf-8')).decode('utf-8')
        encrypted_chat_id = f.encrypt(chat_id.strip().encode('utf-8')).decode('utf-8')
        
        # 3. 암호화된 보정본 데이터 패키지 생성 (소문자로 통일된 brand_name 바인딩)
        config_data = {
            "brand_name": clean_brand_name,
            "telegram_token": encrypted_token,      # 🔐 암호문 투하
            "telegram_chat_id": encrypted_chat_id    # 🔐 암호문 투하
        }
        
        # Supabase Upsert 문법 적용 (소문자 brand_name 기준으로 중복 없이 깔끔하게 덮어쓰기)
        supabase.table("gemi_telegram_config").upsert(config_data, on_conflict="brand_name").execute()
        print(f"✈️ [DB Security Telegram] [{clean_brand_name}] 서랍에 '소문자 변환된 보안 장부' 최종 동기화 완료!")
        return True
    except Exception as e:
        print(f"❌ [DB Telegram] 보안 암호화 장부 동기화 실패 우회: {e}")
        return False