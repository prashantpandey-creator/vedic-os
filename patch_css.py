import sys
import re

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# We need to replace the entire <style> block
pattern = re.compile(r"<style>.*?</style>", re.DOTALL)

glass_css = """<style>
    /* Glassmorphism Dark Theme */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Background - Deep sophisticated gradient */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        background-attachment: fixed;
        color: #e2e8f0;
    }

    /* Sidebar - Frosted Glass */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.4) !important;
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Headers and Topbar */
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* Inputs, TextAreas, SelectBoxes - Glassy */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>div {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #e2e8f0 !important;
        border-radius: 12px !important;
        transition: all 0.3s ease;
    }

    .stTextInput>div>div>input:focus, 
    .stTextArea>div>div>textarea:focus,
    .stSelectbox>div>div>div:focus {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(99, 102, 241, 0.5) !important;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.2) !important;
    }

    /* Chat inputs */
    .stChatInputContainer {
        background-color: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
    }
    
    /* Info boxes and Warnings - Glassy variants */
    .stAlert {
        background-color: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
    }

    /* Buttons - Sleek Glowing */
    .stButton>button {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px);
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: rgba(99, 102, 241, 0.2) !important;
        border-color: rgba(99, 102, 241, 0.5) !important;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(99, 102, 241, 0.2);
    }
    .stButton>button:active {
        transform: translateY(0px);
    }
    
    /* Primary buttons */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.6) 0%, rgba(139, 92, 246, 0.6) 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    .stButton>button[kind="primary"]:hover {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.8) 0%, rgba(139, 92, 246, 0.8) 100%) !important;
        box-shadow: 0 5px 20px rgba(139, 92, 246, 0.4);
    }

    /* Containers and Expanders - Glass Cards */
    [data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }
    [data-testid="stExpander"] > div[role="button"] {
        background-color: rgba(255, 255, 255, 0.02) !important;
    }

    /* Code blocks */
    pre {
        background-color: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(5px);
    }

    /* Model Cards (Custom class) */
    .model-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 15px; 
        margin-bottom: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.3s ease;
    }
    .model-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.3);
    }
    .model-title { color: #818cf8; font-weight: 600; font-size: 1.1em; }
    .model-stat { color: #94a3b8; font-size: 0.9em; }
    .status-active { color: #4ade80; font-weight: 600; }

    /* Tabs Styling - Minimal Pill design */
    [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(0, 0, 0, 0.2);
        padding: 6px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 10px !important;
        border: none !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* Hide annoying UI elements */
    .stDeployButton {display:none;}
    footer {visibility: hidden;}

    /* Custom scrollbars */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: rgba(0,0,0,0.1); }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
</style>"""

if pattern.search(content):
    content = pattern.sub(glass_css, content)
    with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
        f.write(content)
    print("Glassmorphism CSS injected.")
else:
    print("Could not find <style> block.")
