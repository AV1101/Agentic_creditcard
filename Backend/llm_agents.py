from google import genai
from google.genai import types
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool
from pydantic import BaseModel
import os
import json
from google.genai.types import Content, Part
from dotenv import load_dotenv
load_dotenv()
import re
import logging
from otp_simulator import (
    generate_email_otp,
    verify_email_otp,
    generate_aadhaar_otp,
    verify_aadhaar_otp,
    send_email_confirmation 
)
from db_operations import (
    search_credit_cards,
    get_mobile_by_aadhaar,
    verify_identity_records,
    get_cibil_score_by_pan,
    get_address_from_aadhaar,
    get_salary_from_pan,
    get_valid_cards
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("LoanAgent")

with open(r"", "r") as f: #<--add prompt.txt directory here
    SYSTEM_PROMPT = f.read()

MODEL_NAME = os.getenv("LLM_MODEL", "gemini-2.5-flash")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key=GOOGLE_API_KEY)

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,  
)

class Creditcardtype(BaseModel):
    keyword_name: str

import json

def search_credit_card_tool(keyword_name: str) -> str:
    results = search_credit_cards(keyword_name)

    if not results:
        return f"No credit cards found matching: {keyword_name}. Please try another benefit type."

    simplified = []
    for card in results:
        simplified.append({
            "Card Name": card.get("card_name", "N/A"),
            "Network": card.get("payment_network", "N/A"),
            "Joining Fee": card.get("joining_fee", "N/A"),
            "Annual Fee": card.get("annual_fee", "N/A"),
            "Reward Type": card.get("reward_method", "N/A"),
            "Fee Waiver": card.get("fee_waiver", "N/A"),
            "Other Benefits": card.get("other_benefits", "N/A"),
            "Preferred Bank": card.get("PreferredBank", "No"),
            "Min CIBIL": card.get("MinCIBIL", "N/A"),
            "Min Annual Income": card.get("MinAnnualIncome", "N/A")
        })
    json_summary = json.dumps(simplified, ensure_ascii=False, separators=(',', ':'))
    return (
        f"Fetched {len(results)} credit cards for '{keyword_name}' benefits. "
        "Use this dataset to display the top 5 cards, preferring those from HDFC, Axis, ICICI, SBI, "
        "Standard Chartered, or American Express. If user asks for more, you can display additional ones.\n\n"
        f"Credit Card Dataset:\n{json_summary}"
    )

#-----------------------------------------------------------------------------------------------------------------------------
def send_email_otp(email: str) -> str:
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email or ""):
        return "Invalid email"
    result = generate_email_otp(email)
    logger.info(f"Sent OTP for email {email}: {result}")
    return f"OTP sent to email successfully: {email}"

def verify_email_otp_tool(email: str, otp: str) -> str:
    """Verifies an email OTP with full validation and error handling."""
    try:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return "Invalid email format."  
        if not re.match(r"^\d{6}$", otp):
            return "Invalid OTP format. OTP should be 6 digits."
        result = verify_email_otp(email, otp)
        if isinstance(result, dict) and result.get("success"):
            logger.info(f"Email OTP verification for {email}: Success")
            return "Thank you. Your email has been successfully verified."
        else:
            logger.info(f"Email OTP verification for {email}: Failed ({result.get('error', 'Unknown error')})")
            return f"Invalid or expired OTP. Please try again."

    except Exception as e:
        logger.exception(f"Error in verify_email_otp_tool: {e}")
        return "An unexpected error occurred while verifying your email OTP."


    
