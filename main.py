from flask import Flask, request
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
