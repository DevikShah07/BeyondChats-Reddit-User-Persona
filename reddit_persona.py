import argparse
import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import praw
import requests
import streamlit as st
from groq import Groq

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  dotenv not installed. Using direct environment variables or Streamlit secrets.")

# Access API Keys from environment or Streamlit secrets
def get_api_key(key_name: str) -> str:
    """Get API key from environment variables or Streamlit secrets."""
    # Try environment variables first
    value = os.getenv(key_name)
    if value:
        return value
    
    # Try Streamlit secrets if available
    try:
        return st.secrets[key_name]
    except:
        pass
    
    # Return None if not found
    return None

REDDIT_CLIENT_ID = get_api_key("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = get_api_key("REDDIT_CLIENT_SECRET")
GROQ_API_KEY = get_api_key("GROQ_API_KEY")


class RedditScraper:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
    
    def extract_username_from_url(self, url: str) -> str:
        patterns = [
            r'reddit\.com/u/([^/]+)',
            r'reddit\.com/user/([^/]+)',
            r'reddit\.com/users/([^/]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Invalid Reddit URL format: {url}")
    
    def scrape_user_data(self, username: str, limit: int = 100) -> Dict:
        try:
            user = self.reddit.redditor(username)
            
            # Check if user exists
            if not hasattr(user, 'id'):
                try:
                    _ = user.id
                except:
                    raise ValueError(f"User '{username}' not found or suspended")
            
            posts = []
            comments = []
            
            # Scrape submissions (posts)
            try:
                for submission in user.submissions.new(limit=limit):
                    posts.append({
                        'id': submission.id,
                        'title': submission.title,
                        'selftext': submission.selftext,
                        'subreddit': str(submission.subreddit),
                        'score': submission.score,
                        'created_utc': submission.created_utc,
                        'url': f"https://reddit.com{submission.permalink}"
                    })
            except Exception as e:
                print(f"Error scraping posts: {e}")
            
            # Scrape comments
            try:
                for comment in user.comments.new(limit=limit):
                    comments.append({
                        'id': comment.id,
                        'body': comment.body,
                        'subreddit': str(comment.subreddit),
                        'score': comment.score,
                        'created_utc': comment.created_utc,
                        'url': f"https://reddit.com{comment.permalink}"
                    })
            except Exception as e:
                print(f"Error scraping comments: {e}")
            
            return {
                'username': username,
                'posts': posts,
                'comments': comments,
                'total_posts': len(posts),
                'total_comments': len(comments)
            }
            
        except Exception as e:
            raise Exception(f"Error scraping user data: {e}")


class PersonaGenerator:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.model = "llama3-70b-8192"
    
    def generate_persona(self, user_data: Dict) -> str:
        # Prepare content for analysis
        content = self._prepare_content(user_data)
        
        prompt = f"""
        Analyze the following Reddit user data and create a comprehensive digital personality profile.
        
        User: {user_data['username']}
        Total Posts: {user_data['total_posts']}
        Total Comments: {user_data['total_comments']}
        
        Content to analyze:
        {content}
        
        Please create a detailed profile with the following structure:
        
        Reddit Username: {user_data['username']}
        ==========================================
        
        🎯 Core Interests & Passions:
        - List specific interests with supporting evidence
        - Format: Interest (Evidence: "exact quote" - Source: Post/Comment ID)
        
        🧠 Personality Insights:
        - Identify key personality traits with behavioral evidence
        - Format: Trait (Evidence: "exact quote" - Source: Post/Comment ID)
        
        ✍️ Communication Style:
        - Analyze writing patterns and tone
        - Format: Style element (Evidence: "exact quote" - Source: Post/Comment ID)
        
        💭 Core Values & Perspectives:
        - Identify fundamental beliefs and viewpoints
        - Format: Value/Belief (Evidence: "exact quote" - Source: Post/Comment ID)
        
        📱 Digital Behavior Patterns:
        - Examine Reddit engagement and interaction style
        - Format: Behavior (Evidence: "exact quote" - Source: Post/Comment ID)
        
        Guidelines:
        - Use direct quotes from the analyzed content
        - Include specific post/comment IDs for verification
        - Keep quotes meaningful but concise
        - Provide concrete evidence for each insight
        - Maintain objectivity and professionalism
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert digital behavioral analyst specializing in creating comprehensive user personas from social media data. You analyze communication patterns, interests, and behavioral indicators to build accurate psychological profiles."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=4000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Error generating persona: {e}")
    
    def _prepare_content(self, user_data: Dict) -> str:
        content = []
        
        # Add posts
        for post in user_data['posts'][:50]:  # Limit to avoid token limits
            if post['title'] and post['selftext']:
                content.append(f"POST [{post['id']}]: {post['title']} - {post['selftext'][:500]}")
            elif post['title']:
                content.append(f"POST [{post['id']}]: {post['title']}")
        
        # Add comments
        for comment in user_data['comments'][:50]:  # Limit to avoid token limits
            if comment['body'] and len(comment['body']) > 10:
                content.append(f"COMMENT [{comment['id']}]: {comment['body'][:500]}")
        
        return "\n\n".join(content)


class PersonaFileManager:
    @staticmethod
    def ensure_output_directory() -> str:
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        return output_dir
    
    @staticmethod
    def save_persona(persona: str, username: str) -> str:
        output_dir = PersonaFileManager.ensure_output_directory()
        filename = f"{username}_digital_profile.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(persona)
            f.write(f"\n\nProfile Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return filepath


def streamlit_app():
    st.set_page_config(
        page_title="Reddit Digital Persona Analyzer",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for modern design
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        margin: 0;
    }
    .status-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .feature-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        color: #2c3e50;
    }
    .feature-card h4 {
        color: #495057;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    .feature-card p {
        color: #6c757d;
        margin: 0;
        line-height: 1.5;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 15px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🧠 Reddit Digital Persona Analyzer</h1>
        <p>Transform Reddit profiles into comprehensive digital personality insights using advanced AI analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for configuration
    st.sidebar.markdown("## ⚙️ Analysis Configuration")
    
    # Advanced settings
    st.sidebar.markdown("### 📊 Data Collection")
    scrape_limit = st.sidebar.slider(
        "Content Analysis Depth",
        min_value=10,
        max_value=500,
        value=500,
        help="Number of posts/comments to analyze for deeper insights"
    )
    
    model_choice = st.sidebar.selectbox(
        "AI Analysis Model",
        ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"],
        index=0,
        help="Choose AI model for personality analysis"
    )
    
    # API Configuration
    st.sidebar.markdown("### 🔑 API Configuration")
    
    # Check if API keys are configured
    reddit_configured = REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET
    groq_configured = GROQ_API_KEY
    
    if not reddit_configured:
        st.sidebar.error("⚠️ Reddit API keys not configured")
        with st.sidebar.expander("Configure Reddit API"):
            st.markdown("""
            1. Go to https://www.reddit.com/prefs/apps
            2. Create a new app (script type)
            3. Set environment variables:
               - `REDDIT_CLIENT_ID`
               - `REDDIT_CLIENT_SECRET`
            """)
    
    if not groq_configured:
        st.sidebar.error("⚠️ Groq API key not configured")
        with st.sidebar.expander("Configure Groq API"):
            st.markdown("""
            1. Go to https://console.groq.com
            2. Create an API key
            3. Set environment variable:
               - `GROQ_API_KEY`
            """)
    
    # Connection status
    st.sidebar.markdown("### 🔗 System Status")
    reddit_status = "🟢 Connected" if reddit_configured else "🔴 Not Configured"
    groq_status = "🟢 Ready" if groq_configured else "🔴 Not Configured"
    
    st.sidebar.markdown(f"""
    <div class="status-card">
        <strong>System Status</strong><br>
        Reddit API: {reddit_status}<br>
        Groq AI: {groq_status}
    </div>
    """, unsafe_allow_html=True)
    
    # Main interface
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### 🎯 Profile Analysis")
        reddit_url = st.text_input(
            "Enter Reddit Profile URL",
            placeholder="https://www.reddit.com/user/username/",
            help="Paste the complete Reddit user profile URL here"
        )
        
        if st.button("🚀 Analyze Digital Persona", type="primary", use_container_width=True):
            if not reddit_url:
                st.error("⚠️ Please provide a valid Reddit profile URL to begin analysis.")
                return
            
            # Check API configuration
            if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
                st.error("🔑 Reddit API credentials not configured. Please check the sidebar for setup instructions.")
                return
            
            if not GROQ_API_KEY:
                st.error("🔑 Groq API key not configured. Please check the sidebar for setup instructions.")
                return
            
            try:
                # Enhanced progress tracking
                progress_container = st.container()
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Initialize scraper
                    status_text.markdown("🔄 **Initializing Reddit data collector...**")
                    progress_bar.progress(15)
                    
                    scraper = RedditScraper(
                        client_id=REDDIT_CLIENT_ID,
                        client_secret=REDDIT_CLIENT_SECRET,
                        user_agent="DigitalPersonaAnalyzer/2.0"
                    )
                    
                    # Extract username
                    username = scraper.extract_username_from_url(reddit_url)
                    status_text.markdown(f"👤 **Target identified:** u/{username}")
                    progress_bar.progress(25)
                    
                    # Scrape data
                    status_text.markdown("📥 **Collecting digital footprint data...**")
                    user_data = scraper.scrape_user_data(username, limit=scrape_limit)
                    progress_bar.progress(50)
                    
                    # Generate persona
                    status_text.markdown("🧠 **Performing AI personality analysis...**")
                    generator = PersonaGenerator(GROQ_API_KEY)
                    generator.model = model_choice
                    
                    # Test API connection
                    test_response = generator.client.chat.completions.create(
                        model=model_choice,
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=1
                    )
                    
                    persona = generator.generate_persona(user_data)
                    progress_bar.progress(75)
                    
                    # Save file
                    status_text.markdown("💾 **Generating downloadable report...**")
                    filepath = PersonaFileManager.save_persona(persona, username)
                    progress_bar.progress(100)
                    
                    status_text.markdown("✅ **Analysis complete! Digital persona ready.**")
                
                # Success message
                st.success(f"🎉 Successfully analyzed digital persona for **u/{username}**")
                st.info(f"📁 Report saved as: `{filepath}`")
                
                # Display persona in expandable section
                with st.expander("📄 View Complete Digital Profile", expanded=True):
                    st.text_area(
                        "Digital Persona Analysis",
                        value=persona,
                        height=450,
                        disabled=True
                    )
                
                # Enhanced download options
                col_download1, col_download2 = st.columns(2)
                with col_download1:
                    st.download_button(
                        label="📥 Download Full Report",
                        data=persona,
                        file_name=f"{username}_digital_profile.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with col_download2:
                    # Create JSON export
                    json_data = {
                        "username": username,
                        "analysis_date": datetime.now().isoformat(),
                        "persona": persona,
                        "stats": {
                            "posts_analyzed": user_data['total_posts'],
                            "comments_analyzed": user_data['total_comments'],
                            "model_used": model_choice
                        }
                    }
                    st.download_button(
                        label="📊 Export as JSON",
                        data=json.dumps(json_data, indent=2),
                        file_name=f"{username}_profile_data.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                # Enhanced statistics display
                st.markdown("### 📊 Analysis Metrics")
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.metric("📝 Posts Analyzed", user_data['total_posts'])
                with metric_col2:
                    st.metric("💬 Comments Analyzed", user_data['total_comments'])
                with metric_col3:
                    st.metric("🎯 Total Data Points", user_data['total_posts'] + user_data['total_comments'])
                with metric_col4:
                    st.metric("🤖 AI Model", model_choice.split('-')[0].upper())
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                if "api_key" in str(e).lower():
                    st.error("🔑 Invalid Groq API credentials. Please verify your configuration.")
                elif "rate_limit" in str(e).lower():
                    st.error("⏱️ Rate limit reached. Please wait before retrying.")
                elif "not found" in str(e).lower():
                    st.error("👻 Reddit user not found or profile is private/suspended.")
    
    with col2:
        st.markdown("### 💡 How It Works")
        st.markdown("""
        <div class="feature-card">
            <h4>🔍 Data Collection</h4>
            <p>Securely extracts public posts and comments from Reddit profiles</p>
        </div>
        
        <div class="feature-card">
            <h4>🧠 AI Analysis</h4>
            <p>Advanced language models analyze communication patterns and interests</p>
        </div>
        
        <div class="feature-card">
            <h4>📊 Profile Generation</h4>
            <p>Creates comprehensive digital personality insights with evidence</p>
        </div>
        
        <div class="feature-card">
            <h4>📥 Export Options</h4>
            <p>Download detailed reports in multiple formats</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### ⚡ AI Models Available")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; color: #2c3e50;">
        <strong style="color: #495057;">Llama3-70B</strong> - Premium analysis with deep insights<br>
        <strong style="color: #495057;">Llama3-8B</strong> - Fast processing for quick results<br>
        <strong style="color: #495057;">Mixtral-8x7B</strong> - Balanced performance and accuracy
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 Best Practices")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 1rem; border-radius: 8px; color: #2c3e50;">
        • Use profiles with substantial activity<br>
        • Higher content limits yield better insights<br>
        • Try different models for varied perspectives<br>
        • Respect user privacy and terms of service
        </div>
        """, unsafe_allow_html=True)


def command_line_interface():
    """Enhanced command line interface for the persona analyzer."""
    
    parser = argparse.ArgumentParser(
        description="Analyze Reddit user digital personas using advanced AI models"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Reddit profile URL (e.g., https://www.reddit.com/user/username/)"
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=100,
        help="Analysis depth - number of posts/comments to analyze (default: 100)"
    )
    parser.add_argument(
        "--model",
        default="llama3-70b-8192",
        choices=["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"],
        help="AI model for analysis (default: llama3-70b-8192)"
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Output directory for generated profiles (default: output)"
    )
    
    args = parser.parse_args()
    
    try:
        print("🧠 Digital Persona Analyzer v2.0")
        print("=" * 40)
        print("🔄 Initializing Reddit data collector...")
        
        scraper = RedditScraper(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent="DigitalPersonaAnalyzer/2.0"
        )
        
        print("👤 Extracting user identity...")
        username = scraper.extract_username_from_url(args.url)
        print(f"✅ Target identified: u/{username}")
        
        print("📥 Collecting digital footprint...")
        user_data = scraper.scrape_user_data(username, limit=args.depth)
        print(f"✅ Collected {user_data['total_posts']} posts and {user_data['total_comments']} comments")
        
        print(f"🧠 Performing AI analysis with {args.model}...")
        generator = PersonaGenerator(GROQ_API_KEY)
        generator.model = args.model
        
        # Test API connection
        test_response = generator.client.chat.completions.create(
            model=args.model,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        
        persona = generator.generate_persona(user_data)
        
        print("💾 Generating profile report...")
        filepath = PersonaFileManager.save_persona(persona, username)
        
        print(f"✅ Digital persona analysis complete!")
        print(f"📁 Report saved: {filepath}")
        
        # Display enhanced preview
        print("\n" + "=" * 60)
        print("DIGITAL PERSONA PREVIEW")
        print("=" * 60)
        preview = persona[:600] + "..." if len(persona) > 600 else persona
        print(preview)
        print("\n" + "=" * 60)
        print(f"📊 Analysis Stats: {user_data['total_posts']} posts, {user_data['total_comments']} comments")
        print(f"🤖 AI Model: {args.model}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        if "api_key" in str(e).lower():
            print("🔑 Invalid Groq API credentials. Please verify your configuration.")
        elif "rate_limit" in str(e).lower():
            print("⏱️ Rate limit exceeded. Please wait before retrying.")
        elif "not found" in str(e).lower():
            print("👻 Reddit user not found or profile is private/suspended.")
        sys.exit(1)


def main():
    # Check if running with Streamlit
    if len(sys.argv) > 1 and sys.argv[1] == "--streamlit":
        streamlit_app()
    elif len(sys.argv) > 1 and "--url" in sys.argv:
        command_line_interface()
    else:
        # Default to Streamlit interface
        print("🚀 Starting Digital Persona Analyzer...")
        print("💡 Run with --url for command line interface")
        print("🌐 Use 'streamlit run reddit_persona.py' for web interface")
        streamlit_app()


if __name__ == "__main__":
    main()