import requests

class BitrixClient:
    @staticmethod
    def call(method, params, auth_data):
        domain = auth_data.get("domain")
        if not domain and auth_data.get("client_endpoint"):
            domain = auth_data["client_endpoint"].split("/rest")[0].replace("https://", "").replace("http://", "")

        if not domain: return {}

        url = f"https://{domain}/rest/{method}"
        payload = dict(params or {})
        payload["auth"] = auth_data.get("access_token")

        try:
            response = requests.post(url, data=payload, timeout=25)
            return response.json()
        except Exception as e:
            print(f"❌ REST Error ({method}): {e}")
            return {}

    @staticmethod
    def send_message(chat_id, text, auth_data, bot_id):
        if not bot_id: 
            print("🛑 BOT_ID missing, cannot send message.")
            return
            
        res = BitrixClient.call("imbot.message.add", 
                          {"BOT_ID": str(bot_id), "DIALOG_ID": str(chat_id), "MESSAGE": text}, 
                          auth_data)
        if "result" in res:
            print("✅ Sent successfully!")
        else:
            print(f"📬 Bitrix Error: {res}")

    @staticmethod
    def resolve_bot_id(auth_data, bot_code):
        res = BitrixClient.call("imbot.bot.list", {}, auth_data)
        raw = res.get("result")
        
        if isinstance(raw, list):
            if raw and isinstance(raw[0], dict):
                for b in raw:
                    if str(b.get("CODE")) == str(bot_code): 
                        return b.get("ID")
            # თუ ID-ების სიაა
            ids = [str(x) for x in raw if isinstance(x, (str, int))]
            if len(ids) == 1: return ids[0]

        elif isinstance(raw, dict):
            for k, v in raw.items():
                if isinstance(v, dict):
                    if str(v.get("CODE")) == str(bot_code): 
                        return v.get("ID")
        
        return str(raw) if isinstance(raw, (str, int)) else None
