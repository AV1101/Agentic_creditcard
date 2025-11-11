import mysql.connector
from decimal import Decimal
import re
import logging
logger = logging.getLogger("DB-ops")

def clean_for_json(obj):
    """Recursively convert Decimals to floats and ensure Gemini-safe outputs."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(i) for i in obj]
    return obj

def _extract_mobile_from_row(row):
    """Accept row as dict or string and return mobile string or None."""
    if row is None:
        return None
    # If row is already a plain string/int
    if isinstance(row, (str, int)):
        return str(row)
    # If dict-like, accept multiple key casings
    if isinstance(row, dict):
        # common variants
        for key in ("mobile", "Mobile", "MOBILE", "phone", "Phone", "PHONE"):
            if key in row and row[key] not in (None, ""):
                return str(row[key])
        # Sometimes the row is like {"Mobile": "6100..."} inside nested structures:
        # try to find first string value that looks like phone digits
        for v in row.values():
            if isinstance(v, (str, int)):
                s = re.sub(r"\D", "", str(v))
                if len(s) >= 6:
                    return s
    # Not found
    return None

DB_CONFIG = {
    "host": "", #<--MySQL workbench host
    "user": "", #<--MySQL workbench user
    "password": "", #<--MySQL workbench user password
    "database": "credit_cards"
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def search_credit_cards(major_keyword: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT card_name, payment_network, major_benefit, joining_fee, annual_fee, 
           reward_method, fee_waiver, other_benefits, PreferredBank, MinCIBIL, MinAnnualIncome
    FROM CreditCards
    WHERE major_benefit LIKE %s
    ORDER BY 
        CASE WHEN PreferredBank = 'Yes' THEN 1 ELSE 2 END,
        card_name;
    """
    cursor.execute(query, ('%' + major_keyword + '%',))
    rows = cursor.fetchall()
    conn.close()
    return clean_for_json(rows) 

def get_mobile_by_aadhaar(aadhaar: str):
    """
    Query DB and return the mobile number (string) linked to Aadhaar.
    Returns None if not found.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT Mobile FROM Aadhaar WHERE AadhaarID = %s LIMIT 1"
    cursor.execute(query, (aadhaar,))
    result = cursor.fetchone()
    conn.close()

    logger.debug(f"[get_mobile_by_aadhaar] DB raw result for {aadhaar}: {result!r}")
    mobile = _extract_mobile_from_row(result)

    if mobile:
        # normalize to digits-only
        mobile_digits = re.sub(r'\D', '', mobile)
        if mobile_digits:
            return mobile_digits
    return None
    
def verify_identity_records(name: str, aadhaar: str, pan: str) -> bool:
    """Verifies if the given Aadhaar and PAN belong to the same user."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT 1 FROM people
    WHERE LOWER(Name) = LOWER(%s) AND aadhaarID = %s AND panID = %s
    LIMIT 1
    """
    cursor.execute(query, (name, aadhaar, pan))
    row = cursor.fetchone()
    conn.close()

    # Return True if a record exists, else False
    found = row is not None
    logger.info(f"Identity check for {name}, {aadhaar}, {pan}: {'Match' if found else 'No match'}")
    return found

def get_cibil_score_by_pan(pan: str) -> int:
    """Fetch the CIBIL score of the user with given pan number."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT CIBIL FROM pan
    WHERE panID = %s
    """
    cursor.execute(query, (pan,))
    result = cursor.fetchone()
    conn.close()
    return clean_for_json(result["CIBIL"]) if result else -1

def get_address_from_aadhaar(aadhaar: str)-> str:
    """Fetch the address of the user with given aadhaar number."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT address FROM aadhaar
    WHERE aadhaarID = %s
    """
    cursor.execute(query, (aadhaar,))   
    result = cursor.fetchone()
    conn.close()
    return clean_for_json(result["address"]) if result else ""

def get_salary_from_pan(pan: str) -> str:
    """Fetch the annual income of the user with the given PAN number."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT Annual_Income FROM pan
        WHERE panID = %s
        """
        cursor.execute(query, (pan,))
        result = cursor.fetchone()
        conn.close()

        if result and "Annual_Income" in result:
            return clean_for_json(result["Annual_Income"])
        else:
            return -1
    except Exception as e:
        logger.exception(f"Error in get_salary_from_pan: {e}")
        return -1
    
    
def get_valid_cards(salary:float, cibil:int, major_keyword:str)->list[dict]:
    """Fetch cards with minimum requirements equal to or more than CIBIL and salary of user"""
    conn= get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT card_name, payment_network, major_benefit, joining_fee, annual_fee, 
           reward_method, fee_waiver, other_benefits, PreferredBank, MinCIBIL, MinAnnualIncome
    FROM CreditCards
    WHERE major_benefit LIKE %s AND MinCIBIL <= %s AND MinAnnualIncome <= %s
    ORDER BY 
        CASE WHEN PreferredBank = 'Yes' THEN 1 ELSE 2 END,
        card_name;
    """
    cursor.execute(query, ('%' + major_keyword + '%', int(cibil), float(salary)))
    rows = cursor.fetchall()
    conn.close()

    return clean_for_json(rows)
