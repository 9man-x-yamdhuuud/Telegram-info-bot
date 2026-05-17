#!/usr/bin/env python3
"""
Leakosint API Telegram Bot - Facebook UID + Instagram Lookup
------------------------------------------------------------
Features:
- Facebook UID lookup (full profile info)
- Instagram username lookup (public info)
- Phone/Email/Name search in breaches
- Paginated results with inline buttons
"""

import requests
import logging
import re
import json
from random import randint
from typing import Dict, List, Optional, Tuple

try:
    import telebot
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
except ImportError:
    print("ERROR: Run: pip install pyTelegramBotAPI requests")
    exit(1)

# ==================== CONFIGURATION ====================
# API Key already added here
API_TOKEN = "8735045882:dGnfJAPg"  # Your Leakosint API token
BOT_TOKEN = ""  # You need to add your Telegram Bot Token from @BotFather
LANG = "ru"
LIMIT = 300
LEAKOSINT_API_URL = "https://leakosintapi.com/"

# Facebook API endpoints (multiple fallbacks)
FACEBOOK_API_URLS = [
    "https://graph.facebook.com/v18.0/{uid}?access_token=6628568379%7Cc1e620fa708a1d5696fb991c1bde5662&fields=id,name,first_name,last_name,email,gender,birthday,location,hometown,relationship_status,about,picture.width(500).height(500),cover,devices,education,work,friends.limit(0),likes.limit(0),posts.limit(0),albums.limit(0),videos.limit(0),groups.limit(0),events.limit(0),music.limit(0),books.limit(0),games.limit(0)",
    "https://findmyfbid.com/api?uid={uid}",
    "https://lookup-id.com/api/?id={uid}"
]

