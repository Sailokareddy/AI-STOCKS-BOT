from pathlib import Path
import shutil
import sys

app = Path("app.py")

if not app.exists():
    print("ERROR: app.py was not found.")
    print(r"C:\Users\lokar\Downloads\AI_Stock_Bot_V3_Gmail_OAuth")
    sys.exit(1)

text = app.read_text(encoding="utf-8")
start_marker = "# 3D ROBOT / UI"
end_marker = "# PAGE"
start = text.find(start_marker)
end = text.find(end_marker, start + len(start_marker))

if start == -1 or end == -1:
    print("ERROR: UI section markers were not found.")
    sys.exit(1)

backup = app.with_name("app_before_ui_repair.py")
shutil.copy2(app, backup)

replacement = '# 3D ROBOT / UI\n# ============================================================\n\nst.markdown("""\n<style>\n.stApp {\n    background: linear-gradient(135deg, #070a12, #0b1020 50%, #070a12);\n}\n.ai-hero {\n    padding: 30px;\n    margin-bottom: 20px;\n    border: 1px solid rgba(130,180,255,.25);\n    border-radius: 24px;\n    background: linear-gradient(135deg, rgba(24,32,58,.96), rgba(11,16,30,.92));\n    box-shadow: 0 24px 70px rgba(0,0,0,.38);\n}\n.ai-kicker {\n    color: #78b7ff;\n    font-size: .82rem;\n    letter-spacing: .18em;\n    text-transform: uppercase;\n}\n.ai-title {\n    font-size: 2.6rem;\n    font-weight: 800;\n    margin: 8px 0;\n}\n.ai-subtitle {\n    color: #b9c4d8;\n    font-size: 1.05rem;\n}\n</style>\n<div class="ai-hero">\n    <div class="ai-kicker">REAL-TIME INDIAN MARKET INTELLIGENCE</div>\n    <div class="ai-title">🤖 AI Stock Bot</div>\n    <div class="ai-subtitle">NIFTY 50 • SENSEX • Your Stocks • 5-Minute Alerts • Gmail Reports</div>\n</div>\n""", unsafe_allow_html=True)\n\n'
app.write_text(text[:start] + replacement + text[end:], encoding="utf-8")

print("UI section repaired successfully.")
print("Backup:", backup.name)
print("Now run: python -m py_compile app.py")
