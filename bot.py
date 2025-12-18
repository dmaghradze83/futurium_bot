import os
import json
from flask import Flask, request
import requests
import google.generativeai as genai

app = Flask(__name__)

# ==========================================
# ⚙️ CONFIG
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDstHwPMVBZTeYIlzPgRqw_LocgJHT7m9s")
NGROK_URL = "https://bot.futurium.ge"
HANDLER_URL = f"{NGROK_URL}/webhook"
CONFIG_FILE = "appsConfig.json"
INFO_FILE = "company_info.txt"  # 👈 ახალი ფაილი

BOT_CODE = "Gemini_ITR_Final-20" 

genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# 📂 INFO FILE LOADER (ახალი ფუნქცია)
# ==========================================
def load_company_info():
    """კითხულობს კომპანიის ინფორმაციას txt ფაილიდან"""
    if not os.path.exists(INFO_FILE):
        return "შენ ხარ დამხმარე AI ასისტენტი." # თუ ფაილი არ დახვდა, ეს იქნება დეფოლტი
    
    try:
        with open(INFO_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"❌ ვერ წავიკითხე {INFO_FILE}: {e}")
        return "შენ ხარ დამხმარე AI ასისტენტი."

# ==========================================
# 🧠 AI
# ==========================================
def get_ai_response(message: str) -> str:
    if not GEMINI_API_KEY:
        return "ბოდიში, AI არ მუშაობს (GEMINI_API_KEY ცარიელია)."

    # 👇 აქ ვკითხულობთ ფაილს ყოველ ჯერზე (რომ კოდის გადატვირთვა არ დაგჭირდეს ტექსტის შეცვლისას)
    system_instruction = load_company_info()
    
    # ვაერთიანებთ ინსტრუქციას და კლიენტის მესიჯს
    full_prompt = f"{system_instruction}\n\nმომხმარებლის მესიჯი: {message}"

    try:
        model = genai.GenerativeModel("gemini-2.5-flash") # 1.5 უფრო სტაბილურია
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e1:
        print(f"❌ Gemini error (1.5-flash): {e1}")
        try:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e2:
            print(f"❌ Gemini error (gemini-pro): {e2}")
            return "ბოდიში, AI დროებით მიუწვდომელია."

# ==========================================
# 📂 CONFIG I/O
# ==========================================
def load_params():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_params(config_data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)

# ==========================================
# 🔌 Bitrix REST helper
# ==========================================
def rest_command(method, params, auth_data):
    domain = auth_data.get("domain")
    if not domain and auth_data.get("client_endpoint"):
        domain = (
            auth_data["client_endpoint"]
            .split("/rest")[0]
            .replace("https://", "")
            .replace("http://", "")
        )

    if not domain:
        return {}

    url = f"https://{domain}/rest/{method}"
    params = dict(params or {})
    params["auth"] = auth_data.get("access_token")

    try:
        response = requests.post(url, data=params, timeout=25)
        return response.json()
    except Exception as e:
        print(f"❌ REST connection error: {e}")
        return {}

# ==========================================
# ✅ Helpers
# ==========================================
def extract_app_sid(data):
    return (
        data.get("auth[application_token]")
        or data.get("APP_SID")
        or data.get("app_sid")
        or data.get("auth[APP_SID]")
        or data.get("AUTH_APP_SID")
    )

def extract_author_id(data):
    return (
        data.get("data[PARAMS][AUTHOR_ID]")
        or data.get("data[PARAMS][FROM_USER_ID]")
        or data.get("data[MESSAGE][AUTHOR_ID]")
        or data.get("data[MESSAGE][FROM_USER_ID]")
    )

def extract_domain(data):
    return data.get("auth[domain]") or data.get("DOMAIN")

def get_auth_from_request(data):
    return {
        "access_token": data.get("auth[access_token]") or data.get("AUTH_ID"),
        "domain": extract_domain(data),
        "application_token": extract_app_sid(data),
        "client_endpoint": data.get("auth[client_endpoint]"),
    }

