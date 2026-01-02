import requests

class BitrixClient:
    @staticmethod
    def call(method, params, auth_data):
        # 1. დომენის ამოღება (დაცული მეთოდით)
        domain = auth_data.get("domain")
        if not domain and auth_data.get("client_endpoint"):
            try:
                domain = auth_data["client_endpoint"].split("/rest")[0].replace("https://", "").replace("http://", "")
            except:
                domain = ""

        if not domain:
            print(f"❌ REST Error ({method}): Domain not found in auth_data")
            return {}

        # 2. URL-ის აწყობა
        url = f"https://{domain}/rest/{method}"

        # 3. მონაცემების მომზადება (ვრწმუნდებით, რომ dictionary-ია)
        try:
            payload = dict(params or {})
        except:
            payload = {}

        # ავტორიზაციის კოდის ჩამატება (მხოლოდ სტრინგი!)
        token = auth_data.get("access_token")
        if token:
            payload["auth"] = str(token)

        # 4. გაგზავნა
        try:
            # requests-ს მონაცემები გადაეცემა 'data'-თი, რაც ავტომატურად ამუშავებს Dictionary-ს
            response = requests.post(url, data=payload, timeout=25)
            return response.json()
        except Exception as e:
            # აქ ვბეჭდავთ შეცდომას დეტალურად
            print(f"❌ REST Error ({method}): {e}")
            return {}

    @staticmethod
    def send_message(chat_id, text, auth_data, bot_id):
        if not bot_id: 
            print("🛑 BOT_ID missing, cannot send message.")
            return
        
        # chat_id და bot_id სტრინგებად გადაგვყავს
        res = BitrixClient.call("imbot.message.add", 
                          {"BOT_ID": str(bot_id), "DIALOG_ID": str(chat_id), "MESSAGE": str(text)}, 
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
            ids = [str(x) for x in raw if isinstance(x, (str, int))]
            if len(ids) == 1: return ids[0]

        elif isinstance(raw, dict):
            for k, v in raw.items():
                if isinstance(v, dict):
                    if str(v.get("CODE")) == str(bot_code): 
                        return v.get("ID")
        
        return str(raw) if isinstance(raw, (str, int)) else None