# wiki.py
import re

def process_text_for_wiki(text, start_counter=1):
    """
    텍스트 내 대괄호([])는 볼드 효과 없이 가독성 높은 하늘색(#00aaff) 텍스트로 변환하고,
    소괄호 내 주석은 각주로 변환합니다.
    각주는 <a> 태그를 사용하여, 마우스 오버 시 주석 내용을 툴팁(title 속성)으로 표시하고,
    고유 id("footnotemark-{n}")를 부여하여 하단 각주로부터 돌아갈 수 있도록 합니다.
    
    Returns:
        processed: 변환된 본문 텍스트
        footnotes: [(번호, 주석 내용), ...]
        counter: 최종 증가한 번호
    """
    footnotes = []
    counter = start_counter

    def replace_comment(match):
        nonlocal counter
        comment = match.group(1)
        footnotes.append((counter, comment))
        replacement = (f'<a href="#footnote-{counter}" id="footnotemark-{counter}" '
                       f'style="text-decoration:none; color:#00aaff;" title="{comment}">'
                       f'<sup>[{counter}]</sup></a>')
        counter += 1
        return replacement

    # 대괄호 [] 내 텍스트 -> 하늘색 (#00aaff) 텍스트, bold 효과 없이
    processed = re.sub(r'\[([^\]]+)\]', r'<span style="color:#00aaff;">\1</span>', text)
    # 소괄호 () 내 주석 -> 각주 처리 (위의 replace_comment 함수 사용)
    processed = re.sub(r'\(([^)]+)\)', replace_comment, processed)

    return processed, footnotes, counter

