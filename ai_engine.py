import google.generativeai as genai
from config import Config, ConfigManager

class AIEngine:
    def __init__(self, db_manager):
        if Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
        else:
             print("❌ ERROR: GEMINI_API_KEY ვერ მოიძებნა!")
             
        self.db = db_manager

    def get_response(self, chat_id: str, message: str) -> str:
        if not Config.GEMINI_API_KEY:
            return "ბოდიში, AI არ მუშაობს (GEMINI_API_KEY ცარიელია)."

        system_instruction = ConfigManager.load_company_info()
        history = self.db.load_history(chat_id)
        
        try:
            # ცდა 1: Gemini 2.5 Flash
            model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)
            chat = model.start_chat(history=history)
            response = chat.send_message(message)
            text_response = response.text

            # შენახვა
            self.db.save_message(chat_id, "user", message)
            self.db.save_message(chat_id, "model", text_response)
            
            return text_response

        except Exception as e1:
            print(f"❌ Gemini error (2.5-flash): {e1}")
            try:
                # ცდა 2: Gemini Pro (Fallback)
                model = genai.GenerativeModel("gemini-pro", system_instruction=system_instruction)
                chat = model.start_chat(history=history)
                response = chat.send_message(message)
                text_response = response.text
                
                self.db.save_message(chat_id, "user", message)
                self.db.save_message(chat_id, "model", text_response)

                return text_response
            except Exception as e2:
                print(f"❌ Gemini error (gemini-pro): {e2}")
                return "ბოდიში, AI დროებით მიუწვდომელია."
