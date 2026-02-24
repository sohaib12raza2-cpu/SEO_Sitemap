import streamlit as st
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from groq import Groq
import json

# App Ka Title Aur Layout
st.set_page_config(page_title="SEO Internal Linking SaaS", layout="wide")
st.title("⚡ Pro SEO Internal Linking Tool (V8 - Ultimate Context Shield)")

# Sidebar for API Key
with st.sidebar:
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
    else:
        api_key = st.text_input("Enter Groq API Key", type="password")

# Main Input Fields
sitemap_url = st.text_input("🌐 Paste Sitemap URL (e.g., https://bioactors.online/sitemap.xml)")
# NAYA FIELD: Anti-Self-Link Kill Switch
main_subject = st.text_input("🛑 Main Subject of this Article (e.g., Shah Rukh Khan) - We will strictly BLOCK this name!")
article_text = st.text_area("📝 Paste Your New Article Here", height=300)

if st.button("🚀 Generate Perfect Internal Links"):
    if not api_key:
        st.error("Please enter your Groq API Key in the sidebar settings first.")
    elif not sitemap_url or not article_text or not main_subject:
        st.error("Please provide the Sitemap URL, the Main Subject, and the Article text.")
    else:
        try:
            # 1. Sitemap Fetching
            st.info("Fetching Sitemap... Please wait.")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(sitemap_url, headers=headers)
            soup_xml = BeautifulSoup(response.content, 'xml')
            all_urls = [loc.text for loc in soup_xml.find_all('loc')]
            
            valid_urls_list = [u for u in all_urls if u.strip('/') != "https://bioactors.online"]
                
            st.success(f"Found {len(valid_urls_list)} specific pages. Fetching Meta Data...")
            
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
                
            st.success("Meta Data Fetched! Groq AI is scanning for SECONDARY entities... 🧠")

            # 3. Groq AI Call (Strict Focus on Secondary Entities)
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
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            
            # 4. PYTHON GUARDRAILS (The Ultimate Kill-Switch)
            raw_response = chat_completion.choices[0].message.content.strip()
            
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
                
                # THE KILL SWITCH: If AI still tries to link the main subject, Python will delete it!
                if main_subject.lower() in anchor_text.lower():
                    continue # Skip this loop, block the link
                
                # Check if URL is real
                if suggested_url in valid_urls_list:
                    verified_links.append(link)
            
            # 5. Display the Cleaned Results
            st.markdown("### 🎉 Verified SEO Internal Links:")
            if verified_links:
                st.table(verified_links)
            else:
                st.warning(f"⚠️ AI scanned everything and successfully ignored '{main_subject}'. However, no other exact matches (like co-stars/movies) were found in your sitemap.")

        except Exception as e:
            st.error(f"Error parsing AI output: {e}")
            # st.write("Raw AI Output was:", chat_completion.choices[0].message.content)