def verify_aadhaar_send_otp(aadhaar: str) -> str:
    """Sends an OTP to the Aadhaar-linked mobile number."""
    try:
        if not aadhaar:
            logger.error("Aadhaar argument missing or None in tool call.")
            return "Aadhaar number missing. Please enter a valid 12-digit Aadhaar."

        aadhaar = str(aadhaar).strip()
        if not re.match(r'^\d{12}$', aadhaar):
            return "Invalid Aadhaar number format. Please enter a valid 12-digit Aadhaar."

        mobile = get_mobile_by_aadhaar(aadhaar)
        logger.debug(f"Aadhaar lookup result: {mobile}")

        if not mobile:
            logger.error(f"No mobile linked to Aadhaar {aadhaar}")
            return "No mobile linked to this Aadhaar number."

        otp_status = generate_aadhaar_otp(aadhaar)
        logger.info(f"Sent Aadhaar OTP for {aadhaar} to mobile {mobile}: {otp_status}")

        if not otp_status or not otp_status.get("success"):
            return f"Failed to send OTP: {otp_status.get('error', 'Unknown error')}"

        masked = f"{mobile[:2]}*****{mobile[-3:]}"
        return f"OTP sent to your Aadhaar-linked mobile number ending with {masked}. Please enter the OTP to continue."

    except Exception as e:
        logger.exception(f"Unexpected error in verify_aadhaar_send_otp: {e}")
        return "An unexpected error occurred while sending the OTP. Please try again later."


def verify_aadhaar_otp_tool(aadhaar: str, otp: str) -> str:
    """Verifies an Aadhaar OTP using the Aadhaar number and OTP entered by the user."""
    try:
        if not aadhaar or not re.match(r'^\d{12}$', aadhaar.strip()):
            return "Invalid Aadhaar number format. Please enter a valid 12-digit Aadhaar."

        if not otp or not re.match(r'^\d{6}$', otp.strip()):
            return "Invalid OTP format. Please enter a valid 6-digit OTP."

        result = verify_aadhaar_otp(aadhaar.strip(), otp.strip())

        logger.info(f"Aadhaar OTP verification for {aadhaar}: {'Success' if result.get('success') else 'Failed'}")

        if result.get("success"):
            return "✅ Aadhaar verified successfully!"
        else:
            return f"❌ Verification failed: {result.get('error', 'Unknown error')}"

    except Exception as e:
        logger.exception(f"Error verifying Aadhaar OTP: {e}")
        return "An unexpected error occurred while verifying the Aadhaar OTP."


def verify_identity_tool(name: str, aadhaar: str, pan: str) -> str:
    """Verifies identity details (Name, Aadhaar, PAN) with safe parsing and validation."""
    try:
        # Basic validation checks
        if not re.match(r'^[a-zA-Z ]{2,50}$', name):
            return "Invalid name format. Only alphabets and spaces allowed."
        if not re.match(r'^\d{12}$', aadhaar):
            return "Invalid Aadhaar format. Must be a 12-digit number."
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan):
            return "Invalid PAN format. Example: ABCDE1234F"

        # Perform the actual verification
        is_valid = verify_identity_records(name, aadhaar, pan)
        logger.info(f"Identity verification for {name}, {aadhaar}, {pan}: {'Success' if is_valid else 'Failed'}")

        return "Identity verified!" if is_valid else "Identity verification failed."
    except Exception as e:
        logger.exception(f"Error in verify_identity_tool: {e}")
        return "An unexpected error occurred during identity verification. Please try again."



def get_cibil_tool(pan: str) -> str:
    if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan):
        return "Invalid PAN format"
    score = get_cibil_score_by_pan(pan.strip())
    logger.info(f"CIBIL score for PAN {pan}: {score}")
    if score == -1:
        return "CIBIL score not found for given PAN."
    return f"The User's CIBIL score is {score}."

def get_salary_tool(pan: str) -> str:
    if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan):
        return "Invalid PAN format"
    salary = get_salary_from_pan(pan.strip())
    logger.info(f"Salary for PAN {pan}: {salary}")
    if salary == -1:
        return "Salary not found for given PAN."
    return f"The User's salary is ₹{salary}."