ALLOWED_USER_IDS = []
report_cache: Dict[str, List[str]] = {}

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# ==================== FACEBOOK UID LOOKUP ====================
def fetch_facebook_info(uid: str) -> Optional[Dict]:
    """
    Fetch Facebook profile information using UID.
    Returns dict with profile data or None if not found.
    """
    uid = str(uid).strip()
    
    # Method 1: Try Graph API with public access token
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    # Try multiple API endpoints
    for api_url in FACEBOOK_API_URLS:
        try:
            url = api_url.format(uid=uid)
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data and 'error' not in data:
                    return format_facebook_data(data, uid)
        except:
            continue
    
    # Method 2: Search in Leakosint database for Facebook data
    try:
        payload = {
            "token": API_TOKEN,
            "request": f"facebook.com {uid}",
            "limit": 100,
            "lang": LANG
        }
        response = requests.post(LEAKOSINT_API_URL, json=payload, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if "List" in data:
                for db_name, db_content in data["List"].items():
                    if "facebook" in db_name.lower() or "social" in db_name.lower():
                        entries = db_content.get("Data", [])
                        for entry in entries:
                            if uid in str(entry) or str(uid) in str(entry):
                                return {
                                    "uid": uid,
                                    "found_in_breach": True,
                                    "breach_data": entry,
                                    "source": f"Database: {db_name}",
                                    "data_type": "breach"
                                }
    except:
        pass
    
    # Method 3: Try to get username from UID and fetch info
    try:
        # Convert UID to username via lookup service
        lookup_url = f"https://api.reiyuura.com/api/fb/?id={uid}"
        response = requests.get(lookup_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    "uid": uid,
                    "username": data.get('username', 'N/A'),
                    "name": data.get('name', 'N/A'),
                    "found_in_breach": False,
                    "source": "Public Lookup API"
                }
    except:
        pass
    
    return None

def format_facebook_data(data: dict, uid: str) -> dict:
    """Format Facebook API response into structured data."""
    formatted = {
        "uid": uid,
        "name": data.get('name', 'N/A'),
        "first_name": data.get('first_name', 'N/A'),
        "last_name": data.get('last_name', 'N/A'),
        "email": data.get('email', 'N/A'),
        "gender": data.get('gender', 'N/A'),
        "birthday": data.get('birthday', 'N/A'),
        "relationship": data.get('relationship_status', 'N/A'),
        "about": data.get('about', 'N/A')[:300],
        "location": data.get('location', {}).get('name', 'N/A'),
        "hometown": data.get('hometown', {}).get('name', 'N/A'),
        "profile_url": f"https://facebook.com/{uid}",
        "profile_pic": data.get('picture', {}).get('data', {}).get('url', 'N/A'),
        "cover_photo": data.get('cover', {}).get('source', 'N/A'),
        "education": [],
        "work": [],
        "found_in_breach": False
    }
    
    # Parse education
    if 'education' in data:
        for edu in data['education'][:3]:
            school = edu.get('school', {}).get('name', 'N/A')
            year = edu.get('year', {}).get('name', '')
            formatted['education'].append(f"{school} ({year})" if year else school)
    
    # Parse work
    if 'work' in data:
        for job in data['work'][:3]:
            employer = job.get('employer', {}).get('name', 'N/A')
            position = job.get('position', {}).get('name', '')
            formatted['work'].append(f"{position} at {employer}" if position else employer)
    
    return formatted

def create_facebook_report(fb_data: dict, uid: str) -> str:
    """Create formatted report from Facebook data."""
    if not fb_data:
        return f"""
❌ <b>Facebook UID {uid} not found!</b>

💡 <b>Possible reasons:</b>
• Account is private/deleted
• Invalid UID format
• Account doesn't exist

📝 <b>Tips:</b>
• Make sure UID is numeric (e.g., 1000123456789)
• Try searching with full name instead
• Account might be restricted in your region
"""
    
    # If found in breach database
    if fb_data.get('found_in_breach'):
        return f"""
🔐 <b>Facebook UID: {uid}</b>
⚠️ <b>⚠️ FOUND IN DATA BREACH! ⚠️</b>

📋 <b>Breached Information:</b>
<pre>{json.dumps(fb_data.get('breach_data', {}), indent=2, ensure_ascii=False)[:1000]}</pre>

<b>Source:</b> {fb_data.get('source', 'Unknown')}
<b>Risk Level:</b> HIGH - Change your password immediately!
"""
    
    # Normal Facebook profile info
    report = f"""
📘 <b>Facebook Profile Information</b>
━━━━━━━━━━━━━━━━━━━━━━

<b>🆔 UID:</b> <code>{fb_data['uid']}</code>
<b>👤 Name:</b> {fb_data['name']}
<b>📛 First Name:</b> {fb_data['first_name']}
<b>📛 Last Name:</b> {fb_data['last_name']}

<b>⚧ Gender:</b> {fb_data['gender']}
<b>🎂 Birthday:</b> {fb_data['birthday']}
<b>💑 Relationship:</b> {fb_data['relationship']}

<b>📍 Location:</b> {fb_data['location']}
<b>🏠 Hometown:</b> {fb_data['hometown']}

<b>📧 Email:</b> {fb_data['email']}
"""
    
    if fb_data.get('education'):
        report += f"\n<b>🎓 Education:</b>\n"
        for edu in fb_data['education']:
            report += f"  • {edu}\n"
    
    if fb_data.get('work'):
        report += f"\n<b>💼 Work:</b>\n"
        for job in fb_data['work']:
            report += f"  • {job}\n"
    
    if fb_data['about'] != 'N/A':
        report += f"\n<b>📝 About:</b>\n{fb_data['about']}\n"
    
    report += f"""
━━━━━━━━━━━━━━━━━━━━━━
<b>🔗 Profile Link:</b>
<a href='{fb_data['profile_url']}'>{fb_data['profile_url']}</a>
"""
    
    return report

# ==================== INSTAGRAM LOOKUP ====================
def fetch_instagram_info(username: str) -> Optional[Dict]:
    """
    Fetch public Instagram profile information.
    """
    username = username.strip().lstrip('@').lower()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    # Try Instagram Graph API
    try:
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            user_data = data.get('data', {}).get('user', {})
            if user_data:
                return format_instagram_data(user_data, username)
    except:
        pass
    
    # Try alternative endpoints
    alt_urls = [
        f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}",
        f"https://www.instagram.com/{username}/?__a=1&__d=1"
    ]
    
    for url in alt_urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'graphql' in data:
                        user_data = data['graphql']['user']
                        return format_instagram_data(user_data, username)
                    elif 'user' in data:
                        return format_instagram_data(data['user'], username)
                except:
                    pass
        except:
            continue
    
    # Search in Leakosint database
    try:
        payload = {
            "token": API_TOKEN,
            "request": f"instagram {username}",
            "limit": 50,
            "lang": LANG
        }
        response = requests.post(LEAKOSINT_API_URL, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if "List" in data:
                for db_name, db_content in data["List"].items():
                    if "instagram" in db_name.lower() or "social" in db_name.lower():
                        entries = db_content.get("Data", [])
                        for entry in entries:
                            if username in str(entry).lower():
                                return {
                                    "username": username,
                                    "found_in_breach": True,
                                    "breach_data": entry,
                                    "source": f"Database: {db_name}"
                                }
    except:
        pass
    
    return None

def format_instagram_data(user_data: dict, username: str) -> dict:
    """Format Instagram API response."""
    formatted = {
        "username": user_data.get('username', username),
        "full_name": user_data.get('full_name', 'N/A'),
        "bio": user_data.get('biography', 'N/A')[:200],
        "followers": user_data.get('edge_followed_by', {}).get('count', 0),
        "following": user_data.get('edge_follow', {}).get('count', 0),
        "posts": user_data.get('edge_owner_to_timeline_media', {}).get('count', 0),
        "is_private": user_data.get('is_private', False),
        "is_verified": user_data.get('is_verified', False),
        "profile_pic": user_data.get('profile_pic_url_hd', user_data.get('profile_pic_url', 'N/A')),
        "external_url": user_data.get('external_url', 'N/A'),
        "business_category": user_data.get('business_category_name', 'N/A'),
        "account_type": "Business" if user_data.get('is_business_account') else "Personal",
        "found_in_breach": False
    }
    return formatted

def create_instagram_report(insta_data: dict, username: str) -> str:
    """Create Instagram report."""
    if not insta_data:
        return f"""
❌ <b>Instagram user '@{username}' not found!</b>

💡 <b>Tips:</b>
• Check spelling of username
• Account might be deleted/private
• Try searching with full name instead
"""
    
    if insta_data.get('found_in_breach'):
        return f"""
🔐 <b>Instagram: @{username}</b>
⚠️ <b>⚠️ FOUND IN DATA BREACH! ⚠️</b>

📋 <b>Breached Information:</b>
<pre>{json.dumps(insta_data.get('breach_data', {}), indent=2, ensure_ascii=False)[:1000]}</pre>

<b>Source:</b> {insta_data.get('source', 'Unknown')}
"""
    
    status_emoji = "🔒" if insta_data.get('is_private') else "🌐"
    verified_badge = " ✓✓✓" if insta_data.get('is_verified') else ""
    
    report = f"""
📸 <b>Instagram Profile{verified_badge}</b> {status_emoji}

<b>👤 Username:</b> @{insta_data['username']}
<b>📛 Full Name:</b> {insta_data['full_name']}
<b>📝 Bio:</b> {insta_data['bio']}

<b>📊 Statistics:</b>
• 👥 Followers: {format_number(insta_data['followers'])}
• 📌 Following: {format_number(insta_data['following'])}
• 📷 Posts: {format_number(insta_data['posts'])}

<b>🔧 Account Info:</b>
• Type: {insta_data['account_type']}
• Private: {'Yes' if insta_data['is_private'] else 'No'}
• Verified: {'Yes' if insta_data['is_verified'] else 'No'}

<b>🔗 Links:</b>
• Profile: https://instagram.com/{insta_data['username']}
"""
    
    if insta_data['external_url'] != 'N/A':
        report += f"• Website: {insta_data['external_url']}\n"
    
    if insta_data['business_category'] != 'N/A':
        report += f"\n<b>🏢 Category:</b> {insta_data['business_category']}"
    
    return report

# ==================== GENERAL SEARCH (Leakosint) ====================
def search_leakosint(query: str, query_id: int) -> Optional[List[str]]:
    """Search using Leakosint API."""
    try:
        payload = {
            "token": API_TOKEN,
            "request": query,
            "limit": LIMIT,
            "lang": LANG
        }
        
        response = requests.post(LEAKOSINT_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        api_response = response.json()
        
        if "Error code" in api_response:
            logger.error(f"API Error: {api_response['Error code']}")
            return None
        
        pages = []
        api_data = api_response.get("List", {})
        
        if not api_data:
            pages.append("❌ No results found.")
            return pages
        
        for db_name, db_content in api_data.items():
            message_lines = [f"<b>📁 {db_name}</b>", ""]
            
            info_leak = db_content.get("InfoLeak", "")
            if info_leak:
                message_lines.append(info_leak)
                message_lines.append("")
            
            if db_name != "No results found":
                data_entries = db_content.get("Data", [])
                for entry in data_entries:
                    for col_name, col_value in entry.items():
                        safe_value = str(col_value).replace("<", "&lt;").replace(">", "&gt;")
                        safe_name = str(col_name).replace("<", "&lt;").replace(">", "&gt;")
                        message_lines.append(f"<b>{safe_name}</b>: {safe_value}")
                    message_lines.append("")
            else:
                message_lines.append("No data available.")
            
            full_message = "\n".join(message_lines).strip()
            
            if len(full_message) > 3500:
                full_message = full_message[:3500] + "\n\n⚠️ Truncated..."
            
            pages.append(full_message)
        
        if not pages:
            pages.append("⚠️ No readable data found.")
        
        report_cache[str(query_id)] = pages
        return pages
        
    except Exception as e:
        logger.error(f"Leakosint search error: {e}")
        return None

# ==================== HELPERS ====================
def format_number(num: int) -> str:
    """Format numbers with K/M suffix."""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)

def detect_query_type(query: str) -> Tuple[str, str]:
    """Detect what type of query this is."""
    query = query.strip()
    
    # Check for Facebook UID (numeric, 10-20 digits)
    if re.match(r'^\d{10,20}$', query):
        return "facebook_uid", query
    
    # Check for Instagram username (alphanumeric with dots/underscores)
    if re.match(r'^@?[a-zA-Z0-9_.]{1,30}$', query.lstrip('@')):
        # Exclude if it looks like a phone number or email
        if not re.match(r'^[\d\s\+\-\(\)]{8,}$', query):
            return "instagram", query.lstrip('@')
    
    # Check for email
    if re.match(r'^[^@]+@[^@]+\.[^@]+$', query):
        return "email", query
    
    # Check for phone number
    if re.match(r'^[\d\s\+\-\(\)]{8,}$', query):
        return "phone", query
    
    # Default - general search
    return "general", query

def create_pagination_keyboard(query_id: int, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Create pagination keyboard."""
    markup = InlineKeyboardMarkup(row_width=3)
    
    if total_pages <= 1:
        return markup
    
    if current_page < 0:
        current_page = total_pages - 1
    elif current_page >= total_pages:
        current_page = 0
    
    prev_btn = InlineKeyboardButton("◀️ Prev", callback_data=f"page:{query_id}:{current_page - 1}")
    page_btn = InlineKeyboardButton(f"{current_page + 1}/{total_pages}", callback_data="noop")
    next_btn = InlineKeyboardButton("Next ▶️", callback_data=f"page:{query_id}:{current_page + 1}")
    
    markup.add(prev_btn, page_btn, next_btn)
    return markup

def send_safe_message(chat_id: int, text: str, reply_markup=None):
    """Send message safely."""
    try:
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=reply_markup, disable_web_page_preview=True)
    except:
        clean_text = re.sub(r'<[^>]+>', '', text)
        bot.send_message(chat_id, clean_text, reply_markup=reply_markup)

def user_has_access(user_id: int) -> bool:
    """Check user access."""
    if not ALLOWED_USER_IDS:
        return True
    return user_id in ALLOWED_USER_IDS

# ==================== BOT HANDLERS ====================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
🔍 <b>Advanced OSINT Bot</b>

<b>📱 Features:</b>
• 🔍 Facebook UID Lookup
• 📸 Instagram Profile Search  
• 📧 Email/Phone/Name Search
• 💾 Data Breach Database

<b>📝 How to use:</b>
<code>/fb 1000123456789</code> - Facebook UID lookup
<code>/ig username</code> - Instagram profile
<code>@username</code> or any text - General search

<b>⚡ Examples:</b>
• <code>/fb 61556123456789</code>
• <code>/ig cristiano</code>
• <code>+1234567890</code>
• <code>someone@gmail.com</code>

<b>⚠️ Note:</b> For educational purposes only!
"""
    bot.reply_to(message, welcome_text, parse_mode="HTML")

@bot.message_handler(commands=['fb'])
def handle_facebook(message):
    """Handle /fb command for Facebook UID lookup."""
    user_id = message.from_user.id
    if not user_has_access(user_id):
        bot.send_message(message.chat.id, "⛔ Access denied.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "❌ Usage: <code>/fb UID</code>\nExample: <code>/fb 61556123456789</code>", parse_mode="HTML")
        return
    
    uid = args[1].strip()
    bot.send_chat_action(message.chat.id, "typing")
    
    # Send initial message
    status_msg = bot.send_message(message.chat.id, "🔍 Searching Facebook UID...")
    
    fb_data = fetch_facebook_info(uid)
    report = create_facebook_report(fb_data, uid)
    
    bot.edit_message_text(report, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML", disable_web_page_preview=True)

@bot.message_handler(commands=['ig'])
def handle_instagram(message):
    """Handle /ig command for Instagram lookup."""
    user_id = message.from_user.id
    if not user_has_access(user_id):
        bot.send_message(message.chat.id, "⛔ Access denied.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "❌ Usage: <code>/ig username</code>\nExample: <code>/ig cristiano</code>", parse_mode="HTML")
        return
    
    username = args[1].strip()
    bot.send_chat_action(message.chat.id, "typing")
    
    status_msg = bot.send_message(message.chat.id, "🔍 Searching Instagram...")
    
    insta_data = fetch_instagram_info(username)
    report = create_instagram_report(insta_data, username)
    
    bot.edit_message_text(report, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML", disable_web_page_preview=True)

@bot.message_handler(func=lambda message: True)
def handle_search(message):
    """Handle all other messages as searches."""
    user_id = message.from_user.id
    if not user_has_access(user_id):
        bot.send_message(message.chat.id, "⛔ Access denied.")
        return
    
    if message.content_type != "text":
        return
    
    query = message.text.strip()
    if not query:
        return
    
    # Detect query type
    query_type, clean_query = detect_query_type(query)
    
    bot.send_chat_action(message.chat.id, "typing")
    
    # Handle Facebook UID
    if query_type == "facebook_uid":
        fb_data = fetch_facebook_info(clean_query)
        report = create_facebook_report(fb_data, clean_query)
        send_safe_message(message.chat.id, report)
        return
    
    # Handle Instagram
    if query_type == "instagram":
        insta_data = fetch_instagram_info(clean_query)
        report = create_instagram_report(insta_data, clean_query)
        send_safe_message(message.chat.id, report)
        return
    
    # Handle general search via Leakosint
    query_id = randint(0, 99999999)
    status_msg = bot.send_message(message.chat.id, f"🔍 Searching for: <code>{query[:50]}</code>...", parse_mode="HTML")
    
    pages = search_leakosint(query, query_id)
    
    if pages is None:
        bot.edit_message_text("❌ API error. Please try again.", chat_id=message.chat.id, message_id=status_msg.message_id)
        return
    
    if not pages:
        bot.edit_message_text("❌ No results found.", chat_id=message.chat.id, message_id=status_msg.message_id)
        return
    
    markup = create_pagination_keyboard(query_id, 0, len(pages))
    bot.edit_message_text(pages[0], chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_pagination(call: CallbackQuery):
    """Handle pagination button clicks."""
    if call.data == "noop":
        bot.answer_callback_query(call.id, "📄 Page indicator")
        return
    
    if call.data.startswith("page:"):
        try:
            _, query_id_str, page_str = call.data.split(":")
            query_id = query_id_str
            page = int(page_str)
            
            pages = report_cache.get(query_id)
            if not pages:
                bot.answer_callback_query(call.id, "❌ Results expired. Search again.")
                bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
                return
            
            total_pages = len(pages)
            if page < 0:
                page = total_pages - 1
            elif page >= total_pages:
                page = 0
            
            new_markup = create_pagination_keyboard(query_id, page, total_pages)
            
            try:
                bot.edit_message_text(pages[page], chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=new_markup)
                bot.answer_callback_query(call.id)
            except:
                clean_text = re.sub(r'<[^>]+>', '', pages[page])
                bot.edit_message_text(clean_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=new_markup)
                bot.answer_callback_query(call.id, "Plain text mode")
                
        except Exception as e:
            logger.error(f"Pagination error: {e}")
            bot.answer_callback_query(call.id, "Navigation error")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📘 <b>Help Guide</b>

<b>/fb UID</b> - Facebook profile by UID
<b>/ig username</b> - Instagram profile
<b>/start</b> - Welcome message
<b>/help</b> - This guide

<b>📌 Examples:</b>
• <code>/fb 61556123456789</code>
• <code>/ig cristiano</code>
• <code>someone@gmail.com</code>
• <code>+1234567890</code>

<b>⚠️ Disclaimer:</b>
For legitimate research only!
"""
    bot.reply_to(message, help_text, parse_mode="HTML")

# ==================== MAIN ====================
def main():
    if not BOT_TOKEN:
        print("\n" + "="*50)
        print("❌ BOT_TOKEN is not set!")
        print("="*50)
        print("\n📝 How to get Bot Token:")
        print("1. Open Telegram → @BotFather")
        print("2. Send: /newbot")
        print("3. Choose a name for your bot")
        print("4. Choose a username (must end with 'bot')")
        print("5. Copy the token and paste it in the code")
        print("\n📍 In code, find: BOT_TOKEN = ''")
        print("   Replace with: BOT_TOKEN = 'your_token_here'")
        print("\n✅ API_TOKEN is already set to: 8735045882:dGnfJAPg")
        print("="*50 + "\n")
        return
    
    print("\n" + "="*50)
    print("🤖 Bot Started Successfully!")
    print("="*50)
    print(f"📱 Bot Token: {BOT_TOKEN[:10]}...")
    print(f"🔑 API Token: {API_TOKEN[:10]}...")
    print("\n✅ Features:")
    print("   • Facebook UID Lookup")
    print("   • Instagram Profile Search")
    print("   • Email/Phone/Name Search")
    print("   • Data Breach Database")
    print("\n" + "="*50 + "\n")
    
    while True:
        try:
            bot.infinity_polling(timeout=60)
        except KeyboardInterrupt:
            print("\n👋 Bot stopped.")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            import time
            time.sleep(5)

if __name__ == "__main__":
    main()
