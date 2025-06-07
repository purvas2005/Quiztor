from flask import Flask, jsonify, request
import requests
from web3 import Web3
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from requests_toolbelt import MultipartEncoder
from pathlib import Path
from collections import OrderedDict
import pyshorteners
import random

load_dotenv()

# Environment variables
contractAddress = os.getenv("SMART_CONTRACT_ADDRESS")
privateKey = os.getenv("ACCOUNT_PRIVATE_KEY")
accountAddress = os.getenv("ACCOUNT_ADDRESS")
localRPC = "http://127.0.0.1:8545"

# Contract and Pinata configuration
contractJSON = r"D:\CIE_Internship2025\DemoV2\summer-2025\SW2\StudentNFT\Solidity\artifacts\contracts\StudentNFT.sol\StudentBadgeNFT.json"
pinataJWT = os.getenv("PINATA_JWT")
pinataBaseURL = os.getenv("PINATA_BASE_URL")
pinataLegacyURL = os.getenv("PINATA_LEGACY_URL")
STUDENT_BADGE_DATA = "./StudentBadges/StudentBadgeData.json"
CERTIFICATE_DIR = "certificates"

# Quiz configuration
TOKENS_PER_CORRECT_ANSWER = 50
MINIMUM_TOKENS_FOR_NFT = 300
QUIZ_QUESTIONS_FILE = "quiz_questions.json"

# Pinata Headers
PINATA_JWT = os.getenv("PINATA_JWT")
HEADERS = {
    "Authorization": f"Bearer {PINATA_JWT}"
}

# Initialize Flask app
app = Flask(__name__)

# Connect to blockchain
web3 = Web3(Web3.HTTPProvider(localRPC))
assert web3.is_connected()

# Load contract ABI
with open(contractJSON) as f:
    abi = json.load(f)['abi']

checksum_address = Web3.to_checksum_address(contractAddress)
contract = web3.eth.contract(address=checksum_address, abi=abi)

# Quiz questions (hardcoded for now, can be loaded from JSON file)
QUIZ_QUESTIONS = [
    {
        "id": 1,
        "question": "What is intellectual property (IP)?",
        "options": [
            "A physical asset owned by a company",
            "A set of legal rights over creations of the mind",
            "A form of tangible property like land or machinery",
            "A type of government regulation on businesses"
        ],
        "correct_answer": 1
    },
    {
        "id": 2,
        "question": "Which of the following is NOT a type of intellectual property?",
        "options": [
            "Patents",
            "Copyrights", 
            "Trademarks",
            "Having a thought for an idea for a smartphone"
        ],
        "correct_answer": 3
    },
    {
        "id": 3,
        "question": "What type of intellectual property protects an invention?",
        "options": [
            "Copyright",
            "Trademark",
            "Patent",
            "Trade secret"
        ],
        "correct_answer": 2
    },
    {
        "id": 4,
        "question": "A trademark primarily protects:",
        "options": [
            "Literary and artistic works",
            "A company's brand name, logo, or slogan",
            "The design of a product",
            "A new technological invention"
        ],
        "correct_answer": 1
    },
    {
        "id": 5,
        "question": "How long does a copyright generally last in most countries?",
        "options": [
            "10 years",
            "The lifetime of the author plus 60-70 years",
            "20 years from the filing date",
            "Indefinitely as long as it is in use"
        ],
        "correct_answer": 1
    }
]

# In-memory storage for user sessions and tokens
user_sessions = {}
user_tokens = {}

# Utility functions
def get_nonce(address):
    return web3.eth.get_transaction_count(address)

def initialize_user_tokens(user_address, initial_tokens=10000):
    """Initialize user with tokens if not already present"""
    if user_address not in user_tokens:
        user_tokens[user_address] = initial_tokens
    return user_tokens[user_address]

def get_user_tokens(user_address):
    """Get current token balance for user"""
    return user_tokens.get(user_address, 0)

def add_tokens(user_address, amount):
    """Add tokens to user balance"""
    if user_address not in user_tokens:
        user_tokens[user_address] = 0
    user_tokens[user_address] += amount
    return user_tokens[user_address]

def deduct_tokens(user_address, amount):
    """Deduct tokens from user balance"""
    if user_address not in user_tokens:
        return False
    if user_tokens[user_address] < amount:
        return False
    user_tokens[user_address] -= amount
    return True

