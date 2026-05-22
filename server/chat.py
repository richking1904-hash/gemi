import json
import os
import urllib.request
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# CORS 보안 설정 완벽 선언 (브라우저 차단 및 문법 에러 방지)
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
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = "859745575"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 👑 [추가] 업무 외 일상대화 필터링을 위한 키워드 목록
DAILY_KEYWORDS = ["안녕", "반가워", "누구", "나이", "사는곳", "날씨", "밥", "오늘 뭐해", "MBTI", "맛집", "놀자", "심심"]

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
        
        # 👑 [구조 정밀 교정] 프론트엔드에서 안전하게 전송된 가이드라인 패키지 수신 처리
        guideline_data = body.get("guideline_txt", "")

        if not user_message:
            return jsonify({"reply": "질문 내용이 비어있습니다."}), 200

        # 👑 [최적화 설계 - 1순위] Supabase 캐시 장부 우선 매칭 (토큰 0% 소모)
        try:
            cache = supabase.table("gemi_chat_cache").select("answer").eq("question", user_message).execute()
            if cache.data and len(cache.data) > 0:
                return jsonify({"reply": cache.data[0]["answer"]})
        except Exception as cache_err:
            print(f"ℹ️ 캐시 조회 패스: {cache_err}")

        # 👑 [최적화 설계 - 2순위] 업무 무관 일상대화 필터링 (토큰 0% 소모 및 AI 호출 차단)
        is_daily_talk = any(word in user_message.lower() for word in DAILY_KEYWORDS)
        if is_daily_talk:
            return jsonify({
                "reply": "안녕하세요. 저는 디렉터님의 프로젝트 안내를 보조하는 AI 팀원입니다.\n포트폴리오 확인 및 견적 제작 관련 문의를 주시면 가이드라인에 맞춰 상세히 답변해 드릴 수 있습니다."
            }), 200

        # 👑 [최적화 설계 - 3순위] 가이드라인 기반 정밀 AI 프롬프팅 조립
        # 시스템 지침과 사용자 질문의 역할을 엄격히 분리하여 앵무새 에러 완벽 차단
        system_instruction = (
            "너는 브랜드 및 공간 디자인 에이전시의 전문 상담원이야. "
            "반드시 아래 제공된 [가이드라인 문서] 내용을 완벽하게 숙지하고 이를 최우선 기준으로 삼아 답변해줘.\n"
            "고객에게 가이드라인 텍스트 원본을 통째로 읊거나 복사해서 주지 말고, 핵심만 요약해서 정중하고 명확하게 답변해.\n"
            "만약 가이드라인 문서로 답변할 수 없는 엉뚱한 질문이라면, 업무 관련 안내만 가능함을 정중히 안내해.\n\n"
            f"[가이드라인 문서]:\n{guideline_data}"
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

        # 캐시 저장
        try:
            supabase.table("gemi_chat_cache").insert({"question": user_message, "answer": reply}).execute()
        except Exception: pass

        return jsonify({"reply": reply})

    except Exception as e:
        # 👑 예외 발생 시 프론트엔드가 멈추지 않도록 명확한 에러 로그 반환 처리
        print(f"❌ [서버 내부 에러 로그]: {str(e)}")
        return jsonify({"reply": f"상담 엔진 일시적 트래픽 지연 오류: {str(e)}"}), 500


# 🚨 슈파베이스의 진짜 컬럼명 규칙을 200% 일치시킨 대문
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

        # 👑 [백엔드 방어 보완] 필수 입력값인 성함과 연락처가 모두 누락되었을 경우 요청 차단
        if not c_name or not c_contact:
            return jsonify({"success": False, "error": "필수 입력 데이터가 누락되었습니다."}), 400

        # 1. 텔레그램 메시지 알림 발송
        alert_text = (
            f"🔔 *[GeMi 명함 신규 견적 문의]*\n\n"
            f"👤 *고객/기업명:* {c_name}\n"
            f"📞 *연락처:* {c_contact}\n"
            f"📂 *프로젝트 유형:* {i_type}\n"
            f"📝 *상세 내용:* {msg}"
        )
        send_telegram_alert(alert_text)
        
        # 2. 형규님의 진짜 컬럼명과 정확하게 1:1로 매칭하여 데이터 꽂아 넣기
        supabase.table("gemi_customer_inquiry").insert({
            "brand_name": "GeMi", 
            "customer_name": c_name,
            "customer_contact": c_contact,
            "inquiry_type": i_type,
            "message": msg
        }).execute()
        
        return jsonify({"success": True, "message": "Inquiry submitted and saved successfully"}), 200
        
    except Exception as e:
        print(f"❌ [Inquiry Error]: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)