def get_vaild_cards_tool(salary: float, cibil: int, major_keyword: str) -> str:
    """Fetches and formats valid credit card options based on salary, CIBIL score, and benefit type."""
    try:
        salary = float(salary)
    except (ValueError, TypeError):
        salary = 0.0

    results = get_valid_cards(salary, cibil, major_keyword)

    if not results:
        return f"No credit cards found matching: {major_keyword}. Please try another benefit type."

    ranked = sorted(
        results,
        key=lambda card: (
            card.get("annual_fee", 999999) or 999999,
            card.get("joining_fee", 999999) or 999999
        )
    )

    simplified = []
    for card in ranked:
        simplified.append({
            "Card Name": card.get("card_name", "N/A"),
            "Network": card.get("payment_network", "N/A"),
            "Joining Fee": card.get("joining_fee", "N/A"),
            "Annual Fee": card.get("annual_fee", "N/A"),
            "Reward Type": card.get("reward_method", "N/A"),
            "Fee Waiver": card.get("fee_waiver", "N/A"),
            "Other Benefits": card.get("other_benefits", "N/A"),
            "Preferred Bank": card.get("PreferredBank", "No"),
            "Min CIBIL": card.get("MinCIBIL", "N/A"),
            "Min Annual Income": card.get("MinAnnualIncome", "N/A")
        })

    json_summary = json.dumps(simplified, ensure_ascii=False, separators=(',', ':'))
    return (
        f"Fetched {len(results)} valid credit cards for '{major_keyword}' benefits "
        f"(CIBIL: {cibil}, Salary: ₹{salary:,.0f}). "
        "Use this dataset to display the most suitable cards, prioritizing those from HDFC, Axis, ICICI, SBI, "
        "Standard Chartered, or American Express. If user asks for more, show additional ones.\n\n"
        f"Valid Credit Card Dataset:\n{json_summary}"
    )


#-----------------------------------------------------------------------------------------------------------------------------
def get_address_tool(aadhaar: str) -> str:
    result= get_address_from_aadhaar(aadhaar)
    if not result:
        return f"No credit cards found matching: {aadhaar}. Please try another benefit type."
    else:
        return result

def send_confirmation_tool(email: str) -> str:
    """Sends a confirmation email to the given address."""
    try:
        email = email.strip()
        send_email_confirmation(email)
        logger.info(f"Confirmation email sent to {email}")
        return f"Confirmation email sent to: {email}"
    except Exception as e:
        logger.error(f"Error sending confirmation email: {e}")
        return "Failed to send confirmation email. Please check the email address."

tools = [
    Tool.from_function(
        name= "GetCreditCards",
        func= search_credit_card_tool,
        description= "Get Credit cards based on benefit type"
    ),
    Tool.from_function(
        name="SendEmailOTP",
        func=send_email_otp,
        description="Send OTP to email. Input: email as string."
    ),
    Tool.from_function(
        name="VerifyEmailOTP",
        func=verify_email_otp_tool,
        description="Verify email OTP. Takes two parameters: email and otp."
    ),
    Tool.from_function(
        name="VerifyAadhaarSendOtp",
        func=verify_aadhaar_send_otp,
        description="Sends an OTP to the mobile linked with the given Aadhaar number.",
        args_schema={"aadhaar":str},
    ),
    Tool.from_function(
        name="VerifyAadhaarOtp",
        func=verify_aadhaar_otp_tool,
        description="Verify Aadhaar OTP using Aadhaar number and OTP. Inputs: aadhaar (12-digit), otp (6-digit)"
    ),
    Tool.from_function(
        name="VerifyIdentity",
        func=verify_identity_tool,
        description="Verify user identity details using name, Aadhaar, and PAN. Takes three parameters: name, aadhaar, pan."
    ),
    Tool.from_function(
        name="GetCibil",
        func=get_cibil_tool,
        description="Get the CIBIL of the user using their PAN"
    ),
    Tool.from_function(
        name="GetAddress",
        func=get_address_tool,
        description="Get the address of the user using their Aadhaar"
    ),
    Tool.from_function(
        name="GetSalary",
        func=get_salary_tool,
        description="Get the salary of the user using their PAN"
    ),
    Tool.from_function(
        name="GetValidCards",
        func=get_vaild_cards_tool,
        description="Get credit cards matching user CIBIL and salary"
    ),
    Tool.from_function(
        name="SendConfirmation",
        func=send_confirmation_tool,
        description="Send Confirmation of user application"
    )
]

tools_registry  = {
            "GetCreditCards": search_credit_card_tool,
            "SendEmailOTP": send_email_otp,
            "VerifyEmailOTP": verify_email_otp_tool,
            "VerifyAadhaarSendOtp": verify_aadhaar_send_otp,
            "VerifyAadhaarOtp": verify_aadhaar_otp_tool,
            "VerifyIdentity": verify_identity_tool,
            "GetCibil": get_cibil_tool,
            "GetAddress": get_address_tool,
            "GetSalary": get_salary_tool,
            "GetValidCards": get_vaild_cards_tool,
            "SendConfirmation": send_confirmation_tool
        }