# Existing Pinata functions (unchanged)
def uploadFileToPinata(filePath, name=None, keyValues=None, groupID=None, network="public"):
    if not os.path.isfile(filePath):
        raise FileNotFoundError(f"File not found: {filePath}")
    
    fileName = os.path.basename(filePath)
    print(f"The fileName is: {fileName}")

    fields = {
        "file": (fileName, open(filePath, "rb"), "application/octet-stream"),
        "network": network
    }

    if name:
        fields["name"] = name
    if groupID:
        fields["group_id"] = groupID
    if keyValues:
        fields["keyvalues"] = json.dumps(keyValues)

    m = MultipartEncoder(fields=fields)
    headers = {
        "Authorization": f"Bearer {PINATA_JWT}",
        "Content-Type": m.content_type
    }

    response = requests.post("https://uploads.pinata.cloud/v3/files",
                             headers=headers,
                             data=m,
                             timeout=30)

    if response.status_code != 200:
        raise requests.HTTPError(f"Upload failed: {response.status_code} - {response.text}")

    responseJSON = response.json()
    if "data" not in responseJSON or "cid" not in responseJSON["data"]:
        raise ValueError("Unexpected response format: 'cid' missing")

    return responseJSON["data"]

def uploadMetadataToPinata(metadata):
    url = pinataLegacyURL
    headers = {
        "Authorization": f"Bearer {pinataJWT}",
        "Content-Type": "application/json"
    }
    response = requests.request("POST", url, json=metadata, headers=headers)
    if response.status_code != 200:
        raise requests.HTTPError(f"Pinning Metadata to Pinata Failed: {response.status_code} - {response.text}")
    
    responseJSON = response.json()
    if "IpfsHash" not in responseJSON:
        raise ValueError("IPFSHash is not found in the Response")
    return responseJSON["IpfsHash"]

# NEW QUIZ-RELATED ENDPOINTS

@app.route("/initialize_user", methods=["POST"])
def initialize_user():
    """Initialize a new user with starting tokens"""
    data = request.get_json()
    user_address = data.get("user_address")
    
    if not user_address:
        return jsonify({"error": "User address is required"}), 400
    
    tokens = initialize_user_tokens(user_address)
    return jsonify({
        "user_address": user_address,
        "tokens": tokens,
        "message": f"User initialized with {tokens} tokens"
    })

@app.route("/get_user_balance/<user_address>", methods=["GET"])
def get_user_balance(user_address):
    """Get current token balance for a user"""
    tokens = get_user_tokens(user_address)
    return jsonify({
        "user_address": user_address,
        "tokens": tokens
    })

@app.route("/start_quiz", methods=["POST"])
def start_quiz():
    """Start a new quiz session for a user"""
    data = request.get_json()
    user_address = data.get("user_address")
    
    if not user_address:
        return jsonify({"error": "User address is required"}), 400
    
    # Initialize user if not exists
    initialize_user_tokens(user_address)
    
    # Create quiz session
    session_id = f"{user_address}_{datetime.now().timestamp()}"
    user_sessions[session_id] = {
        "user_address": user_address,
        "questions": random.sample(QUIZ_QUESTIONS, min(5, len(QUIZ_QUESTIONS))),
        "current_question": 0,
        "correct_answers": 0,
        "total_questions": min(5, len(QUIZ_QUESTIONS)),
        "started_at": datetime.now().isoformat()
    }
    
    return jsonify({
        "session_id": session_id,
        "total_questions": user_sessions[session_id]["total_questions"],
        "message": "Quiz session started successfully"
    })

@app.route("/get_question/<session_id>", methods=["GET"])
def get_question(session_id):
    """Get current question for a quiz session"""
    if session_id not in user_sessions:
        return jsonify({"error": "Invalid session ID"}), 400
    
    session = user_sessions[session_id]
    
    if session["current_question"] >= len(session["questions"]):
        return jsonify({"error": "Quiz completed"}), 400
    
    current_q = session["questions"][session["current_question"]]
    
    return jsonify({
        "question_number": session["current_question"] + 1,
        "total_questions": session["total_questions"],
        "question": current_q["question"],
        "options": current_q["options"]
    })

