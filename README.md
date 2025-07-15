
# 🧠 BeyondChats - Reddit Digital Persona Analyzer

Transform any Reddit user's public activity into a detailed digital personality profile. This AI-powered app scrapes user content and uses advanced LLMs (via **Groq API**) to analyze tone, interests, beliefs, and communication style — all within a secure, beautifully designed **Streamlit interface**.

---

## 🚀 Features

- 🔍 Scrape posts & comments from any Reddit profile
- 🧠 Analyze user behavior and generate deep persona insights
- 💬 Include real quotes and post/comment citations
- 🤖 Choose between powerful LLMs (LLaMA 3, Mixtral) via **Groq API**
- 🌐 Modern **Streamlit UI** with profile preview and download
- 💻 Optional command-line mode for automation
- 🔐 Secure API key masking using `.env` or `st.secrets`

---

## 📁 Project Structure

```
BEYONDCHATS-REDDIT-USER-PERSONA/
├── output/                    # Folder where generated reports are saved
├── .env                       # Your secret API keys (not committed)
├── .gitignore                 # Ignores .env and other system files
├── README.md                  # Project documentation (this file)
├── reddit_persona.py          # Main Streamlit + CLI app
├── requirements.txt           # Required Python packages
└── bcenv/ (optional)  # Local virtual environment
```

---

## 🔑 API Setup

This app uses 3 keys:

| API        | Variable Name        | How to Get It |
|------------|----------------------|----------------|
| Reddit     | `REDDIT_CLIENT_ID`   | https://www.reddit.com/prefs/apps |
| Reddit     | `REDDIT_CLIENT_SECRET` | Same as above |
| Groq (LLMs)| `GROQ_API_KEY`       | https://console.groq.com |

### 📝 Create `.env` file:

```env
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
GROQ_API_KEY=your_groq_api_key
```

> ✅ Don’t commit this file! Already excluded by `.gitignore`.

---

## 📦 Installation

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/beyondchats-reddit-user-persona.git
cd beyondchats-reddit-user-persona

# 2. Create virtual environment (optional but recommended)
python -m venv bcenv
source bcenv/bin/activate  # or bcenvironment\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your keys to a .env file as described above
```

---

## 🌐 Run the Streamlit App

```bash
streamlit run reddit_persona.py
```

Then:
- Paste any Reddit profile URL  
- Choose how many posts/comments to analyze  
- Select an LLM model  
- View the persona, and download as `.txt` or `.json`

---

## 💻 Run via Command Line

```bash
python reddit_persona.py --url https://www.reddit.com/user/kojied/ --depth 100 --model llama3-70b-8192
```

### CLI Options:

| Flag         | Description                                      |
|--------------|--------------------------------------------------|
| `--url`      | Reddit profile URL (required)                    |
| `--depth`    | Number of posts/comments to analyze (default: 100) |
| `--model`    | LLM model: `llama3-70b-8192`, `llama3-8b-8192`, `mixtral-8x7b-32768` |
| `--output`   | Output directory (default: `output/`)            |

---

## 📤 Output Example

After running, results are saved under the `/output` folder:

```
output/
├── kojied_digital_profile.txt       # Persona in readable format
└── kojied_profile_data.json         # Raw data and analysis stats
```

Each report includes:
- 🎯 Core Interests
- 🧠 Personality Traits
- 💬 Writing Style & Tone
- 💭 Values & Beliefs
- 📱 Reddit Engagement Pattern
- 📌 Quotes with comment/post IDs

---

## 🧠 Supported AI Models via Groq

| Model                | Description                            |
|----------------------|----------------------------------------|
| `llama3-70b-8192`    | Deepest insights, best quality         |
| `llama3-8b-8192`     | Balanced, faster                       |
| `mixtral-8x7b-32768` | Wide context, scalable                 |

---

## 🧪 Sample Reddit Users to Try

- https://www.reddit.com/user/kojied/
- https://www.reddit.com/user/Hungry-Move-6603/

---

## 📊 Best Practices

- Choose profiles with rich Reddit activity  
- Higher content limits yield deeper insights  
- Don’t over-query Groq (respect rate limits)  
- Only use public Reddit data (respect privacy)

---

## 🔒 Security Notes

- No keys are hardcoded  
- `.env` is excluded from git via `.gitignore`  
- Safe to deploy with `st.secrets` in Streamlit Cloud

---

## 🧑‍💻 Author

**Devik Shah**  
📬 devikshah2073@gmail.com  
🌐 [LinkedIn](https://linkedin.com/in/devik-shah)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Contributing

Feel free to submit PRs, file issues, or request features. Let’s improve it together!

---
