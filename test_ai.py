import asyncio
from factory_modules.ai_module import get_chatbot_response

# Test data
SUPABASE_URL = "https://bjbpjkeahkupmeuvfwys.supabase.co"
SUPABASE_KEY = "sb_publishable_yHPGOhKSEPAehg-sin-7IQ_nHtfYBWU"
client_name = "테스트의뢰인"
client_info = "이 회사는 친환경 비건 화장품을 만드는 MUI 브랜드입니다. 대표 향은 흙 내음(Earthy)입니다."
question = "MUI 브랜드의 대표 향이 뭐야?"

async def main():
    # Call the function and print the result
    answer = get_chatbot_response(client_name, client_info, question)
    print(f"Answer: {answer}")

if __name__ == "__main__":
    asyncio.run(main())