@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    """Submit answer for current question"""
    data = request.get_json()
    session_id = data.get("session_id")
    answer = data.get("answer")  # 0-based index
    
    if session_id not in user_sessions:
        return jsonify({"error": "Invalid session ID"}), 400
    
    if answer is None:
        return jsonify({"error": "Answer is required"}), 400
    
    session = user_sessions[session_id]
    current_q = session["questions"][session["current_question"]]
    
    is_correct = answer == current_q["correct_answer"]
    tokens_earned = 0
    
    if is_correct:
        session["correct_answers"] += 1
        tokens_earned = TOKENS_PER_CORRECT_ANSWER
        add_tokens(session["user_address"], tokens_earned)
    
    session["current_question"] += 1
    
    # Check if quiz is completed
    quiz_completed = session["current_question"] >= len(session["questions"])
    
    response = {
        "correct": is_correct,
        "correct_answer": current_q["correct_answer"],
        "tokens_earned": tokens_earned,
        "total_tokens": get_user_tokens(session["user_address"]),
        "quiz_completed": quiz_completed
    }
    
    if quiz_completed:
        response.update({
            "final_score": f"{session['correct_answers']}/{session['total_questions']}",
            "total_tokens_earned": session["correct_answers"] * TOKENS_PER_CORRECT_ANSWER,
            "can_mint_nft": get_user_tokens(session["user_address"]) >= MINIMUM_TOKENS_FOR_NFT
        })
    
    return jsonify(response)

@app.route("/quiz_summary/<session_id>", methods=["GET"])
def quiz_summary(session_id):
    """Get quiz session summary"""
    if session_id not in user_sessions:
        return jsonify({"error": "Invalid session ID"}), 400
    
    session = user_sessions[session_id]
    user_address = session["user_address"]
    current_tokens = get_user_tokens(user_address)
    
    return jsonify({
        "session_id": session_id,
        "user_address": user_address,
        "correct_answers": session["correct_answers"],
        "total_questions": session["total_questions"],
        "tokens_earned": session["correct_answers"] * TOKENS_PER_CORRECT_ANSWER,
        "current_total_tokens": current_tokens,
        "can_mint_nft": current_tokens >= MINIMUM_TOKENS_FOR_NFT,
        "tokens_needed_for_nft": max(0, MINIMUM_TOKENS_FOR_NFT - current_tokens)
    })

# MODIFIED NFT MINTING ENDPOINTS

@app.route("/check_nft_eligibility/<user_address>", methods=["GET"])
def check_nft_eligibility(user_address):
    """Check if user is eligible to mint NFT"""
    current_tokens = get_user_tokens(user_address)
    eligible = current_tokens >= MINIMUM_TOKENS_FOR_NFT
    
    return jsonify({
        "eligible": eligible,
        "current_tokens": current_tokens,
        "required_tokens": MINIMUM_TOKENS_FOR_NFT,
        "tokens_needed": max(0, MINIMUM_TOKENS_FOR_NFT - current_tokens)
    })

@app.route("/mintBadge", methods=["POST"])
def mintBadge():
    """Modified mint badge function with token validation"""
    data = request.get_json()
    badge_type = data.get("badge_type")
    token_uri = data.get("token_uri")
    recipient = data.get("recipient")
    user_address = data.get("user_address")  # Added user address for token validation

    if not all([badge_type, token_uri, recipient, user_address]):
        return jsonify({"error": "Missing required fields"}), 400

    # Check token eligibility
    current_tokens = get_user_tokens(user_address)
    if current_tokens < MINIMUM_TOKENS_FOR_NFT:
        return jsonify({
            "error": f"Insufficient tokens. You have {current_tokens} tokens, need {MINIMUM_TOKENS_FOR_NFT}",
            "tokens_needed": MINIMUM_TOKENS_FOR_NFT - current_tokens
        }), 400

    try:
        # Deduct tokens for minting
        if not deduct_tokens(user_address, MINIMUM_TOKENS_FOR_NFT):
            return jsonify({"error": "Failed to deduct tokens"}), 400

        nonce = get_nonce(accountAddress)
        txn = contract.functions.mintBadge(recipient, badge_type, token_uri).build_transaction({
            "from": accountAddress,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": web3.to_wei("2", "gwei")
        })

        signed_txn = web3.eth.account.sign_transaction(txn, private_key=privateKey)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        return jsonify({
            "tx_hash": web3.to_hex(tx_hash),
            "tokens_deducted": MINIMUM_TOKENS_FOR_NFT,
            "remaining_tokens": get_user_tokens(user_address),
            "message": "NFT minted successfully!"
        })
    except Exception as e:
        # Refund tokens if minting failed
        add_tokens(user_address, MINIMUM_TOKENS_FOR_NFT)
        return jsonify({"error": str(e)}), 400

