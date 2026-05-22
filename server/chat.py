import json
import os
import urllib.request
import requests
import time # 중복 요청 방지용 시간 라이브러리 추가
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# CORS 보안 설정 (Vercel 도메인 연동 허용)
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

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 마지막 요청 시간을 저장할 전역 딕셔너리 (전송 중복 방지용)
last_requests = {}

# 👑 [추가] 업무 외 사적인 질문인지 판별하기 위한 키워드 사전
NON_BIZ_KEYWORDS = [
    "안녕", "반가워", "누구", "이름", "나이", "사는곳", "취미", "날씨", "밥", "오늘 뭐해", 
    "좋아", "싫어", "화이팅", "사랑해", "웃겨", "심심", "놀자", "MBTI", "맛집", "노래"
]

def send_telegram_alert(text: str):
    if not TELEGRAM_BOT_TOKEN:
        print("❌ [Telegram] 에러: TELEGRAM_TOKEN 환경 변수가 설정되지 않았습니다.")
        return
    
    url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){TELEGRAM_BOT_TOKEN}/sendMessage"
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

    if not OPENROUTER_API_KEY:
        return jsonify({"reply": "API Key가 설정되지 않았습니다."}), 500

    try:
        body = request.get_json(silent=True) or {}
        user_message = body.get("message", "").strip()
        guideline_txt = body.get("guideline_txt", "") # 👑 프론트에서 분리해서 보낸 가이드라인 수신

        if not user_message:
            return jsonify({"reply": "질문을 입력해주세요."})

        # 👑 [앵무새 버그 교정] 가이드라인과 질문이 엉켜서 AI에게 전달되는 것을 방지
        # 순수한 사용자의 질문 텍스트만 추출
        clean_user_question = user_message.replace("[참고 가이드라인]:", "").split("\n\n")[0].strip()

        # 👑 [전송 중복 방지] 0.3초 이내에 동일한 질문이 들어오면 AI 호출 없이 무시
        current_time = time.time()
        # IP 기반으로 세션 구분 (간단 구현)
        session_id = request.remote_addr + clean_user_question
        
        if session_id in last_requests:
            if current_time - last_requests[session_id] < 0.3:
                return jsonify({"reply": "잠시만 기다려주시면 답변이 나옵니다..."}), 200 # 이전 답변 대기
        last_requests[session_id] = current_time

        # 👑 **[최종 최적화 설계 - 1순위] Supabase 장부(faq_cache) 우선 매칭 (토큰 0% 소모)**
        # 완전 일치하는 질문이 있는지 장부에서 검색
        try:
            # 아코디언 버튼 클릭 시 넘어오는 깨끗한 질문 텍스트로 검색해야 함
            cache = supabase.table("gemi_chat_cache").select("answer").eq("question", clean_user_question).execute()
            if cache.data and len(cache.data) > 0:
                print(f"✅ [캐시 장부 매칭 성공] 토큰 소모 없이 장부 답변 반환: {clean_user_question}")
                return jsonify({"reply": cache.data[0]["answer"]}), 200
        except Exception: pass # 캐시 조회 오류 시 AI 호출로 우회

        # 👑 **[최종 최적화 설계 - 2순위] 일상대화 필터링 (토큰 0% 소모, 카운트 차단)**
        # 질문에 사적인 키워드가 포함되었는지 1차 판별
        is_non_biz_question = any(keyword in clean_user_question.lower() for keyword in NON_BIZ_KEYWORDS)
        
        if is_non_biz_question:
            # AI 호출하지 않고 차분한 미니멀 전용 일상대화 답변 5종 중 랜덤 반환
            non_biz_replies = [
                "저는 디렉터님의 업무를 든든하게 보조하는 AI 어시스턴트입니다.\n제작 및 비용 관련 궁금한 점을 물어봐 주시면 정성껏 답변해 드릴게요.",
                "반갑습니다.\n차분하고 미니멀한 공간을 그리는 디렉터님의 명함입니다.\n문의 사항을 남겨주시면 AI가 가이드라인에 맞춰 안내해 드립니다.",
                "일상적인 대화도 즐겁지만,\n지금은 디렉터님의 프로젝트 문의에 집중하고 싶습니다.\n궁금하신 제작 관련 내용을 물어봐 주시겠어요?",
                "저는 디렉터님의 포트폴리오와 제작 방식을 안내하는 전용 상담원입니다.\n업무 관련 질문을 남겨주시면 감사하겠습니다.",
                "디렉터님은 공간의 본질에 집중하며 차분한 미니멀리즘을 지향합니다.\n제작 방식이나 상세 비용이 궁금하시다면 편하게 물어봐 주세요."
            ]
            import random
            random_reply = random.choice(non_biz_replies)
            print(f"🔒 [일상대화 필터링] AI 호출 없이 고정 답변 반환: {clean_user_question}")
            return jsonify({"reply": random_reply}), 200

        # 👑 **[최종 최적화 설계 - 3순위] 가이드라인 문서 최우선 기반 AI 답변 (토큰 소모)**
        # 위 두 개에 모두 해당하지 않는 업무 관련 질문일 때만 AI 호출
        print(f"🤖 [AI 호출] 가이드라인 최우선 참고하여 답변 생성 중...: {clean_user_question}")
        
        # 시스템 지침을 통해 앵무새 답변(가이드라인 그대로 출력)을 강력 차단하고, 가이드라인 최우선 명령
        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {"role": "system", "content": (
                    "You are a premium branding expert consulting agent. "
                    "Your primary task is to answer user inquiries strictly based on the provided [Guidelines] document. "
                    "You must remain professional, kind, and minimalist (premium hotel towel mood). "
                    "DO NOT echo or repeat the entire [Guidelines] text in your answer. "
                    "If the answer is found in the [Guidelines], summarize and present it gently. "
                    "If the question is completely irrelevant to the [Guidelines] or business, politely explain that you can only provide information related to spatial design and branding business. "
                    "[Guidelines]:\n" + guideline_txt # 👑 Base64 풀린 가이드라인 텍스트를 시스템 지침에 주입
                )},
                {"role": "user", "content": f"원문 문의 내용:\n{clean_user_question}"} # 👑 가이드라인 빠진 깨끗한 질문만 user로 전달
            ]
        }
        
        req = urllib.request.Request(
            "[https://openrouter.ai/api/v1/chat/completions](https://openrouter.ai/api/v1/chat/completions)",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=10) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            reply = res_data["choices"][0]["message"]["content"].strip()

        # 👑 AI가 답변해 준 내용을 장부에 저장 (0.3초 이내 중복 요청에 대한 사후 저장)
        try:
            supabase.table("gemi_chat_cache").insert({"question": clean_user_question, "answer": reply}).execute()
        except Exception: pass # 캐시 저장 오류 시 그냥 통과

        return jsonify({"reply": reply}), 200

    except Exception as e:
        print(f"❌ [Server Chat Error]: {str(e)}")
        return jsonify({"reply": f"죄송합니다. 통신 중 잠시 오류가 발생했습니다: {str(e)}"}), 500


# 견적 상담 수집 라우터 (필수값 유효성 검사 추가)
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

        # 🚨 [백엔드 유효성 검사 완비] 프론트를 뚫고 들어온 빈 데이터 방어
        if not c_name or not c_contact:
            print("❌ [Inquiry 필수값 누락] 전송 차단.")
            return jsonify({"success": False, "error": "Name and Contact are required."}), 400

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
            "brand_name": "GeMi", # 기본 브랜드 아이덴티티 지정
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