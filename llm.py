# llm.py
import re
from google import genai
from google.genai import types

def summarize_event(text, api_type="Gemini", api_key="", max_tokens=1024):
    """
    입력된 역사적 사건 텍스트를 기반으로 7개 카테고리(개요, 배경, 전개/경과, 결과, 영향, 여담, 대중 매체)
    각각 관련된 키워드 12개를 생성하라는 프롬프트를 Gemini API에 전달하고, 
    각 카테고리별 키워드 리스트를 딕셔너리로 반환합니다.
    
    예시 결과: {"개요": [키워드1, 키워드2, ... , 키워드12], ...}
    """
    prompt = (
        f'{text}에 입력된 역사적 사건을 “개요, 배경, 전개, 결과, 영향, 여담, 대중 매체에서 다루는 이 사건” '
        "각각에 대해 관련된 키워드 12개를 생성하시오. 결과는 각 줄이 '카테고리: 키워드1, 키워드2, ..., 키워드12' 형태여야 합니다."
    )
    
    if api_type == "Gemini":
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=0.8
            )
        )
        output_text = response.text
    else:
        raise ValueError("지원되지 않는 API 타입입니다. 현재는 Gemini만 지원합니다.")
    
    categories = ["개요", "배경", "전개/경과", "결과", "영향", "여담", "대중 매체에서 다루는 이 사건"]
    keywords_dict = {}
    lines = output_text.splitlines()
    for line in lines:
        match = re.match(r'^\s*([^:]+)\s*:\s*(.*)', line)
        if match:
            cat = match.group(1).strip()
            keywords = [kw.strip() for kw in match.group(2).split(",") if kw.strip()]
            if cat in categories:
                keywords_dict[cat] = keywords
    for cat in categories:
        if cat not in keywords_dict:
            keywords_dict[cat] = []
    return keywords_dict

if __name__ == "__main__":
    test_text = "이 사건은 19세기 말에 발생한 가상의 전쟁으로, 여러 국가가 참여하여 복잡한 전개를 보였다."
    result = summarize_event(test_text, api_type="Gemini", api_key="YOUR_API_KEY", max_tokens=1024)
    print(result)