@app.route("/uploadMetadata", methods=["POST"])  
def upload_metadata():
    """Modified metadata upload with token validation"""
    data = request.json
    required_fields = ["student_name", "class_semester", "university", "badge_type", "user_address"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    user_address = data["user_address"]
    
    # Check token eligibility before processing
    current_tokens = get_user_tokens(user_address)
    if current_tokens < MINIMUM_TOKENS_FOR_NFT:
        return jsonify({
            "error": f"Insufficient tokens for NFT minting. You have {current_tokens} tokens, need {MINIMUM_TOKENS_FOR_NFT}",
            "tokens_needed": MINIMUM_TOKENS_FOR_NFT - current_tokens
        }), 400

    student_name = data["student_name"]
    class_semester = data["class_semester"]
    university = data["university"]
    badge_type = data["badge_type"]
    now = datetime.now()
    grant_date = now.strftime("%Y-%m-%d")

    # Upload static image
    baseDir = Path(__file__).parent.resolve()
    imageFileName = f"{badge_type}.PNG"
    image_path = imageFileName
    
    if not os.path.isfile(image_path):
        return jsonify({"error": f"Image for badge type '{badge_type}' not found."}), 400
    
    # Upload Certificate PNG file to Pinata
    image_cid = uploadFileToPinata(filePath=str(image_path), name=str(image_path), keyValues={"category": "Badge"})

    image_url = f"https://gateway.pinata.cloud/ipfs/{image_cid['cid']}"
    s = pyshorteners.Shortener()
    short_url = s.tinyurl.short(image_url)

    pinContent = {
        "image_cid": image_cid['cid'],
        "certificate_url": short_url,
        "attributes": [
            {"Student": student_name},
            {"Class": class_semester},
            {"University": university},
            {"Date": grant_date},
            {"Badge Type": badge_type},
            {"Tokens Used": MINIMUM_TOKENS_FOR_NFT}
        ]
    }
    
    metadata = {
        "pinataMetadata": {"name": f"{student_name}-{badge_type}"},
        "pinataContent": pinContent
    }

    # Upload metadata JSON to Pinata
    metaDataCid = uploadMetadataToPinata(metadata)
    metadataURL = f"https://gateway.pinata.cloud/ipfs/{metaDataCid}"
    
    # Save to local JSON log
    record = {
        "student_name": student_name,
        "class_semester": class_semester, 
        "university": university,
        "badge_type": badge_type,
        "grant_date": grant_date,
        "metadata_uri": metadataURL,
        "user_address": user_address,
        "tokens_used": MINIMUM_TOKENS_FOR_NFT
    }

    local_log_path = STUDENT_BADGE_DATA
    if os.path.exists(local_log_path):
        with open(local_log_path, "r") as f:
            badge_data = json.load(f)
    else:
        badge_data = []

    badge_data.append(record)

    with open(local_log_path, "w") as f:
        json.dump(badge_data, f, indent=2)

    return jsonify({"metadata_uri": metadataURL}), 200

# EXISTING ENDPOINTS (unchanged)
@app.route("/canmint/<badge_type>", methods=["GET"])
def canMint(badge_type):
    try:
        result = contract.functions.canMintBadge(badge_type).call()
        minted = contract.functions.getMintedCount(badge_type).call()
        cap = contract.functions.badgeTypes(badge_type).call()[1]
        return jsonify({
            "can_mint": result,
            "minted": minted,
            "cap": cap
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/getMintedCount/<badge_type>", methods=["GET"])
def mintedCount(badge_type):
    try:
        count = contract.functions.getMintedCount(badge_type).call()
        return jsonify({"minted_count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/list_minted_badges", methods=["GET"])
def list_minted_badges():
    metadata_uris = []
    try:
        latest_id = contract.functions.totalSupply().call()  
        if latest_id <= 0:
            return jsonify([]), 200
        for token_id in range(1, latest_id + 1):
            metadata_uri = contract.functions.tokenURI(token_id).call()
            metadata_uris.append(metadata_uri)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    results = []
    for metadata_uri in metadata_uris:
        try:
            response = requests.get(metadata_uri)
            if response.status_code != 200:
                continue
            badge_data = response.json()
            certificate_url = badge_data.get('certificate_url', 'N/A')
            attributes = badge_data.get("attributes", [])
            student_collection = {
                list(attr.keys())[0]: list(attr.values())[0] for attr in attributes
            }
            badge_info = OrderedDict([
                ("Student Name", student_collection.get("Student", "N/A")),
                ("Badge Grant Date", student_collection.get("Date", "N/A")),
                ("Badge Type", student_collection.get("Badge Type", "N/A")),
                ("Class or Semester", student_collection.get("Class", "N/A")),
                ("University", student_collection.get("University", "N/A")),
                ("Certificate URL", certificate_url),
                ("Tokens Used", student_collection.get("Tokens Used", "N/A"))
            ])
            results.append(badge_info)
        except Exception as e:
            continue
        
    return jsonify(results), 200

if __name__ == "__main__":
    app.run(debug=True)