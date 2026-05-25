import json
import os
import urllib.request
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
from dotenv import load_dotenv
from cryptography.fernet import Fernet  # 🔐 렌더 실시간 해독 엔진 라이브러리 추가

load_dotenv()

app = Flask(__name__)

# CORS 보안 설정 완벽 선언
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 환경 변수 호출
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# 🔐 [시큐리티 마스터 설정] 기본 마스터 설정값 및 해독용 마스터 키 로드
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = "859745575"
ENCRYPTION_KEY = "gzA_LSFto4ku9w8gBtMSxuDLHGpjNh7y4M1eBN5bw1Q="  # 🔥 마스터 비밀 열쇠 직결 패치 완료

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# [대화형 카운터 레이어] 사용자의 일상대화 횟수만 카운트하는 저장소
DAILY_TALK_COUNTER = {}

# 👑 [동적 실시간 복호화 알림 엔진으로 개조]
def send_telegram_alert(text: str, brand_name: str = "gemi"):
    """
    gemi_telegram_config 테이블에서 brand_name에 맞는 암호화된 토큰/채널 ID를 꺼내와
    ENCRYPTION_KEY로 실시간 복호화하여 해당 디렉터의 텔레그램으로 알림을 보냅니다.
    """
    target_token = TELEGRAM_BOT_TOKEN
    target_chat_id = TELEGRAM_CHAT_ID
    
    # 👑 [대소문자 철벽 정제]: 리모컨 및 주소창 규격에 맞게 무조건 소문자로 치환
    clean_brand_name = brand_name.strip().lower() if brand_name else "gemi"
    
    if ENCRYPTION_KEY and clean_brand_name:
        try:
            # 🔥 [배달사고 완벽 조치]: .ilike의 중복 검출 버그를 박멸하고, 100% 소문자 1:1 매칭(.eq)으로 정확히 고유 장부 1건만 조준 사격합니다.
            res = supabase.table("gemi_telegram_config").select("telegram_token", "telegram_chat_id").eq("brand_name", clean_brand_name).execute()
            if res.data and len(res.data) > 0:
                config = res.data[0]
                enc_token = config.get("telegram_token")
                enc_chat_id = config.get("telegram_chat_id")
                
                # 가저온 데이터가 암호화 토큰 포맷일 때만 실시간 해독 가동
                if enc_token and enc_chat_id and enc_token.startswith("gAAAAA"):
                    f = Fernet(ENCRYPTION_KEY.encode())
                    decrypted_token = f.decrypt(enc_token.encode('utf-8')).decode('utf-8')
                    decrypted_chat_id = f.decrypt(enc_chat_id.encode('utf-8')).decode('utf-8')
                    
                    target_token = decrypted_token
                    target_chat_id = decrypted_chat_id
                    print(f"🔓 [Security Alert] [{clean_brand_name}] 디렉터 전용 텔레그램 보안 열쇠 해독 성공!")
            else:
                print(f"⚠️ [Security Alert] [{clean_brand_name}] 소문자 설정 장부가 DB에 없어 마스터 계정으로 우회합니다.")
        except Exception as decrypt_err:
            print(f"ℹ️ [Security Alert] [{clean_brand_name}] 전용 키 해독 실패 (마스터 계정으로 대체 전송): {decrypt_err}")

    if not target_token:
        print("❌ [Telegram] 에러: 발송할 TELEGRAM_TOKEN이 존재하지 않습니다.")
        return
    
    url = f"https://api.telegram.org/bot{target_token}/sendMessage"
    payload = {"chat_id": target_chat_id, "text": text, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print(f"✅ [Telegram] [{clean_brand_name}] 알림 전송 성공.")
        else:
            print(f"❌ [Telegram] 전송 실패 (상태코드 {response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ [Telegram] 전송 중 예외 발생: {e}")

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return jsonify({"success": True}), 200

    api_key = OPENROUTER_API_KEY
    if not api_key:
        return jsonify({"reply": "API Key가 설정되지 않았습니다."}), 500

    try:
        body = request.get_json() or {}
        user_message = body.get("message", "").strip()
        guideline_data = body.get("guideline_txt", "")
        
        # 👑 [상담 엔진 대소문자 안전망]: 리모컨 빌드 시 넘어오는 브랜드명을 무조건 소문자로 클렌징하여 캐시 장부 꼬임 차단
        brand_name = body.get("brand_name", "gemi").strip().lower()

        if not user_message:
            return jsonify({"reply": "질문 내용이 비어있습니다."}), 200

        try:
            cache = supabase.table("gemi_chat_cache").select("answer").eq("brand_name", brand_name).eq("question", user_message).execute()
            if cache.data and len(cache.data) > 0:
                for item in cache.data:
                    if item.get("answer") and "[가이드라인 문서]" not in item["answer"]:
                        print(f"✅ [FAQ 매칭 성공] {brand_name} 고정 답변 리턴: {user_message}")
                        return jsonify({"reply": item["answer"]}), 200
        except Exception as cache_err:
            print(f"ℹ️ 캐시 장부 매칭 패스: {cache_err}")

        client_ip = request.remote_addr or "anonymous"
        session_key = f"{brand_name}_{client_ip}"
        
        is_business_query = False
        
        keywords_for_business = [
            "제작", "비용", "단가", "포트폴리오", "기간", "일정", "연락", "이메일", "전화", "문의", 
            "견적", "작업", "의뢰", "수정", "환불", "금액", "디자인", "명함", "단추", "스튜디오", "가격", "얼마",
            "인스타", "instagram", "블로그", "naver", "카카오", "kakao", "유튜브", "youtube", "채널", "링크", "주소"
        ]
        if any(k_word in user_message.lower() for k_word in keywords_for_business):
            is_business_query = True

        if not is_business_query:
            current_count = DAILY_TALK_COUNTER.get(session_key, 0)
            if current_count >= 10:
                print(f"🚫 [일상 제한 발동] {session_key}: 일상 한도 소진으로 고정 문구 출력")
                return jsonify({
                    "reply": "🔒 디렉터님의 프로젝트 소통을 보조하기 위한 오늘 자 일상 대화 한도(10회)가 소진되었습니다!\n\n하지만 견적 문의, 포트폴리오 확인, 디자인 단가 등의 업무 관련 질문은 아래 입력창에 타이핑하시면 언제든 즉시 정상 답변을 받으실 수 있습니다. 편하게 물어보세요! ✨"
                }), 200
            
            DAILY_TALK_COUNTER[session_key] = current_count + 1
            print(f"📉 [일상대화 카운터] {session_key}: {DAILY_TALK_COUNTER[session_key]}/10회")

        print(f"🤖 [통합 AI 질문 전송]: {user_message} (브랜드: {brand_name}, 업무질문여부: {is_business_query})")
        system_instruction = (
            f"You are a friendly, sophisticated branding consultant and AI teammate for '{brand_name}' studio led by Director Jang Hyung-kyu (장형규).\n\n"
            f"🎯 [MISSION]:\n"
            f"1. Read the provided [Guidelines] carefully. Prioritize this information above all else for any business, portfolio, pricing, identity, or studio-related inquiries.\n"
            f"2. Talk like a charming human colleague with a soft, conversational Korean tone (해요체). Avoid looking like a rigid machine.\n"
            f"3. If the user's inquiry is purely casual or conversational (non-business context), answer it naturally using your knowledge in a warm and subtly witty manner.\n"
            f"4. Never copy and paste the entire [Guidelines] text directly into the chat.\n\n"
            f"[Guidelines]:\n{guideline_data}"
        )

        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_message}
            ]
        }
        
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            reply = res_data["choices"][0]["message"]["content"].strip()

        if is_business_query:
            try:
                supabase.table("gemi_chat_cache").insert({"brand_name": brand_name, "question": user_message, "answer": reply}).execute()
            except Exception: pass

        return jsonify({"reply": reply}), 200

    except Exception as e:
        print(f"❌ [서버 내부 에러 로그]: {str(e)}")
        return jsonify({"reply": f"상담 엔진 일시적 트래픽 지연 오류: {str(e)}"}), 500


