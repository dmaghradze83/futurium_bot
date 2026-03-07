from config import Config, ConfigManager, json
from bitrix_client import BitrixClient

def handle_install(data, incoming_auth):
    """ამუშავებს ინსტალაციის ივენთს"""

    app_sid = incoming_auth['application_token']
    domain = incoming_auth['domain']

    print(f"\n🔔 Install/Update detected... domain={domain}")

    # 1. რეგისტრაციის მოთხოვნა Bitrix-თან
    result = BitrixClient.call("imbot.register", Config.REG_PARAMS, incoming_auth)

    # CoPilot-ის ტექსტის გენერატორის (Gemini) პარამეტრები

    #ai_engine_settings = {
    #    "code_alias": "gemini_pro_geo",
    #    "model_context_type": "token",
    #    "model_context_limit": 16384
    #}

    #ai_engine_params = {
    #    "name": "Gemini (Georgian)",
    #    "code": "gemini_pro_geo",
    #    "category": "text",
    #    "completions_url": f"{Config.NGROK_URL}/api/ai/completions",
    #    "settings": json.dumps(ai_engine_settings, ensure_ascii=False)
    #}

    # AI ძრავის რეგისტრაციის მოთხოვნა
    # ai_result = BitrixClient.call("ai.engine.register", ai_engine_params, incoming_auth)
    # print(f"🧠 AI Engine registration: {ai_result}")

    # HTML პასუხი, რასაც Bitrix ელოდება iframe-ში
    # finish_html = """<!DOCTYPE html><html><head>
    # <script src="//api.bitrix24.com/api/v1/"></script>
    # <script>BX24.init(function(){BX24.installFinish();});</script>
    # </head><body>INSTALLED</body></html>"""

    finish_html = f"""<!DOCTYPE html>
    <html>
    <head>
    <script src="//api.bitrix24.com/api/v1/"></script>
    <script>
    BX24.init(function() {{
    
        BX24.callMethod(
            'ai.engine.register',
            {{
                name: 'Gemini (Georgian)',
                code: 'gemini_pro_geo',
                category: 'text',
                completions_url: 'https://bot.futurium.ge/api/ai/completions',
                settings: {{
                    code_alias: 'gemini_pro_geo',
                    model_context_type: 'token',
                    model_context_limit: 16 * 1024
                }}
            }},
            function(result) {{
                if (result.error()) {{
                    console.error('AI Engine registration error:', result.error());
                    console.error(result.error_description());
                }} else {{
                    console.log('AI Engine registered:', result.data());
                }}
    
                BX24.installFinish();
            }}
        );
    
    }});
    </script>
    </head>
    <body>INSTALLED</body>
    </html>"""

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
