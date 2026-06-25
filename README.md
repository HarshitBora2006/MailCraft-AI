# 📧 MailCraft AI

AI-powered Email and Letter Generator for students and job seekers with smart templates and PDF export.

---

## ✨ Overview

MailCraft AI is an intelligent email and letter generation tool that helps users instantly create professional, personalized emails using simple inputs. It is designed to save time and improve communication efficiency using Generative AI.

---

## 🚀 Features

- ✨ Generate professional emails instantly  
- 🧠 AI-powered content generation  
- 📝 Custom tone selection (formal, casual, friendly, etc.)  
- 📌 Easy input form for quick email creation  
- 📄 Copy or download generated emails (PDF export support)  
- ⚡ Fast and responsive UI  

---

## 🛠️ Tech Stack

**Frontend:**
- HTML
- CSS
- JavaScript (or React if used)

**Backend:**
- Node.js / Express (or Python backend if applicable)

**AI Integration:**
- OpenAI API / Any LLM API

**Others:**
- REST API
- dotenv for environment variables

---

## 📁 Project Structure

MailCraft-AI/

│

├── backend/

│   ├── main.py

│   ├── requirement.txt

│   ├── .env (not included in repo)

│
├── frontend/

│   ├── index.html

└── README.md

⚙️ Installation & Setup

1. Clone the repository
   
     git clone https://github.com/HarshitBora2006/mail-generator.git
     cd mail-generator

2. Install dependencies

      npm install

3. Setup environment variables

    Create a .env file in the backend folder:

      OPENAI_API_KEY=your_api_key_here

      PORT=5000

4. Run the project
   
    Backend
   
      cd backend
   
      node server.js
   
    Frontend

      Open index.html in browser or use Live Server.

📌 Usage

Enter recipient details or context

Select email tone

Click Generate Email

Copy or download your generated email

🔐 Security Note

Never upload .env file to GitHub

API keys must remain private

Add .env to .gitignore

🧠 Future Improvements

Email templates library

Login system

Save email history

Multi-language support (Hindi + English)

Gmail direct integration

🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first.

📄 License

This project is open-source and available under the MIT License.

💡 Author

Built with ❤️ by Harshit Bora