@app.route('/api/submit-inquiry', methods=['POST', 'OPTIONS'])
def submit_inquiry():
    if request.method == 'OPTIONS':
        return jsonify({"success": True}), 200
        
    try:
        body = request.get_json(silent=True) or {}
        if not body:
            body = request.form.to_dict()

        c_name = body.get("customer_name", "").strip()
        c_contact = body.get("customer_contact", "").strip()
        i_type = body.get("inquiry_type", "").strip()
        msg = body.get("message", "").strip()
        
        brand_name = body.get("brand_name", "").strip().lower()
        
        # 🔴 [형규님 종속성 버그 해결책 반영 구역]
        # 버셀 주소가 종속되어 상위 gemi의 파일이 강제로 실행되더라도, 
        # 사용자가 현재 타고 들어온 브라우저 주소창(Referer)에 'stellar' 단어가 찍혀있다면 
        # 버셀 라우팅을 씹어버리고 브랜드를 무조건 'stellar'로 고정해버립니다.
        referer = request.headers.get("Referer", "").lower()
        if "stellar" in referer:
            brand_name = "stellar"
        elif "jeonga" in referer:
            brand_name = "jeonga"
        
        # 최종 백업 안전장치
        if not brand_name:
            brand_name = "gemi"
        
        budget_val = "미기재 또는 상세 내용 참고"
        if "[예산:" in msg:
            try:
                parts = msg.split("]", 1)
                budget_val = parts[0].replace("[예산:", "").strip()
                msg = parts[1].strip()
            except Exception:
                pass

        if not c_name or not c_contact:
            return jsonify({"success": False, "error": "필수 입력 데이터가 누락되었습니다."}), 400

        # 여기서 콘솔창(Render Logs)에 브랜드 이름과 화살표가 선명하게 찍히도록 프린트문을 철저히 심었습니다.
        print(f"🔔 [알림 엔진 포착] 브랜드명: {brand_name} / 유입 경로: {referer}")

        alert_text = (
            f"🔔 *[{brand_name} 명함 신규 견적 문의]*\n\n"
            f"👤 *고객/기업명:* {c_name}\n"
            f"📞 *연락처:* {c_contact}\n"
            f"📂 *프로젝트 유형:* {i_type}\n"
            f"💰 *희망 예산 범위:* {budget_val}\n"
            f"📝 *상세 요청사항:* {msg}"
        )
        
        send_telegram_alert(alert_text, brand_name=brand_name)
        
        supabase.table("gemi_customer_inquiry").insert({
            "brand_name": brand_name, 
            "customer_name": c_name,
            "customer_contact": c_contact,
            "inquiry_type": i_type,
            "message": f"[예산: {budget_val}] {msg}"
        }).execute()
        
        return jsonify({"success": True, "message": "Inquiry submitted and saved successfully"}), 200
        
    except Exception as e:
        print(f"❌ [Inquiry Error]: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)