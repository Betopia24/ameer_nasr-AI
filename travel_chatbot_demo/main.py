import requests
import json
from datetime import datetime
import os

class LawFirmChatbot:
    def __init__(self):
        self.api_key = ""
        self.base_url = ""
        self.conversation_history = []
        self.client_info = {}
        self.session_start_time = datetime.now()
        self.recommended_attorney = None
        
        # Sample attorney database
        self.attorneys = {
            "criminal": {
                "name": "John Smith",
                "specialization": "Criminal Defense",
                "experience": "15 years",
                "contact": "john.smith@lawfirm.com"
            },
            "family": {
                "name": "Sarah Johnson",
                "specialization": "Family Law",
                "experience": "12 years",
                "contact": "sarah.johnson@lawfirm.com"
            },
            "personal_injury": {
                "name": "Michael Brown",
                "specialization": "Personal Injury",
                "experience": "18 years",
                "contact": "michael.brown@lawfirm.com"
            },
            "business": {
                "name": "Emily Davis",
                "specialization": "Business Law",
                "experience": "20 years",
                "contact": "emily.davis@lawfirm.com"
            },
            "real_estate": {
                "name": "Robert Wilson",
                "specialization": "Real Estate Law",
                "experience": "14 years",
                "contact": "robert.wilson@lawfirm.com"
            },
            "employment": {
                "name": "Lisa Anderson",
                "specialization": "Employment Law",
                "experience": "16 years",
                "contact": "lisa.anderson@lawfirm.com"
            }
        }

    def call_groq_api(self, messages):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama3-8b-8192",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: {str(e)}"

    def analyze_legal_issue(self, user_input):
        system_prompt = """You are a legal assistant chatbot for a law firm. Your job is to:
1. Ask relevant questions to understand the client's legal problem
2. Determine which area of law the issue falls under
3. When you have enough information, categorize the issue as one of: criminal, family, personal_injury, business, real_estate, or employment

Respond naturally and ask one question at a time. When you're confident about the legal category, end your response with [CATEGORY: category_name]"""

        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history,
            {"role": "user", "content": user_input}
        ]
        
        return self.call_groq_api(messages)

    def extract_category(self, response):
        if "[CATEGORY:" in response:
            category = response.split("[CATEGORY:")[1].split("]")[0].strip()
            return category.lower()
        return None

    def suggest_attorney(self, category):
        if category in self.attorneys:
            attorney = self.attorneys[category]
            self.recommended_attorney = attorney
            return f"""
Based on your legal issue, I recommend our attorney:

Name: {attorney['name']}
Specialization: {attorney['specialization']}
Experience: {attorney['experience']}
Contact: {attorney['contact']}

Would you like me to help you schedule a consultation or create a summary of our conversation?
"""
        else:
            return "I apologize, but I couldn't determine the best attorney for your case. Please contact our main office for assistance."

    def start_chat(self):
        print("Welcome to our Law Firm Legal Assistant!")
        print("I'm here to understand your legal issue and connect you with the right attorney.")
        print("Please describe your legal problem or situation.")
        print("(You can ask for a 'summary' at any time to save our conversation)\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Thank you for contacting our law firm. Have a great day!")
                break
            
            if not user_input:
                continue
            
            # Check if user is asking for a summary
            if self.handle_summary_request(user_input) and self.conversation_history:
                summary_result = self.create_summary()
                print(f"\nAssistant: {summary_result}")
                
                continue_chat = input("\nWould you like to continue our conversation? (yes/no): ").strip().lower()
                if continue_chat not in ['yes', 'y']:
                    print("Thank you for contacting our law firm. Have a great day!")
                    break
                else:
                    print("\nHow else can I help you today?\n")
                continue
            
            # Add user input to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Get AI response
            ai_response = self.analyze_legal_issue(user_input)
            print(f"\nAssistant: {ai_response}")
            
            # Check if AI has determined a category
            category = self.extract_category(ai_response)
            if category:
                # Remove the category tag from display
                clean_response = ai_response.split("[CATEGORY:")[0].strip()
                print(f"\nAssistant: {clean_response}")
                
                # Suggest attorney
                attorney_suggestion = self.suggest_attorney(category)
                print(f"\nAssistant: {attorney_suggestion}")
                
                # Ask if they want to continue or start over
                continue_chat = input("\nWould you like to discuss another legal matter or request a summary? (continue/summary/quit): ").strip().lower()
                
                if continue_chat in ['summary', 's']:
                    summary_result = self.create_summary()
                    print(f"\nAssistant: {summary_result}")
                    
                    final_choice = input("\nWould you like to discuss another matter? (yes/no): ").strip().lower()
                    if final_choice not in ['yes', 'y']:
                        print("Thank you for contacting our law firm. Have a great day!")
                        break
                    else:
                        # Reset for new conversation
                        self.conversation_history = []
                        self.recommended_attorney = None
                        self.session_start_time = datetime.now()
                        print("\nPlease describe your new legal problem or situation.\n")
                        
                elif continue_chat in ['continue', 'c', 'yes', 'y']:
                    # Reset for new conversation
                    self.conversation_history = []
                    self.recommended_attorney = None
                    self.session_start_time = datetime.now()
                    print("\nPlease describe your new legal problem or situation.\n")
                else:
                    print("Thank you for contacting our law firm. Have a great day!")
                    break
            else:
                # Add AI response to conversation history
                self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            print()  # Add blank line for readability
            
    def create_summary(self):
        """Generate a summary of the conversation and save it to a file"""
        try:
            # Create summary using AI
            summary_prompt = """Please create a concise summary of this legal consultation conversation. Include:
1. Client's main legal issue
2. Key details discussed
3. Recommended attorney and specialization
Format it as a professional consultation summary."""

            conversation_text = "\n".join([
                f"{'Client' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}" 
                for msg in self.conversation_history
            ])

            messages = [
                {"role": "system", "content": summary_prompt},
                {"role": "user", "content": f"Conversation:\n{conversation_text}"}
            ]

            summary_content = self.call_groq_api(messages)

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"consultation_summary_{timestamp}.txt"

            # Create summaries directory if it doesn't exist
            if not os.path.exists("summaries"):
                os.makedirs("summaries")

            # Write summary to file
            filepath = os.path.join("summaries", filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("="*50 + "\n")
                f.write("LEGAL CONSULTATION SUMMARY\n")
                f.write("="*50 + "\n\n")
                f.write(f"Date: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Duration: {datetime.now() - self.session_start_time}\n\n")
                
                if self.recommended_attorney:
                    f.write("RECOMMENDED ATTORNEY:\n")
                    f.write(f"Name: {self.recommended_attorney['name']}\n")
                    f.write(f"Specialization: {self.recommended_attorney['specialization']}\n")
                    f.write(f"Experience: {self.recommended_attorney['experience']}\n")
                    f.write(f"Contact: {self.recommended_attorney['contact']}\n\n")
                
                f.write("CONSULTATION SUMMARY:\n")
                f.write("-" * 25 + "\n")
                f.write(summary_content)
                f.write("\n\n" + "="*50 + "\n")
                f.write("END OF SUMMARY\n")

            return f"Summary saved successfully as '{filename}' in the 'summaries' folder."

        except Exception as e:
            return f"Error creating summary: {str(e)}"

    def handle_summary_request(self, user_input):
        """Check if user is asking for a summary"""
        summary_keywords = ['summary', 'summarize', 'save', 'file', 'document', 'record']
        return any(keyword in user_input.lower() for keyword in summary_keywords)

if __name__ == "__main__":
    chatbot = LawFirmChatbot()
    chatbot.start_chat()