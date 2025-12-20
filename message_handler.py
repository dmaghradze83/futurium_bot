from config import Config, ConfigManager
from bitrix_client import BitrixClient
import utils

def handle_incoming_message(data, incoming_auth, ai_engine):
    """ამუშავებს შემოსულ მესიჯს"""
    
    apps_config = ConfigManager.load_apps_config()
    
    message = data.get("data[PARAMS][MESSAGE]")
    chat_id = data.get("data[PARAMS][DIALOG_ID]")
    author_id = utils.extract_author_id(data)
    
    domain = incoming_auth['domain']
    app_sid = incoming_auth['application_token']
    access_token = incoming_auth['access_token']

    # --- 1. სწორი ავტორიზაციის და BOT_ID-ის პოვნა ---
    auth_for_work = None
    bot_id = None
    
    # ა) ვეძებთ კონფიგში
    if domain and domain in apps_config:
        bot_id = apps_config[domain].get("BOT_ID")
    elif app_sid and app_sid in apps_config:
        bot_id = apps_config[app_sid].get("BOT_ID")

    # ბ) თუ ახალი ტოკენი მოვიდა, ვაახლებთ!
    if access_token:
        auth_for_work = incoming_auth
        if bot_id:
            ConfigManager.update_mapping(app_sid, domain, bot_id, auth_for_work)
            print("♻️ Token updated from request.")
    else:
        # თუ არ მოვიდა, ვიღებთ ძველს
        if domain and domain in apps_config:
            auth_for_work = apps_config[domain]["AUTH"]
        else:
            auth_for_work = utils.get_auth_from_request(data)

    # გ) თუ BOT_ID ჯერ კიდევ არ გვაქვს, ვკითხულობთ API-დან
    if not bot_id:
        found = BitrixClient.resolve_bot_id(auth_for_work, Config.BOT_CODE)
        if found:
            bot_id = str(found)
            ConfigManager.update_mapping(app_sid, domain, bot_id, auth_for_work)

    # --- 2. Loop Protection ---
    # თუ მესიჯის ავტორი თავად ბოტია, ვაიგნორებთ
    if bot_id and author_id and str(author_id) == str(bot_id):
        return "OK"

    # --- 3. ბოტის პასუხის ლოგიკა ---
    if message and chat_id:
        print(f"\n📩 Incoming: {message}")
        _process_commands(chat_id, message, auth_for_work, bot_id, ai_engine)

    return "OK"

def _process_commands(chat_id, message, auth_data, bot_id, ai_engine):
    """შიდა ფუნქცია ბრძანებების დასამუშავებლად"""
    msg_lower = (message or "").strip().lower()

    # მენიუ
    if msg_lower in ("0", "help", "/start"):
        text = "გამარჯობა! მე ვარ AI ასისტენტი. 🤖\n1 - ოპერატორი\n9 - დასრულება"
        BitrixClient.send_message(chat_id, text, auth_data, bot_id)

    # ოპერატორთან გადართვა
#     elif msg_lower == "1" or "ოპერატორ" in msg_lower:
#        BitrixClient.send_message(chat_id, "გადამყავს ოპერატორთან...", auth_data, bot_id)
#       BitrixClient.call("imopenlines.bot.session.transfer",
#          {"CHAT_ID": str(chat_id).replace("chat", ""), "LEAVE": "Y"}, auth_data)

    # საუბრის დასრულება
    elif msg_lower == "9" or "დასრულება" in msg_lower:
        BitrixClient.send_message(chat_id, "ნახვამდის!", auth_data, bot_id)
        BitrixClient.call("imopenlines.bot.session.finish",
            {"CHAT_ID": str(chat_id).replace("chat", "")}, auth_data)

    # AI პასუხი
    else:
        ai_text = ai_engine.get_response(chat_id, message)
        print(f"🤖 AI Answer: {ai_text[:50]}...")
        BitrixClient.send_message(chat_id, ai_text, auth_data, bot_id)