def generate_wiki_html(event_title, original_text, detailed_articles, output_file="wiki.html"):
    """
    event_title: 사건의 제목
    original_text: 원본 텍스트 (옵션)
    detailed_articles: 딕셔너리, 키: "개요", "배경", "전개/경과"(전개), "결과", "영향", "여담", "대중 매체"
    
    - 최상단 헤더는 초록색 배경의 "생성형 위키" 타이틀.
    - 그 아래 별도의 영역에 event_title이 표시됩니다.
    - 목차는 배경 없이 파란색 텍스트 링크로 제공됩니다.
    - 각 섹션은 번호가 붙으며, "전개/경과"는 "전개", "대중 매체"는 "대중 매체에서의 {event_title}"로 표시됩니다.
    - 본문 내 대괄호는 하늘색(#00aaff) 텍스트로, 소괄호 주석은 각주 마커로 변환되며, 마우스 오버 시 툴팁으로 주석 내용을 확인할 수 있습니다.
    - 하단 각주 목록의 각 항목은 원래 각주 마커로 돌아가는 링크를 포함합니다.
    """
    # "전개/경과" 키가 있다면 "전개"로 대체
    articles = detailed_articles.copy()
    if "전개/경과" in articles:
        articles["전개"] = articles.pop("전개/경과")
    
    sections = [
        ("1. 개요", articles.get("개요", "")),
        ("2. 배경", articles.get("배경", "")),
        ("3. 전개", articles.get("전개", "")),
        ("4. 결과", articles.get("결과", "")),
        ("5. 영향", articles.get("영향", "")),
        ("6. 여담", articles.get("여담", "")),
        (f"7. 대중 매체에서의 {event_title}", articles.get("대중 매체에서 다루는 이 사건", ""))
    ]
    
    section_html = ""
    all_footnotes = []
    current_counter = 1
    for title, content in sections:
        processed_content, footnotes, current_counter = process_text_for_wiki(content, start_counter=current_counter)
        processed_content = processed_content.replace("\n", "<br/>")
        all_footnotes.extend(footnotes)
        # 섹션 id: 제목의 번호와 한글 부분을 조합 (공백 제거)
        sec_id = title.split()[1] if len(title.split()) > 1 else title.replace(".", "")
        section_html += f"""
    <section id="{sec_id}">
      <h2>{title}</h2>
      <p>{processed_content}</p>
    </section>
    """
    
    toc_html = f"""
    <div class="toc">
      <h2>목차</h2>
      <ul>
        <li><a href="#개요" style="color:#007acc; text-decoration:none;">1. 개요</a></li>
        <li><a href="#배경" style="color:#007acc; text-decoration:none;">2. 배경</a></li>
        <li><a href="#전개" style="color:#007acc; text-decoration:none;">3. 전개</a></li>
        <li><a href="#결과" style="color:#007acc; text-decoration:none;">4. 결과</a></li>
        <li><a href="#영향" style="color:#007acc; text-decoration:none;">5. 영향</a></li>
        <li><a href="#여담" style="color:#007acc; text-decoration:none;">6. 여담</a></li>
        <li><a href="#대중매체" style="color:#007acc; text-decoration:none;">7. 대중 매체에서의 {event_title}</a></li>
      </ul>
    </div>
    """
    
    footnotes_html = ""
    if all_footnotes:
        footnotes_html += "<div class='footnotes'><h2>각주</h2><ol>"
        for idx, note in all_footnotes:
            # 각주 항목에 원래 footnote 마커로 돌아가는 링크를 추가
            footnotes_html += f'<li id="footnote-{idx}"><a href="#footnotemark-{idx}" style="text-decoration:none; color:#00aaff;">[{idx}]</a> {note}</li>'
        footnotes_html += "</ol></div>"
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{event_title} - 생성형 위키</title>
  <style>
    body {{
      font-family: 'Noto Sans KR', sans-serif;
      background-color: #ffffff;
      color: #333;
      margin: 0;
      padding: 0;
      line-height: 1.6;
    }}
    .container {{
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }}
    header {{
      background-color: #2e7d32;
      color: #fff;
      padding: 20px;
      text-align: center;
    }}
    header h1 {{
      margin: 0;
      font-size: 32px;
    }}
    .sub-title {{
      text-align: center;
      font-size: 26px;
      margin: 20px 0;
      color: #333;
      background-color: #ffffff;
      padding: 10px;
      border: 1px solid #ccc;
    }}
    .toc {{
      padding: 10px;
      margin: 20px 0;
      border-bottom: 1px solid #ccc;
    }}
    .toc ul {{
      list-style: none;
      padding-left: 0;
    }}
    .toc li {{
      margin-bottom: 8px;
    }}
    .toc a {{
      color: #007acc;
      text-decoration: none;
      font-weight: bold;
    }}
    section {{
      margin-bottom: 30px;
      padding: 20px;
      border: 1px solid #81c784;
      border-radius: 4px;
      background-color: #ffffff;
    }}
    section h2 {{
      margin-bottom: 15px;
      border-bottom: 1px solid #c8e6c9;
      padding-bottom: 5px;
    }}
    .footnotes {{
      font-size: 14px;
      color: #555;
      border-top: 1px solid #ccc;
      padding-top: 10px;
    }}
    .footnotes ol {{
      padding-left: 20px;
    }}
    footer {{
      text-align: center;
      font-size: 14px;
      color: #555;
      margin-top: 30px;
      padding: 20px;
      border-top: 1px solid #ccc;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>생성형 위키</h1>
    </header>
    <div class="sub-title">{event_title}</div>
    {toc_html}
    {section_html}
    {footnotes_html}
    <footer>
      <p>© 2025 생성형 위키. All rights reserved.</p>
    </footer>
  </div>
</body>
</html>
"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    return html

if __name__ == "__main__":
    # 테스트 예시
    event_title = "가상의 전쟁 사건"
    original_text = "이 사건은 19세기 말에 발생한 가상의 전쟁에 관한 내용이다."
    detailed_articles = {
        "개요": "[전쟁]은 (치열한 충돌) 역사상 중요한 사건이다.",
        "배경": "국제정세 (불안정한 상황)와 경제 위기 (심각한 문제)가 겹쳤다.",
        "전개/경과": "전개 1: [전략]에 따른 첫 충돌 (예상치 못한 전개). 전개 2: 추가 전투 (변수 등장).",
        "결과": "결과적으로 (예측 불가) 승리와 패배가 공존했다.",
        "영향": "사회 전반에 (장기적 후폭풍)이 나타났다.",
        "여담": "비화로 (흥미로운 사실) 여러 에피소드가 있다.",
        "대중 매체": "[보도]와 (논란의 중심)이 되었다."
    }
    generate_wiki_html(event_title, original_text, detailed_articles)