# ==========================================
# ✅ BOT_ID finder
# ==========================================
def resolve_bot_id_by_code(auth_data, bot_code: str):
    result = rest_command("imbot.bot.list", {}, auth_data)
    raw = result.get("result")

    # 1) list
    if isinstance(raw, list):
        if raw and isinstance(raw[0], dict):
            for b in raw:
                code = b.get("CODE") or b.get("code")
                if str(code) == str(bot_code):
                    return b.get("ID") or b.get("BOT_ID") or b.get("id")
            return None

        ids = [str(x) for x in raw if isinstance(x, (str, int))]
        if len(ids) == 1:
            return ids[0]
        return None

    # 2) dict mapping
    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, dict):
                code = v.get("CODE") or v.get("code")
                if str(code) == str(bot_code):
                    return v.get("ID") or v.get("BOT_ID") or k
        return None

    # 3) raw is str/int
    if isinstance(raw, (str, int)):
        return str(raw)

    return None

def save_mapping(apps_config, app_sid, domain, bot_id, auth_data):
    changed = False
    if app_sid:
        apps_config[str(app_sid)] = {"BOT_ID": str(bot_id), "AUTH": auth_data}
        changed = True
    if domain:
        apps_config[str(domain)] = {"BOT_ID": str(bot_id), "AUTH": auth_data}
        changed = True
    if changed:
        save_params(apps_config)

# ==========================================
# 🚀 MAIN WEBHOOK
# ==========================================
# ==========================================
# 🚀 MAIN WEBHOOK (განახლებული ლოგიკა)
# ==========================================
@app.route("/webhook", methods=["POST"])
def main_handler():
    data = request.values
    event = data.get("event")
    apps_config = load_params()

    # ------------------------------
    # 1) INSTALL / UPDATE
    # ------------------------------
    access_token = data.get("auth[access_token]") or data.get("AUTH_ID")
    app_sid = extract_app_sid(data)
    domain = extract_domain(data)

    # შემოსული ახალი მონაცემები
    incoming_auth = {
        "access_token": access_token,
        "domain": domain,
        "application_token": app_sid,
        "client_endpoint": data.get("auth[client_endpoint]"),
    }

    should_register = (event == "ONAPPINSTALL") or ("AUTH_ID" in data) or ("APP_SID" in data)
    
    # თუ ინსტალაციაა, ვარეგისტრირებთ
    if should_register and access_token:
        print(f"\n🔔 Install/Update detected... domain={domain} app_sid={app_sid}")
        
        reg_params = {
            "CODE": BOT_CODE,
            "TYPE": "B",
            "EVENT_HANDLER": HANDLER_URL,
            "EVENT_MESSAGE_ADD": HANDLER_URL,
            "EVENT_WELCOME_MESSAGE": HANDLER_URL,
            "EVENT_BOT_DELETE": HANDLER_URL,
            "OPENLINE": "Y",
            "PROPERTIES[NAME]": "Gemini AI (Final)-20",
            "PROPERTIES[WORK_POSITION]": "AI Assistant 20",
            "PROPERTIES[COLOR]": "AQUA",
        }

        result = rest_command("imbot.register", reg_params, incoming_auth)

        finish_html = """<!DOCTYPE html><html><head>
        <script src="//api.bitrix24.com/api/v1/"></script>
        <script>BX24.init(function(){BX24.installFinish();});</script>
        </head><body>INSTALLED</body></html>"""

        if "result" in result:
            bot_id = result["result"]
            print(f"✅ Bot registered! BOT_ID={bot_id}")
            rest_command("event.bind", {"EVENT": "OnAppUpdate", "HANDLER": HANDLER_URL}, incoming_auth)
            save_mapping(apps_config, app_sid, domain, bot_id, incoming_auth)
            return finish_html

        print(f"❌ imbot.register failed: {result}")
        return finish_html

    # ------------------------------
    # 2) MESSAGE
    # ------------------------------
    if event == "ONIMBOTMESSAGEADD":
        message = data.get("data[PARAMS][MESSAGE]")
        chat_id = data.get("data[PARAMS][DIALOG_ID]")
        
        # მონაცემების ამოღება
        domain = extract_domain(data)
        current_app_sid = extract_app_sid(data)
        author_id = extract_author_id(data)
        
        # 🔑 მთავარი ცვლილება: 
        # თუ შემოსულ სიგნალს მოყვა ახალი ტოკენი, ვიყენებთ მას და ვაახლებთ ფაილს!
        auth_for_work = None
        bot_id = None
        
        # ვეძებთ BOT_ID-ს კონფიგურაციაში
        if domain and domain in apps_config:
            bot_id = apps_config[domain].get("BOT_ID")
        elif current_app_sid and current_app_sid in apps_config:
            bot_id = apps_config[current_app_sid].get("BOT_ID")

        # ავტორიზაციის არჩევა: 
        # თუ ახალი ტოკენი მოვიდა (access_token), ვიყენებთ მას.
        # თუ არ მოვიდა, ვიყენებთ ძველს ფაილიდან.
        if access_token:
            auth_for_work = incoming_auth
            # თან ვინახავთ განახლებულ ტოკენს მომავლისთვის
            if bot_id:
                save_mapping(apps_config, current_app_sid, domain, bot_id, auth_for_work)
                print("♻️ ტოკენი განახლდა შემოსული მესიჯიდან.")
        else:
            # თუ ტოკენი არ მოყვა მესიჯს, ვიღებთ ფაილიდან
            if domain and domain in apps_config:
                auth_for_work = apps_config[domain]["AUTH"]
            elif current_app_sid and current_app_sid in apps_config:
                auth_for_work = apps_config[current_app_sid]["AUTH"]
            else:
                auth_for_work = get_auth_from_request(data) # Fallback

        # Fallback BOT_ID-სთვის
        if not bot_id:
            found = resolve_bot_id_by_code(auth_for_work, BOT_CODE)
            if found:
                bot_id = str(found)
                save_mapping(apps_config, current_app_sid, domain, bot_id, auth_for_work)

        # Loop guard
        if bot_id and author_id and str(author_id) == str(bot_id):
            return "OK", 200

        print(f"\n📩 Incoming: msg={message}")

        if message and chat_id:
            process_bot_logic(chat_id, message, auth_for_work, bot_id)

        return "OK", 200

    return "OK", 200

