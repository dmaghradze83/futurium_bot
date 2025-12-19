from config import Config, ConfigManager
from bitrix_client import BitrixClient

def handle_install(data, incoming_auth):
    """ამუშავებს ინსტალაციის ივენთს"""
    
    app_sid = incoming_auth['application_token']
    domain = incoming_auth['domain']

    print(f"\n🔔 Install/Update detected... domain={domain}")
    
    # 1. რეგისტრაციის მოთხოვნა Bitrix-თან
    result = BitrixClient.call("imbot.register", Config.REG_PARAMS, incoming_auth)

    # HTML პასუხი, რასაც Bitrix ელოდება iframe-ში
    finish_html = """<!DOCTYPE html><html><head>
    <script src="//api.bitrix24.com/api/v1/"></script>
    <script>BX24.init(function(){BX24.installFinish();});</script>
    </head><body>INSTALLED</body></html>"""

    if "result" in result:
        bot_id = result["result"]
        print(f"✅ Bot registered! BOT_ID={bot_id}")
        
        # 2. ივენთის მიბმა განახლებაზე
        BitrixClient.call("event.bind", {"EVENT": "OnAppUpdate", "HANDLER": Config.HANDLER_URL}, incoming_auth)
        
        # 3. მონაცემების შენახვა config ფაილში
        ConfigManager.update_mapping(app_sid, domain, bot_id, incoming_auth)
        return finish_html
    
    print(f"❌ imbot.register failed: {result}")
    return finish_html
