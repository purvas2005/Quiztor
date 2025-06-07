# 🪙 Student NFT Badges Project (Solidity + Python)

This is a v0 of full-stack blockchain project that uses **Solidity** to define a ERC 721 NFT Token to create and grant Badges to Students, **Hardhat** for smart contract deployment/testing, **Flask** for backend APIs, and **Streamlit** for a simple UI.
This is developed as an introduction to Blockchain for Students (at **PES University**) who have no or limited knowledge yet of Blockchain and would like to use a small experimental Smart Contract to get a quick understanding of using Solidity and wrap it in an API layer and access it via a UI Client.

---

## 🔗 References

## https://hardhat.org/tutorial

---

## 📁 Project Structure

```
.
├── Solidity/       # Smart contract and Hardhat project
├── Python/         # Flask API and Streamlit UI
└── README.md       # This file
```

---

## 🛠 Prerequisites

Make sure you have the following installed:

- Node.js + npm
- Python 3.8+
- Git
- Metamask (optional, for public testnets. This code does not yet use Metamask)

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/StudentNFT.git
cd StudentNFT
```

---

### 2. ⚙️ Run the Solidity/Hardhat Project

# Navigate to the Solidity folder

```bash
cd Solidity
npm install
npx hardhat node          # Starts local blockchain with 20 test accounts
npx hardhat ignition deploy ./ignition/modules/StudentNFT.js --network localhost
```

This deploys the NFT Token contract to a local blockchain and assigns all tokens to the first account.

---

### 3. 🧪 Run Tests (Optional)

```bash
npx hardhat test
```

---

### 4. 🔗 Run the Flask API

```bash
cd ../Python
pip install -r requirements.txt
python StudentNFTAPI.py
```

This starts a local API server at `http://localhost:5000` with endpoints like:

- `POST /init`
- `POST /transfer`
- `GET /balance/<address>`

---

### 5. 💻 Launch the Streamlit Frontend

In a new terminal:

```bash
cd StudentNFT/Python/UI
streamlit run StudentNFTAdmin.py
```

This opens a UI where you can:

- View the Total number of granted Student Badges based on Badge Type
- Mint New Student Badges based on the choice of Badge Type. A dummy set of Students has been added.
- View details of each granted Badge and ability to navigate to the Badge Certificate

---

## 🔐 Security Notes

- This project uses test accounts and private keys only for **local testing**
- Never use real private keys or deploy this setup to mainnet without proper key management

---

## 🙋‍♂️ Need Help?

If you encounter issues:

- Check your `.env` or `StudentNFTAPI.py` values for correct addresses
- Ensure Hardhat node is running before launching Flask or Streamlit
- Make sure `Token.sol` is compiled and deployed

---

## 📃 License

This project is open source and intended for learning and prototyping purposes.
_Last updated by rdeshmukh73 on 2026-06-01_
