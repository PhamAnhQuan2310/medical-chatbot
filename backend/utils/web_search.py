import requests
import json
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv


SERPER_API_KEY = "fb79bf62763fba510043b0b55eb4e6b57aacdc4a"
def search_web(query, num_results=5, serper_api_key=None):
    """
    Tìm kiếm thông tin trên Google thông qua Serper API.
    
    Args:
        query (str): Câu truy vấn tìm kiếm
        num_results (int): Số kết quả trả về
        serper_api_key (str): API key cho Serper.dev
        
    Returns:
        list: Danh sách kết quả tìm kiếm, mỗi kết quả là dict với title, link, snippet
    """
    
    api_key = serper_api_key or os.getenv("SERPER_API_KEY")
    
    if not api_key:
        return {"error": "API key for Serper is missing"}
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    params = {
        'q': query,
        'gl': 'vn',  
        'hl': 'vi',  
    }
    
    try:
        response = requests.post(
            'https://google.serper.dev/search',
            headers=headers,
            data=json.dumps(params)
        )
        response.raise_for_status()
        search_results = response.json()
        
        formatted_results = []
        
        
        if 'organic' in search_results:
            for result in search_results['organic'][:num_results]:
                formatted_results.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', '')
                })
        
        return formatted_results
    
    except Exception as e:
        return {"error": f"Error occurred during web search: {str(e)}"}

def fallback_search(query):
    """
    Phương pháp dự phòng khi không có API key hoặc API gặp lỗi.
    Sử dụng URL trực tiếp đến Google Search.
    """
   
    encoded_query = quote_plus(query)
    search_url = f"https://www.google.com/search?q={encoded_query}"
    
    return {
        "message": "Tôi không tìm thấy thông tin trong cơ sở dữ liệu của mình.",
        "suggestion": f"Bạn có thể tìm kiếm trực tiếp trên Google: {search_url}"
    }

def generate_web_search_response(query, gemini_api_url, gemini_api_key, search_results=None):
    """
    Tạo phản hồi dựa trên kết quả tìm kiếm web sử dụng Gemini API
    
    Args:
        query (str): Câu hỏi gốc của người dùng
        gemini_api_url (str): URL của Gemini API
        gemini_api_key (str): API key của Gemini
        search_results (list): Kết quả tìm kiếm từ web (có thể None)
        
    Returns:
        str: Câu trả lời được tổng hợp từ kết quả tìm kiếm
    """
    if not search_results or isinstance(search_results, dict) and "error" in search_results:
        return fallback_search(query)
    
   
    search_context = "\n\n".join([
        f"Tiêu đề: {result['title']}\nURL: {result['link']}\nMô tả: {result['snippet']}"
        for result in search_results
    ])
    
    prompt = f"""
    Dưới đây là một số kết quả tìm kiếm web cho câu hỏi: "{query}"
    
    {search_context}
    
    Dựa trên các kết quả tìm kiếm trên, hãy tạo một câu trả lời ngắn gọn, đầy đủ và chính xác.
    Bắt đầu câu trả lời bằng "Dựa trên kết quả tìm kiếm trên internet:".
    Không bao gồm URL trong câu trả lời.
    Nếu thông tin không rõ ràng hoặc không đủ, hãy nói thẳng thắn rằng bạn không có đủ thông tin.
    """
    
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(
            f"{gemini_api_url}?key={gemini_api_key}", 
            json=data, 
            headers=headers
        )
        response.raise_for_status()
        
        response_data = response.json()
        answer = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        
        if not answer.strip():
           
            return {
                "answer": "Dựa trên kết quả tìm kiếm trên internet: Tôi không thể tổng hợp được câu trả lời từ thông tin tìm được. Vui lòng thử lại với câu hỏi cụ thể hơn.",
                "web_sources": [result.get('link') for result in search_results if result.get('link')]
            }
        
        return {
            "answer": answer,
            "web_sources": [result.get('link') for result in search_results if result.get('link')]
        }
        
    except Exception as e:
        return {
            "answer": f"Dựa trên kết quả tìm kiếm trên internet: Tôi đã tìm thấy một số thông tin liên quan, nhưng không thể xử lý kết quả. Lỗi: {str(e)}",
            "web_sources": [result.get('link') for result in search_results if result.get('link')]
        }