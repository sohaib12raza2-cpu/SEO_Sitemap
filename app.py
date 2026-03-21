import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import google.generativeai as genai
import json

# App Ka Title Aur Layout
st.set_page_config(page_title="SEO Internal Linking SaaS", layout="wide")
st.title("⚡ Pro SEO Internal Linking Tool (V10 - Bulletproof Fetcher)")

# Sidebar for API Key
with st.sidebar:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Enter Gemini API Key", type="password")

# Main Input Fields
st.warning("💡 Tip: Use your EXACT post sitemap (e.g., https://bioactors.online/post-sitemap.xml) not the main index.")
sitemap_url = st.text_input("🌐 Paste Sitemap URL")
main_subject = st.text_input("🛑 Main Subject of this Article (e.g., Shah Rukh Khan) - We will strictly BLOCK this name!")
article_text = st.text_area("📝 Paste Your New Article Here", height=300)

if st.button("🚀 Generate Perfect Internal Links"):
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar settings first.")
    elif not sitemap_url or not article_text or not main_subject:
        st.error("Please provide the Sitemap URL, the Main Subject, and the Article text.")
    else:
        # 1. Sitemap Fetching (UPGRADED TO BYPASS BLOCKS)
        st.info("Fetching Sitemap... Please wait.")
        
        # Adding real browser headers so your server doesn't block it as a bot
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/xml, text/xml, */*; q=0.01'
        }
        
        try:
            response = requests.get(sitemap_url, headers=headers, timeout=10)
            
            # Check if server blocked us
            if response.status_code != 200:
                st.error(f"🚨 Server Blocked the Request! Status Code: {response.status_code}. Your hosting or security plugin is blocking this tool.")
            else:
                # Use Regex to extract links (never fails unlike HTML parsers)
                all_urls = re.findall(r'<loc>(.*?)</loc>', response.text)
                
                # Filter out the main domain and other .xml sitemaps
                valid_urls_list = [u for u in all_urls if u.strip('/') != "https://bioactors.online" and ".xml" not in u.split('/')[-1]]
                
                if len(valid_urls_list) == 0:
                    st.error("🚨 Found 0 articles! Please make sure you pasted the exact 'post-sitemap.xml' link and not the main index. Open the link in your browser to verify it contains URLs.")
                else:
                    st.success(f"Found {len(valid_urls_list)} specific article pages. Fetching Meta Data...")
                    
                    # 2. Meta Data Fetching
                    progress_bar = st.progress(0)
                    enriched_data = ""
                    max_urls = len(valid_urls_list)
                    
                    for i in range(max_urls):
                        url = valid_urls_list[i]
                        try:
                            page_resp = requests.get(url, headers=headers, timeout=5)
                            soup = BeautifulSoup(page_resp.content, 'html.parser')
                            title = soup.title.string if soup.title else "No Title"
                            
                            meta_desc = soup.find('meta', attrs={'name': 'description'})
                            desc = meta_desc['content'] if meta_desc else "No Description"
                            
                            enriched_data += f"URL: {url}\nTitle: {title}\nDescription: {desc}\n\n"
                        except:
                            enriched_data += f"URL: {url}\nTitle: Error\nDescription: Error\n\n"
                        
                        progress_bar.progress((i + 1) / max_urls)
                        
                    st.success("Meta Data Fetched! Gemini AI is scanning for SECONDARY entities... 🧠")

                    # 3. GEMINI AI CALL
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(
                        'gemini-2.5-flash',
                        generation_config={"response_mime_type": "application/json"}
                    )
                    
                    prompt = f"""
                    You are an SEO Internal Linking API. Your job is to find EXACT entity matches between the [AVAILABLE EXISTING PAGES] and the [NEW ARTICLE].

                    🚨 CRITICAL RULE (ANTI-SELF-LINKING):
                    The main subject of this article is '{main_subject}'. YOU ARE STRICTLY FORBIDDEN from creating any link where the Anchor Text is '{main_subject}'. 
                    You MUST actively scan the article for SECONDARY entities (co-stars, spouses, directors, specific movies) that match the available pages.

                    RULES:
                    1. Only link if there is a 100% undeniable match for a SECONDARY entity (e.g., Gauri Khan).
                    2. The "Target URL" MUST be an exact copy-paste from the provided sitemap list.

                    OUTPUT FORMAT:
                    You must respond ONLY with a valid JSON object. Do NOT include markdown formatting or any other text.
                    Example:
                    {{
                      "links": [
                        {{
                          "Anchor Text": "Gauri Khan",
                          "Found Under Heading": "Personal Life",
                          "Target URL": "https://bioactors.online/gauri-khan-biography/",
                          "Relationship Reason": "Wife of Shah Rukh Khan."
                        }}
                      ]
                    }}

                    If no exact secondary matches are found, return {{"links": []}}

                    [AVAILABLE EXISTING PAGES (SITEMAP DATA)]
                    {enriched_data}

                    [NEW ARTICLE]
                    {article_text}
                    """
                    
                    gemini_response = model.generate_content(prompt)
                    
                    # 4. PYTHON GUARDRAILS (The Ultimate Kill-Switch)
                    raw_response = gemini_response.text.strip()
                    
                    if "```json" in raw_response:
                        raw_response = raw_response.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw_response:
                        raw_response = raw_response.split("```")[1].split("```")[0].strip()
                        
                    data = json.loads(raw_response)
                    ai_links = data.get("links", [])
                    
                    verified_links = []
                    for link in ai_links:
                        suggested_url = link.get("Target URL", "").strip()
                        anchor_text = link.get("Anchor Text", "").strip()
                        
                        if main_subject.lower() in anchor_text.lower():
                            continue 
                        
                        if suggested_url in valid_urls_list:
                            verified_links.append(link)
                    
                    # 5. Display the Cleaned Results
                    st.markdown("### 🎉 Verified SEO Internal Links (Gemini Powered):")
                    if verified_links:
                        st.table(verified_links)
                    else:
                        st.warning(f"⚠️ AI scanned everything and successfully ignored '{main_subject}'. However, no other exact matches (like co-stars/movies) were found in your sitemap.")

        except Exception as e:
            st.error(f"System Error: {e}")

# --- ADDING EMPTY SPACE AT THE BOTTOM SO RESULTS DON'T GET CUT ---
st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
