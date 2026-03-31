
import os
import requests
import io
import re
from bs4 import BeautifulSoup
from pypdf import PdfReader
from .config import GOOGLE_API_KEY, GOOGLE_CX

# 헤더 설정 (크롤링 차단 방지)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# PDF 저장 경로 설정
PDF_SAVE_DIR = "output/references"
if not os.path.exists(PDF_SAVE_DIR):
    os.makedirs(PDF_SAVE_DIR, exist_ok=True)

def search_google(query, num=2):
    """
    구글 커스텀 서치 API를 이용해 관련 링크를 찾습니다.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        print("⚠ Google API Key 또는 CX가 없습니다.")
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_CX,
        'q': query,
        'num': num
    }

    try:
        print(f"🔎 검색 수행: {query}")
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            return items 
    except Exception as e:
        print(f"⚠ 검색 중 오류 발생: {e}")
    
    return []

def extract_text_from_pdf(pdf_content):
    """
    PDF 바이너리 데이터에서 텍스트 추출
    """
    try:
        f = io.BytesIO(pdf_content)
        reader = PdfReader(f)
        text = ""
        # 첫 5페이지만 읽기 (속도 및 토큰 제한 고려)
        for page in reader.pages[:5]:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"PDF 읽기 실패: {str(e)}"

def fetch_content(url):
    """
    URL에 접속하여 본문 텍스트를 추출 (HTML or PDF)
    """
    try:
        # PDF 파일인지 확인
        is_pdf = url.lower().endswith('.pdf')
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '').lower()
        
        # PDF 처리
        if is_pdf or 'application/pdf' in content_type:
            print(f"   📄 PDF 다운로드 및 변환: {url}")
            
            # PDF 파일 저장 로직 추가
            try:
                # 파일명 추출 (URL 마지막 부분)
                filename = url.split("/")[-1]
                # 파일명이 너무 길거나 쿼리 파라미터가 있으면 정리
                if "?" in filename:
                    filename = filename.split("?")[0]
                if not filename.lower().endswith(".pdf"):
                    filename += ".pdf"
                
                # 특수문자 제거 및 길이 제한
                filename = re.sub(r'[\\/*?:"<>|]', "", filename)
                if len(filename) > 50:
                    filename = filename[:50]

                # 중복 방지를 위해 타임스탬프 추가 (선택사항, 일단은 덮어쓰기 방지용으로 안전하게)
                import time
                timestamp = int(time.time())
                save_path = os.path.join(PDF_SAVE_DIR, f"{timestamp}_{filename}")
                
                with open(save_path, "wb") as f:
                    f.write(response.content)
                print(f"      └─ [저장 완료] {save_path}")

            except Exception as e:
                print(f"      └─ [저장 실패] {e}")

            return extract_text_from_pdf(response.content)
            
        # HTML 처리
        else:
            print(f"   🌐 웹페이지 분석: {url}")
            # 인코딩 자동 감지
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 불필요한 태그 제거 (스크립트, 스타일, 네비게이션 등)
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.extract()
                
            # 텍스트만 추출
            text = soup.get_text(separator='\n')
            
            # 공백 정리
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
    except Exception as e:
        print(f"   ⚠ 콘텐츠 가져오기 실패 ({url}): {e}")
        return ""

def get_fact_sheet(topic_query):
    """
    주제에 대해 검색하고, 상위 결과의 내용을 요약하여 'Fact Sheet' 텍스트를 반환
    """
    print(f"\n[Web Researcher] '{topic_query}' 자료 수집 시작...")
    
    search_results = search_google(topic_query, num=2) 
    
    fact_sheet = []
    
    for idx, item in enumerate(search_results, 1):
        title = item.get('title', 'No Title')
        link = item.get('link', '')
        snippet = item.get('snippet', '')
        
        # 본문 가져오기
        content = fetch_content(link)
        
        # 본문이 너무 길면 자르기 (약 1500자)
        if len(content) > 1500:
            content = content[:1500] + "...(중략)"
        
        # 검색 결과가 내용이 너무 없으면 스니펫이라도 사용
        if len(content) < 50:
            content = f"(본문 추출 실패, 요약 내용): {snippet}"

        fact_text = f"""
[자료 {idx}]
- 제목: {title}
- 링크: {link}
- 핵심 내용:
{content}
--------------------------------------------------
"""
        fact_sheet.append(fact_text)
        
    return "\n".join(fact_sheet)

if __name__ == "__main__":
    # 테스트
    res = get_fact_sheet("2024년 디지털 헬스케어 시장 규모")
    print(res)
