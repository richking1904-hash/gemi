# api/chat.py
import json
import os
print("DEBUG: API가 호출되었습니다!")
import urllib.request
from supabase import create_client

# 설정 (환경 변수에서 호출하도록 확실하게 구성)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Vercel이 호출할 핵심 함수
def handler(request):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return {"reply": "API Key가 설정되지 않았습니다."}, 500

    try:
        body = request.get_json()
        user_message = body.get("message", "").strip()

        cache = supabase.table("gemi_chat_cache").select("answer").eq("question", user_message).execute()
        if cache.data and len(cache.data) > 0:
            return {"reply": cache.data[0]["answer"]}

        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {"role": "system", "content": "너는 브랜드 전문 상담원이야. 제공된 가이드라인을 바탕으로 친절하게 답변해."},
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
            reply = res_data["choices"][0]["message"]["content"]

        supabase.table("gemi_chat_cache").insert({"question": user_message, "answer": reply}).execute()

        return {"reply": reply}

    except Exception as e:
        return {"reply": f"서버 실행 오류: {str(e)}"}, 500