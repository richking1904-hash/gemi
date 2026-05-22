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

# [대화형 카운터 레이어] 사용자의 일상대화 횟수만 카운트하는 저장소
DAILY_TALK_COUNTER = {}

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
        brand_name = body.get("brand_name", "GeMi").strip()

        if not user_message:
            return jsonify({"reply": "질문 내용이 비어있습니다."}), 200

        # [검증 1순위] 내 브랜드 서랍에 등록된 고정 FAQ 버튼 매칭 (토큰 0개 즉시 리턴)
        try:
            cache = supabase.table("gemi_chat_cache").select("answer").eq("brand_name", brand_name).eq("question", user_message).execute()
            if cache.data and len(cache.data) > 0:
                for item in cache.data:
                    if item.get("answer") and "[가이드라인 문서]" not in item["answer"]:
                        print(f"✅ [FAQ 매칭 성공] {brand_name} 고정 답변 리턴: {user_message}")
                        return jsonify({"reply": item["answer"]}), 200
        except Exception as cache_err:
            print(f"ℹ️ 캐시 장부 매칭 패스: {cache_err}")

        # [업무용 질문 판별기] 핵심 단어가 포함되어 있다면 일상 제한 레이어를 완전히 우회시킵니다.
        is_business_query = False
        keywords_for_business = [
            "제작", "비용", "단가", "포트폴리오", "기간", "일정", "연락", "이메일", "전화", "문의", 
            "견적", "작업", "의뢰", "수정", "환불", "금액", "디자인", "명함", "단추", "스튜디오", "가격"
        ]
        if any(k_word in user_message for k_word in keywords_for_business):
            is_business_query = True

        # [검증 2순위] 일상대화 필터링 및 한도 초과 시 고정 저장 문구 리턴 (토큰 세이브)
        if not is_business_query:
            client_ip = request.remote_addr or "anonymous"
            session_key = f"{brand_name}_{client_ip}"
            current_count = DAILY_TALK_COUNTER.get(session_key, 0)
            
            # 일상대화 10회 제한 초과 시 -> AI 호출 없이 고정 안내문만 출력 (토큰 소모 0)
            if current_count >= 10:
                print(f"🚫 [일상 제한 발동] {session_key}: 일상 질문 한도 초과로 고정 문구 출력")
                return jsonify({
                    "reply": "🔒 디렉터님의 프로젝트 소통을 보조하기 위한 오늘 자 일상 대화 한도(10회)가 소진되었습니다!\n\n하지만 견적 문의, 포트폴리오 확인, 디자인 단가 등의 업무 관련 질문은 아래 입력창에 타이핑하시면 언제든 즉시 정상 답변을 받으실 수 있습니다. 편하게 물어보세요! ✨"
                }), 200
            
            # 한도 내 일상대화 카운트 적립 및 위트 답변 추론
            DAILY_TALK_COUNTER[session_key] = current_count + 1
            print(f"📉 [일상대화 카운터] {session_key}: {DAILY_TALK_COUNTER[session_key]}/10회")

            daily_system_instruction = (
                f"You are a friendly and witty AI assistant for the premium minimalist design studio '{brand_name}'.\n"
                "The user is asking a casual, non-business question. Answer based on your general knowledge.\n"
                "Keep your answer short (1-3 sentences), warm, natural, and subtly witty (like a charming team member, not a robot).\n"
                "Speak in polite, conversational Korean (해요체)."
            )

            daily_payload = {
                "model": "google/gemini-2.0-flash-001",
                "messages": [
                    {"role": "system", "content": daily_system_instruction},
                    {"role": "user", "content": user_message}
                ]
            }

            req_daily = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(daily_payload).encode('utf-8'),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            )

            with urllib.request.urlopen(req_daily) as res:
                res_data = json.loads(res.read().decode('utf-8'))
                reply = res_data["choices"][0]["message"]["content"].strip()
                
            return jsonify({"reply": reply}), 200

        # [검증 3순위] 순수 실시간 업무 관련 질문 (가이드라인 기반 AI 무제한 가동)
        print(f"🤖 [업무 AI 질문 전송]: {user_message} (브랜드: {brand_name})")
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
        
        # 👑 [교정 추가] Vercel 비동기 요청 본문에서 독립된 budget(예산) 데이터를 안전하게 추출
        # 만약 프론트엔드에서 message 필드 안에 통째로 묶어서 보냈을 상황을 대비해 예외 안전망을 쳐둡니다.
        budget_val = "미기재 또는 상세 내용 참고"
        if "[예산:" in msg:
            try:
                # "[예산: 300만원] 내용내용" 형태에서 예산 텍스트 분리 파싱
                parts = msg.split("]", 1)
                budget_val = parts[0].replace("[예산:", "").strip()
                msg = parts[1].strip()  # 메시지 본문은 깨끗하게 복구
            except Exception:
                pass

        if not c_name or not c_contact:
            return jsonify({"success": False, "error": "필수 입력 데이터가 누락되었습니다."}), 400

        # 👑 [텔레그램 알림 양식 고도화] 5대 입력칸이 각각 명확히 구분되도록 전면 수정
        alert_text = (
            f"🔔 *[GeMi 명함 신규 견적 문의]*\n\n"
            f"👤 *고객/기업명:* {c_name}\n"
            f"📞 *연락처:* {c_contact}\n"
            f"📂 *프로젝트 유형:* {i_type}\n"
            f"💰 *희망 예산 범위:* {budget_val}\n"
            f"📝 *상세 요청사항:* {msg}"
        )
        send_telegram_alert(alert_text)
        
        # Supabase DB 적재할 때도 가독성을 위해 가공된 내용을 예쁘게 기록합니다.
        supabase.table("gemi_customer_inquiry").insert({
            "brand_name": "GeMi", 
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