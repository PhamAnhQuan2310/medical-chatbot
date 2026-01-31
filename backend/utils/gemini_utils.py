import requests

def get_gemini_response(user_input, prompt, api_url, api_key):
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(f"{api_url}?key={api_key}", json=data, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        candidates = response_data.get('candidates', [])
        if not candidates:
            return "No response from bot.", False
        content = candidates[0].get('content', {})
        parts = content.get('parts', [])
        if not parts or 'text' not in parts[0]:
            return "No response from bot.", False
        raw_response = parts[0]['text']
        cleaned_response = raw_response.replace("```sql", "").replace("```", "").strip()
        return cleaned_response, True
    except requests.RequestException as e:
        return f"Error calling Gemini API: {str(e)}", False