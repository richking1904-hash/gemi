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
CORS(app) # 프론트엔드에서의 접근 허용

# 환경 변수 호출
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = "859745575"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

@app.route('/chat', methods=['POST'])
def chat():
    api_key = OPENROUTER_API_KEY
    if not api_key:
        return jsonify({"reply": "API Key가 설정되지 않았습니다."}), 500

    try:
        body = request.get_json()
        user_message = body.get("message", "").strip()

        # Supabase 캐시 확인
        cache = supabase.table("gemi_chat_cache").select("answer").eq("question", user_message).execute()
        if cache.data and len(cache.data) > 0:
            return jsonify({"reply": cache.data[0]["answer"]})

        # OpenRouter AI 호출
        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {"role": "system", "content": "너는 브랜드 전문 상담원이야. 제공된 가이드라인을 바탕으로 친절하게 답변해."},
                {"role": "user", "content": user_message}
            }
        }
        
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            reply = res_data["choices"][0]["message"]["content"]

        # 캐시 저장
        supabase.table("gemi_chat_cache").insert({"question": user_message, "answer": reply}).execute()

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"서버 실행 오류: {str(e)}"}), 500

@app.route('/api/submit-inquiry', methods=['POST'])
def submit_inquiry():
    try:
        body = request.get_json()
        customer_name = body.get("customer_name", "").strip()
        customer_contact = body.get("customer_contact", "").strip()
        inquiry_type = body.get("inquiry_type", "").strip()
        message = body.get("message", "").strip()

        # 텔레그램 메시지 포맷팅
        alert_text = (
            f"🔔 *[GeMi 명함 신규 견적 문의]*\n\n"
            f"👤 *고객/기업명:* {customer_name}\n"
            f"📞 *연락처:* {customer_contact}\n"
            f"📂 *프로젝트 유형:* {inquiry_type}\n"
            f"📝 *상세 내용:* {message}"
        )
        
        # 텔레그램 알림 발송
        send_telegram_alert(alert_text)
        
        return jsonify({"success": True, "message": "Inquiry submitted successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)