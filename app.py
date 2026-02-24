import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import json
import re

st.set_page_config(page_title="SEO Internal Linking SaaS", layout="wide")
st.title("⚡ Pro SEO Internal Linking Tool (V9 - The Final Fix)")

with st.sidebar:
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
    else:
        api_key = st.text_input("Enter Groq API Key", type="password")

sitemap_url = st.text_input("🌐 Paste Sitemap URL (e.g., [https://bioactors.online/post-sitemap.xml](https://bioactors.online/post-sitemap.xml))")
main_subject = st.text_input("🛑 Main Subject of this Article (e.g., Shah Rukh Khan) - We will strictly BLOCK this name!")
article_text = st.text_area("📝 Paste Your New Article Here", height=300)

if st.button("🚀 Generate Perfect Internal Links"):
    if not api_key or not sitemap_url or not article_text or not main_subject:
        st.error("Please fill all fields.")
    else:
        try:
            # 1. Sitemap Fetching (Ultimate Regex)
            st.info("Fetching Sitemap... Please wait.")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(sitemap_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                st.error(f"Server blocked the request. Status Code: {response.status_code}")
                st.stop()
            
            # Robust Regex to catch URLs even with line breaks or extra spaces in XML
            raw_urls = re.findall(r'<loc[^>]*>(.*?)</loc>', response.text, re.IGNORECASE | re.DOTALL)
            all_urls = [u.strip() for u in raw_urls if u.strip()]
            
            valid_urls_list = [u for u in all_urls if u.rstrip('/') != "[https://bioactors.online](https://bioactors.online)"]
            
            if not valid_urls_list:
                st.error(f"Sitemap properly fetched but 0 URLs extracted. Please verify if '{sitemap_url}' contains <loc> tags.")
                st.stop()
                
            st.success(f"Found {len(valid_urls_list)} specific pages. Fetching Meta Data...")
            
            # 2. Meta Data Fetching
            progress_bar = st.progress(0)
            enriched_data = ""
            max_urls = len(valid_urls_list)
            
            for i, url in enumerate(valid_urls_list):
                try:
                    page_resp = requests.get(url, headers=headers, timeout=5)
                    soup = BeautifulSoup(page_resp.content, 'html.parser')
                    title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"
                    
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    desc = meta_desc['content'].strip() if meta_desc and meta_desc.has_attr('content') else "No Description"
                    
                    enriched_data += f"URL: {url}\nTitle: {title}\nDescription: {desc}\n\n"
                except Exception:
                    enriched_data += f"URL: {url}\nTitle: Error\nDescription: Error\n\n"
                
                progress_bar.progress((i + 1) / max_urls)
                
            st.success("Meta Data Fetched! Groq AI is scanning for SECONDARY entities... 🧠")

            # 3. Groq AI Call
            client = Groq(api_key=api_key)
            
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
            {{
              "links": [
                {{
                  "Anchor Text": "Gauri Khan",
                  "Found Under Heading": "Personal Life",
                  "Target URL": "[https://bioactors.online/gauri-khan-biography/](https://bioactors.online/gauri-khan-biography/)",
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
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.1 # Low temperature for strict JSON formatting
            )
            
            # 4. JSON Cleaning and Parsing
            raw_response = chat_completion.choices[0].message.content.strip()
            
            if raw_response.startswith("```json"):
                raw_response = raw_response.split("```json")[1]
            if raw_response.startswith("```"):
                raw_response = raw_response.split("```")[1]
            if raw_response.endswith("```"):
                raw_response = raw_response.rsplit("```", 1)[0]
                
            raw_response = raw_response.strip()
            
            try:
                data = json.loads(raw_response)
                ai_links = data.get("links", [])
            except json.JSONDecodeError:
                st.error("AI returned malformed JSON. Please generate again.")
                st.stop()
            
            verified_links = []
            for link in ai_links:
                suggested_url = link.get("Target URL", "").strip()
                anchor_text = link.get("Anchor Text", "").strip()
                
                if main_subject.lower() in anchor_text.lower():
                    continue 
                
                if suggested_url in valid_urls_list:
                    verified_links.append(link)
            
            # 5. Display the Cleaned Results
            st.markdown("### 🎉 Verified SEO Internal Links:")
            if verified_links:
                st.table(verified_links)
            else:
                st.warning(f"⚠️ AI scanned everything and successfully ignored '{main_subject}'. However, no other exact matches (like co-stars/movies) were found in your sitemap.")

        except Exception as e:
            st.error(f"System Error: {str(e)}")
