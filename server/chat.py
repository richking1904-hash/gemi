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
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = "859745575"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        guideline_data = body.get("guideline_txt", "")

        if not user_message:
            return jsonify({"reply": "질문 내용이 비어있습니다."}), 200

        # 👑 [최적화 교정 - 1순위] 리모컨 고정 FAQ 데이터를 장부에서 최우선 매칭 (AI 절대 차단)
        # 중요: 새로 유입된 질문이 장부에 중복 적재되기 전에 완전 매칭되는 진짜 답변을 먼저 리턴하고 함수를 끝냅니다.
        try:
            cache = supabase.table("gemi_chat_cache").select("answer").eq("question", user_message).execute()
            if cache.data and len(cache.data) > 0:
                # 리모컨으로 등록한 기존 답변 배열 중 가장 온전한 데이터를 선택하여 즉시 반환
                for item in cache.data:
                    if item.get("answer") and "[가이드라인 문서]" not in item["answer"]:
                        print(f"✅ [FAQ 매칭 성공] 고정 장부 답변 즉시 리턴: {user_message}")
                        return jsonify({"reply": item["answer"]}), 200
        except Exception as cache_err:
            print(f"ℹ️ 캐시 장부 매칭 패스: {cache_err}")

        # 👑 [최적화 교정 - 2순위] 일상대화 필터링 (토큰 0%, 장부 적재 불필요)
        is_daily_talk = any(word in user_message.lower() for word in DAILY_KEYWORDS)
        if is_daily_talk:
            return jsonify({
                "reply": "안녕하세요. 저는 디렉터님의 프로젝트 안내를 보조하는 AI 팀원입니다.\n포트폴리오 확인 및 견적 제작 관련 문의를 주시면 가이드라인에 맞춰 상세히 답변해 드릴 수 있습니다."
            }), 200

        # 👑 [최적화 교정 - 3순위] 순수 실시간 질문만 가이드라인 기반 AI 작동
        print(f"🤖 [순수 AI 호출 진행]: {user_message}")
        system_instruction = (
            "Answering user inquiries strictly based on the provided [Guidelines].\n"
            "DO NOT echo or repeat the entire [Guidelines] text in your answer.\n"
            "If you cannot answer based on Guidelines, politely decline.\n\n"
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

        # 👑 [중복 저장 방지] 실시간 AI가 답변한 순수 결과물만 장부에 사후 적재 처리
        # 리모컨으로 심은 고정 FAQ 질문이 아니라면 안전하게 캐시 장부에 추가합니다.
        try:
            supabase.table("gemi_chat_cache").insert({"question": user_message, "answer": reply}).execute()
        except Exception: pass

        return jsonify({"reply": reply})

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

        if not c_name or not c_contact:
            return jsonify({"success": False, "error": "필수 입력 데이터가 누락되었습니다."}), 400

        alert_text = (
            f"🔔 *[GeMi 명함 신규 견적 문의]*\n\n"
            f"👤 *고객/기업명:* {c_name}\n"
            f"📞 *연락처:* {c_contact}\n"
            f"📂 *프로젝트 유형:* {i_type}\n"
            f"📝 *상세 내용:* {msg}"
        )
        send_telegram_alert(alert_text)
        
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