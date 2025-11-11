#  Agentic Credit Card Assistant

An **AI-powered conversational credit card assistant** built with **FastAPI**, **Python**, **MySQL**, and **Google Gemini API**.  
This project intelligently recommends credit cards based on user benefits and guides them through a complete **end-to-end credit card application process** — all within a single chat interface.

---

##  Features

-  **AI-driven agentic workflow** powered by Gemini API  
-  **Smart credit card recommendations** based on lifestyle benefits  
-  **Eligibility checking** using CIBIL score and annual income  
-  **Aadhaar and Email OTP verification simulators**  
-  **Full credit card application process** within the chat  
-  **MySQL database integration** for user, card, and verification data  
-  **Chat-based web interface** built with HTML, CSS, and FastAPI  
-  **Strict step-by-step logic** defined in `prompt.txt` for LLM guidance  

---

##  Tech Stack

| Layer | Technology |
|-------|-------------|
| **Language** | Python |
| **Backend Framework** | FastAPI |
| **Frontend** | HTML, CSS, JavaScript |
| **Database** | MySQL |
| **LLM API** | Google Gemini |
| **Deployment Options** | Localhost, Vercel, Render |

---

##  Project Workflow

###  Stage 1: Card Selection
1. User specifies a **benefit type** (Travel, Shopping, Dining, etc.)  
2. The app calls the `GetCreditCards` tool and displays top 5 results (preferred banks prioritized)  
3. User can request **more options** or **change benefit type** dynamically  

###  Stage 2: Application Flow
1. User selects a preferred bank card  
2. System collects:
   - Full Name  
   - Aadhaar Number → sends OTP (via `VerifyAadhaarSendOtp` and `VerifyAadhaarOtp`)  
   - Email → OTP verified (via `SendEmailOTP` and `VerifyEmailOTP`)  
   - PAN → Identity check (via `VerifyIdentity`)  
3. Requests consent to:
   - Fetch **CIBIL score** (`GetCibil`)  
   - Get **Annual Salary** (`GetSalary`)  
4. Compares profile against card’s **MinCIBIL** and **MinAnnualIncome**  
   - If eligible → proceeds with application  
   - If not → suggests better-suited cards via `GetValidCards`  
5. Retrieves address from Aadhaar (`GetAddress`) and confirms delivery address  
6. Final confirmation via `SendConfirmation` tool and success message  

---

## Setup Instructions

###  Clone the Repository
git clone https://github.com/AV1101/Agentic_creditcard 
cd agentic-credit-card-assistant

###  Create and Activate Virtual Environment
python -m venv venv  
# On Windows  
venv\Scripts\activate  
# On macOS/Linux  
source venv/bin/activate  

###  Install Dependencies
pip install -r requirements.txt

###  Configure Database
- Create a MySQL database named `credit_card_agent`  
- Update connection credentials in `db_config.py`

###  Add Gemini API Key
export GEMINI_API_KEY="your_api_key_here"

###  Run the FastAPI App
uvicorn main:app --reload

### Access the Chat Interface
Visit  http://127.0.0.1:8000

---

## 💬 Example Conversation

**User:** I want a credit card for travel  
**Assistant:** Here are the top 5 travel cards...  
**User:** I’ll take the HDFC Diners Club Miles card  
**Assistant:** Great choice! Let’s begin your application. Please share your Aadhaar number...  
→ Aadhaar OTP, Email OTP, PAN verification follow  
→ CIBIL and salary check complete  
→ Application submitted successfully 

---

## Tools Integrated

| Tool Name | Purpose |
|------------|----------|
| `GetCreditCards` | Fetch top credit card options |
| `VerifyAadhaarSendOtp` | Send OTP to Aadhaar-linked mobile |
| `VerifyAadhaarOtp` | Verify Aadhaar OTP |
| `SendEmailOTP` | Send OTP to user’s email |
| `VerifyEmailOTP` | Verify email OTP |
| `VerifyIdentity` | PAN-based identity verification |
| `GetCibil` | Fetch user CIBIL score |
| `GetSalary` | Fetch user annual income |
| `GetAddress` | Retrieve Aadhaar-linked address |
| `SendConfirmation` | Send final application confirmation |
| `GetValidCards` | Suggest cards for low eligibility profiles |

---

## Author

**Avyakt Varshney**  
Student | Agentic Systems Developer | AI & FinTech Enthusiast  

Email: [avyaktvarshney@example.com]  
GitHub: [https://github.com/AV1101](https://github.com/AV1101)


