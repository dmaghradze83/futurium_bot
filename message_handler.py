from config import Config, ConfigManager
from bitrix_client import BitrixClient
import utils

def handle_incoming_message(data, incoming_auth, ai_engine):
    """ამუშავებს შემოსულ მესიჯს მთლიანად AI-ზე დაყრდნობით"""
    
    apps_config = ConfigManager.load_apps_config()
    
    message = data.get("data[PARAMS][MESSAGE]")
    chat_id = data.get("data[PARAMS][DIALOG_ID]")
    author_id = utils.extract_author_id(data)
    
    domain = incoming_auth['domain']
    app_sid = incoming_auth['application_token']
    access_token = incoming_auth['access_token']

    # --- 1. ავტორიზაცია ---
    auth_for_work = None
    bot_id = None
    
    if domain and domain in apps_config:
        bot_id = apps_config[domain].get("BOT_ID")
    elif app_sid and app_sid in apps_config:
        bot_id = apps_config[app_sid].get("BOT_ID")

    if access_token:
        auth_for_work = incoming_auth
        if bot_id:
            ConfigManager.update_mapping(app_sid, domain, bot_id, auth_for_work)
            print("♻️ Token updated from request.")

    else:
        if domain and domain in apps_config:
            auth_for_work = apps_config[domain]["AUTH"]
        else:
            auth_for_work = utils.get_auth_from_request(data)

    if not bot_id:
        found = BitrixClient.resolve_bot_id(auth_for_work, Config.BOT_CODE)
        if found:
            bot_id = str(found)
            ConfigManager.update_mapping(app_sid, domain, bot_id, auth_for_work)

    # --- 2. Loop Protection ---
    if bot_id and author_id and str(author_id) == str(bot_id):
        return "OK"

    # --- 3. ლოგიკა ---
    if message and chat_id:
        print(f"\n📩 Incoming: {message}")
        _process_with_ai_logic(chat_id, message, auth_for_work, bot_id, ai_engine)

    return "OK"

def _process_with_ai_logic(chat_id, message, auth_data, bot_id, ai_engine):
    """
    ყველაფერს ვუგზავნით AI-ს და მისი პასუხის მიხედვით ვმოქმედებთ.
    """
    
    # 1. მივიღოთ პასუხი AI-სგან
    ai_text = ai_engine.get_response(chat_id, message)
    
    # 2. ვამოწმებთ, AI-მ ხომ არ გვითხრა "გადართეო" (TRANSFER_AGENT)
    if "TRANSFER_AGENT" in ai_text:
        print(f"🤖 AI Logic: მომხმარებელმა მოითხოვა ოპერატორი. (AI Output: {ai_text})")
        transfer_to_agent(chat_id, auth_data, bot_id)
        return

    # 3. თუ გადართვა არაა, უბრალოდ ვუგზავნით AI-ს პასუხს კლიენტს
    print(f"🤖 AI Answer: {ai_text[:50]}...")
    BitrixClient.send_message(chat_id, ai_text, auth_data, bot_id)


def transfer_to_agent(chat_id, auth_data, bot_id):
    """გადართავს საუბარს რიგში მდგომ ოპერატორთან"""
    
    # 1. შეტყობინება
    BitrixClient.send_message(chat_id, "მიმდინარეობს გაყიდვების მენეჯერთან გადართვა... ⏳", auth_data, bot_id)
    
    # 2. გადართვა
    # ვრწმუნდებით, რომ ID სუფთა სტრინგია
    real_chat_id = str(chat_id).replace("chat", "")
    
    BitrixClient.call("imopenlines.bot.session.transfer",
        {
            "CHAT_ID": real_chat_id, 
            "LEAVE": "Y"
        }, 
        auth_data
    )