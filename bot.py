#!/usr/bin/env python3
"""
COMPLETE OSINT TELEGRAM BOT - FIXED VERSION
"""

import requests
import logging
import re
import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from random import randint
from typing import Dict, List, Optional, Tuple

try:
    import telebot
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
except ImportError:
    print("ERROR: Run: pip install pyTelegramBotAPI requests phonenumbers")
    exit(1)

# ==================== CONFIGURATION ====================
API_TOKEN = "8735045882:dGnfJAPg"
BOT_TOKEN = os.environ.get('8683516544:AAGyndEbkMW1wsbXTFIbFMg8AVA_uZ__bSk', '')
PORT = int(os.environ.get('PORT', 8080))
LANG = "ru"
LIMIT = 500
LEAKOSINT_API_URL = "https://leakosintapi.com/"
PHONE_DEFAULT_COUNTRY = "IN"

ALLOWED_USER_IDS = []
report_cache: Dict[str, List[str]] = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

# ==================== HEALTH CHECK SERVER ====================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Bot is Running!</h1><p>Status: Active</p></body></html>")
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def run_health_server():
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
        logger.info(f"Health check server running on port {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Health server error: {e}")

# ==================== INSTAGRAM FUNCTIONS ====================
def fetch_instagram_full_info(username: str) -> Optional[Dict]:
    username = username.strip().lstrip('@').lower()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    urls = [
        f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}",
        f"https://www.instagram.com/{username}/?__a=1&__d=1"
    ]
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'graphql' in data:
                    user_data = data['graphql']['user']
                    return format_instagram_location(user_data, username)
                elif 'data' in data and 'user' in data['data']:
                    user_data = data['data']['user']
                    return format_instagram_location(user_data, username)
        except:
            continue
    
    try:
        payload = {
            "token": API_TOKEN,
            "request": f"instagram {username}",
            "limit": 100,
            "lang": LANG
        }
        response = requests.post(LEAKOSINT_API_URL, json=payload, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if "List" in data:
                for db_name, db_content in data["List"].items():
                    entries = db_content.get("Data", [])
                    for entry in entries:
                        if username in str(entry).lower():
                            location = extract_location_from_text(str(entry))
                            return {
                                "username": username,
                                "found_in_breach": True,
                                "breach_data": entry,
                                "location": location,
                                "source": f"Database: {db_name}"
                            }
    except:
        pass
    
    return None

def format_instagram_location(user_data: dict, username: str) -> dict:
    bio = user_data.get('biography', '')
    location_data = extract_location_from_text(bio)
    
    recent_locations = []
    recent_media = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
    for post in recent_media[:5]:
        node = post.get('node', {})
        if node.get('location'):
            loc = node.get('location')
            recent_locations.append({
                'name': loc.get('name', ''),
                'lat': loc.get('lat', ''),
                'lng': loc.get('lng', '')
            })
    
    return {
        "username": user_data.get('username', username),
        "full_name": user_data.get('full_name', 'N/A'),
        "bio": bio[:300],
        "followers": user_data.get('edge_followed_by', {}).get('count', 0),
        "following": user_data.get('edge_follow', {}).get('count', 0),
        "posts": user_data.get('edge_owner_to_timeline_media', {}).get('count', 0),
        "is_private": user_data.get('is_private', False),
        "is_verified": user_data.get('is_verified', False),
        "external_url": user_data.get('external_url', 'N/A'),
        "business_category": user_data.get('business_category_name', 'N/A'),
        "account_type": "Business" if user_data.get('is_business_account') else "Personal",
        "location": location_data,
        "recent_locations": recent_locations,
        "found_in_breach": False
    }

def extract_location_from_text(text: str) -> Dict:
    location = {"city": None, "state": None, "country": None}
    
    city_match = re.search(r'(?:in|at|from|📍)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
    if city_match:
        location["city"] = city_match.group(1)
    
    countries = ['India', 'USA', 'UK', 'Russia', 'Germany', 'France', 'Canada', 'Australia', 'UAE']
    for country in countries:
        if country.lower() in text.lower():
            location["country"] = country
            break
    
    return location

def create_instagram_report(insta_data: dict, username: str) -> str:
    if not insta_data:
        return f"ERROR: Instagram '{username}' not found!\n\nTry: /ig cristiano"
    
    if insta_data.get('found_in_breach'):
        return f"""
[BREACH ALERT] Instagram: @{username}

Location: {format_location_text(insta_data.get('location', {}))}

Breached Data:
{json.dumps(insta_data.get('breach_data', {}), indent=2, ensure_ascii=False)[:800]}

Source: {insta_data.get('source', 'Unknown')}
"""
    
    status = "Private" if insta_data['is_private'] else "Public"
    verified = "[VERIFIED]" if insta_data['is_verified'] else ""
    
    report = f"""
[INSTAGRAM PROFILE] {verified}

Username: @{insta_data['username']}
Name: {insta_data['full_name']}
Bio: {insta_data['bio']}

---------- LOCATION ----------
{format_location_text(insta_data.get('location', {}))}

---------- STATISTICS ----------
Followers: {format_number(insta_data['followers'])}
Following: {format_number(insta_data['following'])}
Posts: {format_number(insta_data['posts'])}

---------- ACCOUNT INFO ----------
Type: {insta_data['account_type']}
Private: {insta_data['is_private']}
Category: {insta_data['business_category']}

---------- LINK ----------
https://instagram.com/{insta_data['username']}
"""
    
    if insta_data.get('recent_locations'):
        report += f"\n---------- RECENT CHECK-INS ----------\n"
        for loc in insta_data['recent_locations'][:3]:
            if loc.get('name'):
                report += f"- {loc['name']}\n"
                if loc.get('lat') and loc.get('lng'):
                    report += f"  Map: https://maps.google.com/?q={loc['lat']},{loc['lng']}\n"
    
    return report

# ==================== FACEBOOK FUNCTIONS ====================
def fetch_facebook_full_info(uid: str) -> Optional[Dict]:
    uid = str(uid).strip()
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    fb_urls = [
        f"https://graph.facebook.com/v18.0/{uid}?access_token=6628568379%7Cc1e620fa708a1d5696fb991c1bde5662&fields=id,name,first_name,last_name,email,gender,birthday,location,hometown,relationship_status,about,picture,education,work",
        f"https://graph.facebook.com/v18.0/{uid}?fields=id,name,first_name,last_name,email,gender,birthday,location&access_token=6628568379%7Cc1e620fa708a1d5696fb991c1bde5662"
    ]
    
    for url in fb_urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data and 'error' not in data:
                    return format_facebook_address(data, uid)
        except:
            continue
    
    try:
        payload = {
            "token": API_TOKEN,
            "request": f"facebook {uid}",
            "limit": 100,
            "lang": LANG
        }
        response = requests.post(LEAKOSINT_API_URL, json=payload, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if "List" in data:
                for db_name, db_content in data["List"].items():
                    entries = db_content.get("Data", [])
                    for entry in entries:
                        if uid in str(entry):
                            address = extract_address_from_text(str(entry))
                            return {
                                "uid": uid,
                                "found_in_breach": True,
                                "breach_data": entry,
                                "address": address,
                                "source": f"Database: {db_name}"
                            }
    except:
        pass
    
    return None

def format_facebook_address(data: dict, uid: str) -> dict:
    location = data.get('location', {})
    hometown = data.get('hometown', {})
    
    formatted = {
        "uid": uid,
        "name": data.get('name', 'N/A'),
        "first_name": data.get('first_name', 'N/A'),
        "last_name": data.get('last_name', 'N/A'),
        "email": data.get('email', 'N/A'),
        "gender": data.get('gender', 'N/A'),
        "birthday": data.get('birthday', 'N/A'),
        "relationship": data.get('relationship_status', 'N/A'),
        "about": data.get('about', 'N/A')[:200],
        "current_city": location.get('name', 'N/A'),
        "hometown": hometown.get('name', 'N/A'),
        "profile_url": f"https://facebook.com/{uid}",
        "education": [],
        "work": [],
        "found_in_breach": False
    }
    
    if 'education' in data:
        for edu in data['education'][:3]:
            school = edu.get('school', {}).get('name', 'N/A')
            year = edu.get('year', {}).get('name', '')
            formatted['education'].append(f"{school} ({year})" if year else school)
    
    return formatted

def extract_address_from_text(text: str) -> Dict:
    address = {"street": None, "city": None, "zip": None}
    
    street_match = re.search(r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave)\b', text, re.IGNORECASE)
    if street_match:
        address["street"] = street_match.group(0)
    
    zip_match = re.search(r'\b\d{5}(?:-\d{4})?\b', text)
    if zip_match:
        address["zip"] = zip_match.group(0)
    
    return address

def create_facebook_report(fb_data: dict, uid: str) -> str:
    if not fb_data:
        return f"ERROR: Facebook UID {uid} not found!\n\nUsage: /fb 61556123456789"
    
    if fb_data.get('found_in_breach'):
        return f"""
[BREACH ALERT] Facebook UID: {uid}

Address: {format_address_text(fb_data.get('address', {}))}

Breached Data:
{json.dumps(fb_data.get('breach_data', {}), indent=2, ensure_ascii=False)[:800]}

Source: {fb_data.get('source', 'Unknown')}
"""
    
    report = f"""
[FACEBOOK PROFILE]
----------------------------------------
UID: {fb_data['uid']}
Name: {fb_data['name']}
Email: {fb_data['email']}

Location: {fb_data['current_city']}
Hometown: {fb_data['hometown']}

Gender: {fb_data['gender']}
Birthday: {fb_data['birthday']}
"""
    
    if fb_data.get('education'):
        report += f"\nEducation:\n"
        for edu in fb_data['education']:
            report += f"  - {edu}\n"
    
    report += f"\nProfile: {fb_data['profile_url']}"
    report += f"\n\nMaps: https://maps.google.com/?q={fb_data['current_city']}"
    
    return report

# ==================== PHONE FUNCTIONS ====================
def validate_phone_number(phone: str) -> Optional[Dict]:
    try:
        cleaned = re.sub(r'[^\d+]', '', phone)
        if cleaned.startswith('+'):
            parsed = phonenumbers.parse(cleaned, None)
        else:
            parsed = phonenumbers.parse(cleaned, PHONE_DEFAULT_COUNTRY)
        
        if phonenumbers.is_valid_number(parsed):
            return {
                "valid": True,
                "international": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
                "e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
                "country": geocoder.description_for_number(parsed, "en"),
                "carrier": carrier.name_for_number(parsed, "en") or "Unknown",
                "type": get_number_type(parsed)
            }
    except:
        pass
    return None

def get_number_type(parsed):
    types = {
        phonenumbers.PhoneNumberType.MOBILE: "Mobile",
        phonenumbers.PhoneNumberType.FIXED_LINE: "Landline"
    }
    return types.get(phonenumbers.number_type(parsed), "Unknown")

def create_phone_report(phone_info: Dict) -> str:
    if not phone_info:
        return "ERROR: Invalid phone number"
    
    return f"""
[PHONE NUMBER INFO]
----------------------------------------
Number: {phone_info['international']}
Country: {phone_info['country']}
Carrier: {phone_info['carrier']}
Type: {phone_info['type']}
"""

# ==================== LEAKOSINT SEARCH ====================
def search_leakosint(query: str, query_id: int) -> Optional[List[str]]:
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
            return None
        
        pages = []
        api_data = api_response.get("List", {})
        
        if not api_data:
            pages.append("No results found.")
            return pages
        
        for db_name, db_content in api_data.items():
            if db_name == "No results found":
                continue
            
            message_lines = [f"[{db_name}]", "="*30, ""]
            
            data_entries = db_content.get("Data", [])
            for entry in data_entries:
                for col_name, col_value in entry.items():
                    safe_value = str(col_value).replace("<", "&lt;").replace(">", "&gt;")
                    safe_name = str(col_name).replace("<", "&lt;").replace(">", "&gt;")
                    message_lines.append(f"{safe_name}: {safe_value}")
                message_lines.append("-"*20)
            
            full_message = "\n".join(message_lines).strip()
            if len(full_message) > 3500:
                full_message = full_message[:3500] + "\n\n[TRUNCATED]"
            
            pages.append(full_message)
        
        report_cache[str(query_id)] = pages
        return pages
        
    except Exception as e:
        logger.error(f"Leakosint error: {e}")
        return None

# ==================== HELPERS ====================
def format_number(num: int) -> str:
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)

def format_location_text(location: Dict) -> str:
    if not location:
        return "Location not available"
    
    lines = []
    if location.get('city'):
        lines.append(f"City: {location['city']}")
    if location.get('state'):
        lines.append(f"State: {location['state']}")
    if location.get('country'):
        lines.append(f"Country: {location['country']}")
    
    return "\n".join(lines) if lines else "Location not found"

def format_address_text(address: Dict) -> str:
    if not address:
        return "Address not available"
    
    lines = []
    if address.get('street'):
        lines.append(f"Street: {address['street']}")
    if address.get('city'):
        lines.append(f"City: {address['city']}")
    if address.get('zip'):
        lines.append(f"ZIP: {address['zip']}")
    
    return "\n".join(lines) if lines else "Address not found"

def create_pagination_keyboard(query_id: int, page: int, total: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=3)
    if total <= 1:
        return markup
    
    prev = InlineKeyboardButton("<< Prev", callback_data=f"page:{query_id}:{page - 1}")
    ind = InlineKeyboardButton(f"{page + 1}/{total}", callback_data="noop")
    nxt = InlineKeyboardButton("Next >>", callback_data=f"page:{query_id}:{page + 1}")
    markup.add(prev, ind, nxt)
    return markup

def send_safe(chat_id: int, text: str, reply_markup=None):
    try:
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=reply_markup, disable_web_page_preview=True)
    except:
        clean = re.sub(r'<[^>]+>', '', text)
        bot.send_message(chat_id, clean, reply_markup=reply_markup)

# ==================== BOT COMMANDS ====================
@bot.message_handler(commands=['start'])
def start(message):
    welcome = """
OSINT BOT v3.0

Commands:
/fb 61556123456789 - Facebook with address
/ig cristiano - Instagram with location
/help - Full guide

Auto-detect:
+919876543210 -> Phone info
user@gmail.com -> Breach search
@username -> Instagram
123456789012 -> Facebook UID
"""
    bot.reply_to(message, welcome)

@bot.message_handler(commands=['fb'])
def fb_cmd(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "Usage: /fb UID\nExample: /fb 61556123456789")
        return
    
    uid = args[1].strip()
    bot.send_chat_action(message.chat.id, "typing")
    msg = bot.send_message(message.chat.id, "Searching Facebook...")
    data = fetch_facebook_full_info(uid)
    report = create_facebook_report(data, uid)
    bot.edit_message_text(report, chat_id=message.chat.id, message_id=msg.message_id, disable_web_page_preview=True)

@bot.message_handler(commands=['ig'])
def ig_cmd(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "Usage: /ig username\nExample: /ig cristiano")
        return
    
    username = args[1].strip()
    bot.send_chat_action(message.chat.id, "typing")
    msg = bot.send_message(message.chat.id, "Searching Instagram...")
    data = fetch_instagram_full_info(username)
    report = create_instagram_report(data, username)
    bot.edit_message_text(report, chat_id=message.chat.id, message_id=msg.message_id, disable_web_page_preview=True)

@bot.message_handler(commands=['help'])
def help_cmd(message):
    help_text = """
COMMANDS

/fb UID - Facebook with address
   Example: /fb 61556123456789

/ig username - Instagram with location
   Example: /ig cristiano

AUTO DETECTION:
Phone: +919876543210
Email: user@gmail.com
Instagram: @username
Facebook: 61556123456789

WHAT YOU GET:
- Instagram: City, Country, Maps link
- Facebook: Location, Address, Maps link
- Phone: Carrier, Country, Type
"""
    bot.reply_to(message, help_text)

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    if message.content_type != "text":
        return
    
    query = message.text.strip()
    if not query:
        return
    
    bot.send_chat_action(message.chat.id, "typing")
    
    # Phone number
    if re.match(r'^\+?\d{8,15}$', re.sub(r'[^\d+]', '', query)):
        phone_info = validate_phone_number(query)
        send_safe(message.chat.id, create_phone_report(phone_info))
        if phone_info:
            qid = randint(0, 99999999)
            pages = search_leakosint(phone_info['e164'], qid)
            if pages:
                markup = create_pagination_keyboard(qid, 0, len(pages))
                send_safe(message.chat.id, pages[0], markup)
        return
    
    # Email
    if '@' in query and '.' in query:
        qid = randint(0, 99999999)
        msg = bot.send_message(message.chat.id, "Searching email...")
        pages = search_leakosint(query, qid)
        if pages:
            markup = create_pagination_keyboard(qid, 0, len(pages))
            bot.edit_message_text(pages[0], chat_id=message.chat.id, message_id=msg.message_id, reply_markup=markup)
        else:
            bot.edit_message_text("No results found", chat_id=message.chat.id, message_id=msg.message_id)
        return
    
    # Instagram username
    if query.startswith('@') or (query.isalnum() and len(query) < 30 and not query.isdigit()):
        data = fetch_instagram_full_info(query)
        send_safe(message.chat.id, create_instagram_report(data, query))
        return
    
    # Facebook UID (digits only)
    if query.isdigit() and len(query) >= 10:
        data = fetch_facebook_full_info(query)
        send_safe(message.chat.id, create_facebook_report(data, query))
        return
    
    # General search
    qid = randint(0, 99999999)
    msg = bot.send_message(message.chat.id, f"Searching: {query[:50]}...")
    pages = search_leakosint(query, qid)
    if pages:
        markup = create_pagination_keyboard(qid, 0, len(pages))
        bot.edit_message_text(pages[0], chat_id=message.chat.id, message_id=msg.message_id, reply_markup=markup)
    else:
        bot.edit_message_text("No results found", chat_id=message.chat.id, message_id=msg.message_id)

@bot.callback_query_handler(func=lambda call: True)
def pagination(call):
    if call.data == "noop":
        bot.answer_callback_query(call.id)
        return
    
    if call.data.startswith("page:"):
        try:
            _, qid, pstr = call.data.split(":")
            page = int(pstr)
            pages = report_cache.get(qid)
            if not pages:
                bot.answer_callback_query(call.id, "Results expired")
                return
            
            total = len(pages)
            if page < 0:
                page = total - 1
            elif page >= total:
                page = 0
            
            markup = create_pagination_keyboard(qid, page, total)
            bot.edit_message_text(pages[page], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Pagination error: {e}")

# ==================== MAIN ====================
if __name__ == "__main__":
    print("\n" + "="*50)
    print("OSINT TELEGRAM BOT")
    print("="*50)
    
    if not BOT_TOKEN:
        print("\nERROR: BOT_TOKEN not set!")
        print("Set environment variable: BOT_TOKEN=your_token")
        exit(1)
    
    print(f"Bot Token: {BOT_TOKEN[:15]}...")
    print(f"API Token: {API_TOKEN[:15]}...")
    print(f"Health Port: {PORT}")
    print("\nFeatures: Instagram + Location | Facebook + Address | Phone | Email")
    print("="*50)
    print("BOT STARTING...")
    print("="*50 + "\n")
    
    # Start health check server
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Start bot
    while True:
        try:
            bot.infinity_polling(timeout=60)
        except KeyboardInterrupt:
            print("\nBot stopped.")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            import time
            time.sleep(5)
