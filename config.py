import os
import json

class Config:
    # გარემოს ცვლადები
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    NGROK_URL = "https://bot.futurium.ge"
    HANDLER_URL = f"{NGROK_URL}/webhook"
    
    # ფაილების სახელები
    CONFIG_FILE = "appsConfig.json"
    INFO_FILE = "company_info.txt"
    DB_NAME = "bot_memory.db"
    
    # ბოტის პარამეტრები
    BOT_CODE = "Gemini_ITR_Final-20"
    
    # რეგისტრაციის მონაცემები
    REG_PARAMS = {
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

class ConfigManager:
    @staticmethod
    def load_company_info():
        if not os.path.exists(Config.INFO_FILE):
            return "შენ ხარ დამხმარე AI ასისტენტი."
        try:
            with open(Config.INFO_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"❌ Read Error {Config.INFO_FILE}: {e}")
            return "შენ ხარ დამხმარე AI ასისტენტი."

    @staticmethod
    def load_apps_config():
        if not os.path.exists(Config.CONFIG_FILE):
            return {}
        try:
            with open(Config.CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    @staticmethod
    def save_apps_config(config_data):
        with open(Config.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def update_mapping(app_sid, domain, bot_id, auth_data):
        config = ConfigManager.load_apps_config()
        changed = False
        if app_sid:
            config[str(app_sid)] = {"BOT_ID": str(bot_id), "AUTH": auth_data}
            changed = True
        if domain:
            config[str(domain)] = {"BOT_ID": str(bot_id), "AUTH": auth_data}
            changed = True
        if changed:
            ConfigManager.save_apps_config(config)
