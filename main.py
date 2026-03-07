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
    if request.method == "GET":
        return jsonify({"status": "success"}), 200

    try:
        raw_bytes = request.get_data(cache=True)
        raw_text = raw_bytes.decode("utf-8", errors="replace")

        print("\n================= CoPilot DEBUG =================", flush=True)
        print("Method:", request.method, flush=True)
        print("Headers:", dict(request.headers), flush=True)
        print("Content-Length header:", request.headers.get("Content-Length"), flush=True)
        print("Raw bytes len:", len(raw_bytes), flush=True)
        print("Raw text first 1000 chars:", raw_text[:1000], flush=True)
        print("=================================================\n", flush=True)

        data = request.get_json(silent=True)

        if not data and raw_text:
            try:
                data = json.loads(raw_text)
            except Exception as e:
                print("JSON parse error:", e, flush=True)
                data = None

        if not data:
            return jsonify({
                "result": "No input received"
            }), 200

        prompt = data.get("prompt", "")

        # დროებითი ტესტი
        generated_text = f"Test response from Flask Copilot. Prompt length: {len(prompt)}"

        return jsonify({
            "result": generated_text
        }), 200

    except Exception as e:
        print(f"❌ Error in ai_completions: {e}", flush=True)
        return jsonify({"error": str(e)}), 500
# =====================================================================
# =====================================================================


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
