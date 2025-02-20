# llm_to_wiki.py
from google import genai
from google.genai import types

def expand_category(text, category, keywords, api_key, max_tokens=8192):
    """
    주어진 원본 텍스트와 해당 카테고리의 12개 키워드를 토대로, Namuwiki 스타일의 상세 문서를 생성합니다.
    주요 키워드는 []로 감싸고, 일부 주석은 ()로 표기하며 (반드시 몇 개의 주석 포함),
    '전개' 카테고리의 경우 여러 부분으로 나눌 수 있도록 합니다.
    최종 출력은 한글로 작성되어야 합니다.
    """
    prompt = f"이벤트 설명 : \"{text}\"를 바탕으로, 카테고리 \"{category}\"에 대해, 다음 키워드를 사용하여: [{', '.join(keywords)}], 한국어로 위키피디아와 같이 역사적 사건을 서술하는 문장을 생성해 주세요. 주요 키워드는 대괄호로 감싸고, 몇몇 주석은 소괄호로 표시하여 각주로 포함시켜 주세요. {category}와 {text}는 출력에 포함되어선 안됩니다. 이 사건이 가상의 사건임을 언급해서는 안됩니다. \\n을 통해 개행을 해주세요. 개행을 너무 자주해서는 안됩니다."


    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=0.8
        )
    )
    result_text = response.text
    return result_text

def expand_event_to_wiki(text, keywords_dict, api_key, max_tokens=8192):
    """
    각 카테고리별 키워드 리스트(keywords_dict)와 원본 텍스트를 바탕으로 상세 위키 문서를 생성합니다.
    Returns:
        dict: 각 카테고리별 상세 문서 (문자열)
    """
    wiki_articles = {}
    for category, keywords in keywords_dict.items():
        detailed_article = expand_category(text, category, keywords, api_key, max_tokens)
        wiki_articles[category] = detailed_article
    return wiki_articles

if __name__ == "__main__":
    test_text = "이 사건은 19세기 말에 발생한 가상의 전쟁으로, 여러 국가가 참여하여 복잡한 전개를 보였다."
    keywords_dict = {
        "개요": ["전쟁", "가상", "참여", "국가", "복잡", "개요", "19세기", "말", "사건", "역사", "예시", "분석"],
        "배경": ["배경", "정치", "경제", "사회", "상황", "원인", "동기", "국제", "내부", "요인", "분석", "사례"],
        "전개/경과": ["전개", "전투", "진행", "과정", "변화", "전략", "전술", "결정적", "순서", "전환", "중요", "사건"],
        "결과": ["결과", "승리", "패배", "변화", "후유증", "영향", "합의", "조약", "변동", "사건", "분석", "정리"],
        "영향": ["영향", "후폭풍", "사회", "정치", "경제", "문화", "장기", "변화", "사례", "분석", "피해", "효과"],
        "여담": ["여담", "뒷이야기", "비화", "에피소드", "특이", "재미", "소문", "사건", "비판", "의문", "추가", "논의"],
        "대중 매체에서 다루는 이 사건": ["대중", "매체", "보도", "영향력", "이미지", "전파", "문학", "영화", "방송", "분석", "반응", "예시"]
    }
    api_key = "YOUR_API_KEY"
    detailed_articles = expand_event_to_wiki(test_text, keywords_dict, api_key, max_tokens=8192)
    for cat, article in detailed_articles.items():
        print(f"--- {cat} ---")
        print(article)
        print("\n")