# ==========================================
# 🤖 BOT LOGIC
# ==========================================
def process_bot_logic(chat_id, message, auth_data, bot_id):
    msg_lower = (message or "").strip().lower()

    if msg_lower in ("0", "help", "/start"):
        text = "გამარჯობა! მე ვარ AI ასისტენტი. 🤖\n1 - ოპერატორი\n9 - დასრულება"
        send_message(chat_id, text, auth_data, bot_id)

    elif msg_lower == "1" or "ოპერატორ" in msg_lower:
        send_message(chat_id, "გადამყავს ოპერატორთან...", auth_data, bot_id)
        rest_command(
            "imopenlines.bot.session.transfer",
            {"CHAT_ID": str(chat_id).replace("chat", ""), "LEAVE": "Y"},
            auth_data,
        )

    elif msg_lower == "9" or "დასრულება" in msg_lower:
        send_message(chat_id, "ნახვამდის!", auth_data, bot_id)
        rest_command(
            "imopenlines.bot.session.finish",
            {"CHAT_ID": str(chat_id).replace("chat", "")},
            auth_data,
        )

    else:
        ai_text = get_ai_response(message)
        print(f"🤖 AI Answer: {ai_text[:120]}...")
        send_message(chat_id, ai_text, auth_data, bot_id)

# ==========================================
# 📤 SEND MESSAGE
# ==========================================
def send_message(chat_id, text, auth_data, bot_id):
    dialog_id = str(chat_id)

    if not bot_id:
        print("🛑 BOT_ID არ მაქვს -> არ ვაგზავნი პასუხს.")
        return

    params = {
        "BOT_ID": str(bot_id),
        "DIALOG_ID": dialog_id,
        "MESSAGE": text
    }

    result = rest_command("imbot.message.add", params, auth_data)

    if "result" in result:
        print("✅ Sent successfully!")
    else:
        print(f"📬 Bitrix Error: {result}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
