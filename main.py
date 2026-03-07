from flask import Flask, request, jsonify  # 👈 აქ დაემატა jsonify
import utils
from database import DatabaseManager
from ai_engine import AIEngine
# იმპორტი ახალი ჰენდლერებიდან
from registration_handler import handle_install
from message_handler import handle_incoming_message

app = Flask(__name__)

# ინიციალიზაცია
db = DatabaseManager()
ai = AIEngine(db)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.values
    event = data.get("event")

    # მონაცემების ამოღება (Parsing)
    access_token = data.get("auth[access_token]") or data.get("AUTH_ID")
    app_sid = utils.extract_app_sid(data)
    domain = utils.extract_domain(data)

    incoming_auth = {
        "access_token": access_token,
        "domain": domain,
        "application_token": app_sid,
        "client_endpoint": data.get("auth[client_endpoint]"),
    }

    # 1. ინსტალაციის დამუშავება
    should_register = (event == "ONAPPINSTALL") or ("AUTH_ID" in data) or ("APP_SID" in data)
    
    if should_register and access_token:
        # გადავამისამართებთ registration_handler-ში
        return handle_install(data, incoming_auth)

    # 2. მესიჯის დამუშავება
    if event == "ONIMBOTMESSAGEADD":
        # გადავამისამართებთ message_handler-ში
        return handle_incoming_message(data, incoming_auth, ai)

    return "OK", 200


# =====================================================================
# 👇 აქედან იწყება ჩვენი ახალი CoPilot (Gemini) Endpoint-ი 👇
# =====================================================================
# =====================================================================
# 👇 აქედან იწყება ჩვენი ახალი CoPilot (Gemini) Endpoint-ი 👇
# =====================================================================
@app.route("/api/ai/completions", methods=["GET", "POST"])
def ai_completions():
    # 1. Bitrix-ის სატესტო შემოწმება რეგისტრაციის დროს (GET მოთხოვნა)
    if request.method == "GET":
        return jsonify({"status": "success"}), 200

    try:
        # მონაცემების წამოღება (JSON ან Form Data)

        # სრული დიაგნოსტიკა
        print("\n================= CoPilot DEBUG =================", flush=True)
        print("Method:", request.method, flush=True)
        print("Headers:", dict(request.headers), flush=True)
        print("Args:", request.args.to_dict(flat=False), flush=True)
        print("Form:", request.form.to_dict(flat=False), flush=True)
        print("Values:", request.values.to_dict(flat=False), flush=True)
        print("Raw body bytes:", request.data, flush=True)
        print("Raw body text:", request.get_data(as_text=True), flush=True)
        print("=================================================\n", flush=True)
        
        data = request.get_json(silent=True)
        if not data:
            data = request.values.to_dict()

        # ვაიძულებთ პითონს, ლოგი მაშინვე გამოიტანოს ტერმინალში
        print(f"\n✅ [CoPilot Request]: {data}\n", flush=True)

        # თუ მონაცემები საერთოდ არ მოვიდა
        if not data:
            return jsonify({"status": "success"}), 200

        # ვიღებთ მომხმარებლის მიერ დაწერილ ტექსტს (პრომპტს)
        prompt = data.get("prompt", "")
        
        # სატესტო პასუხი, სანამ Gemini-ს მივაბამთ
        generated_text = f"მე ვარ შენი CoPilot ასისტენტი. შენ მომწერე: {prompt}"

        # ❗️ როდესაც მზად იქნები, ზედა ხაზს წაშლი და გამოიყენებ შენს ai_engine-ს:
        # generated_text = ai.generate_reply(prompt) 

        # ვაბრუნებთ პასუხს
        return jsonify({"result": generated_text}), 200

    except Exception as e:
        print(f"❌ Error in ai_completions: {e}", flush=True)
        return jsonify({"error": str(e)}), 500
# =====================================================================
# =====================================================================


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