def run_gemini(prompt: str, tools_registry=None):
    try:
        logger.info("--- Running Gemini ---")

        contents = [
            types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )
        ]

        tool_defs = []
        for name, fn in (tools_registry or {}).items():
            if not name or not re.match(r'^[A-Za-z_][A-Za-z0-9_\.\-:]{0,63}$', name):
                logger.warning(f"Skipping invalid function name: {name}")
                continue

            params = {
                "type": "object",
                "properties": {},
                "required": []
            }

            try:
                import inspect
                sig = inspect.signature(fn)
                for param_name, param in sig.parameters.items():
                    params["properties"][param_name] = {"type": "string"}
                    params["required"].append(param_name)
            except Exception:
                pass

            tool_defs.append(
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=name,
                            description=fn.__doc__ or f"Function {name} for Gemini tool calling.",
                            parameters=params
                        )
                    ]
                )
            )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=tool_defs,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False),
            )
        )

        logger.info(f"Gemini raw response: {repr(response)}")

        if response and hasattr(response, "candidates"):
            for candidate in response.candidates:
                parts = getattr(candidate.content, "parts", [])
                for part in parts:
                    if hasattr(part, "function_call") and part.function_call:
                        fn_call = part.function_call
                        fn_name = fn_call.name
                        fn_args = json.loads(fn_call.args) if isinstance(fn_call.args, str) else fn_call.args
                        logger.info(f"Tool Call: {fn_name}({fn_args})")

                        if fn_name in (tools_registry or {}):
                            fn = tools_registry[fn_name]
                            if not fn_args or any(v is None for v in fn_args.values()):
                                logger.warning(f"Skipping tool call {fn_name} due to missing args: {fn_args}")
                                return f"Tool call skipped: invalid arguments ({fn_args})"
                            try:
                                # ✅ Run the tool only once
                                result = fn(**fn_args)
                                logger.info(f"Tool result for {fn_name}: {result}")

                                # ✅ Prevent Gemini from re-calling the same tool
                                safe_result_text = (
                                    f"The tool {fn_name} executed successfully and returned this result:\n"
                                    f"{result}\n"
                                    f"Please continue the conversation naturally based on this result. "
                                    f"Do not call the same tool again."
                                )

                                # ✅ Feed result back for natural continuation
                                follow_up = client.models.generate_content(
                                    model=MODEL_NAME,
                                    contents=[
                                        types.Content(role="user", parts=[types.Part(text=prompt)]),
                                        types.Content(role="model", parts=[types.Part(text=safe_result_text)])
                                    ]
                                )

                                return follow_up.text.strip() if hasattr(follow_up, "text") and follow_up.text else str(result)

                            except Exception as e:
                                logger.error(f"Error executing tool {fn_name}: {e}")
                                return f"Tool execution failed for {fn_name}: {e}"

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        return "No valid response received from Gemini."

    except Exception as e:
        logger.error(f"Gemini tool execution failed: {e}", exc_info=True)
        return f"Gemini tool execution failed: {str(e)}"


def run_llm_agents(user_input: str) -> str:
    try:
        memory_vars = memory.load_memory_variables({})
        chat_history = memory_vars.get("chat_history", [])

        history_text = "\n".join(
            [f"User: {msg.content}" if msg.type == "human" else f"AI: {msg.content}" for msg in chat_history]
        )

        prompt = f"""{SYSTEM_PROMPT}

Previous conversation:
{history_text}

User query: {user_input}
"""
        output = run_gemini(prompt, tools_registry)
        memory.save_context({"input": user_input}, {"output": output[:4000]})
        return output.strip()

    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return f"Agent execution failed: {str(e)}"
    

def test_run_gemini():
    print("\n--- Running Gemini Test ---")
    test_prompt = "List the top 3 benefits of using a travel credit card."
    
    result = run_gemini(test_prompt, tools_registry)
    print("\nGemini Test Output:\n", result)
    print("--- Test Complete ---\n")

if __name__ == "__main__":

    test_run_gemini()
