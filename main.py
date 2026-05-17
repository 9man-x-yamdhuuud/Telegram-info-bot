<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Документация API</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
            color: #333;
        }
        header {
            background-color: #333;
            color: white;
            padding: 20px;
            text-align: center;
        }
        h1 {
            margin: 0;
        }
        .content {
            max-width: 900px;
            margin: 20px auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        h2 {
            color: #333;
        }
        pre {
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Courier New', Courier, monospace;
            border: 1px solid #ddd;
        }
        .note {
            background-color: #ffecb3;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .example {
            background-color: #e9f7f7;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .parameters-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        .parameters-table th, .parameters-table td {
            padding: 8px 12px;
            border: 1px solid #ddd;
            text-align: left;
        }
        .parameters-table th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>

<header>
    <h1>Документация API</h1>
</header>

<div class="content">
    <h2>Getting data via API</h2>
    <p>You can receive data automatically using the API. To do this, you need to write a command /API in the bot and get your personal token. Initially, it will have 100 free requests that will allow testing the system. When they end, money will begin to spend money from your balance.</p>

    <p>The price of the request depends on the type of request and on the specified search limit. By default, the limit is 100, with such a limit, most requests will cost 0.003 $.</p>

    <p>The price calculation formula in dollars is as follows:</p>
    <pre><code>0.0002 * (5 + sqrt(Limit * Complexity))</code></pre>
    <ul>
        <li>Limit is a search limit that you specified (for example, 100).</li>
        <li>Complexity is a parameter reflecting the number of single searches that must be performed for your request.</li>
    </ul>

    <p>If the request consists of several words, then they are looking for in all possible rearrangements, and therefore the complexity depends on the number of words in your request. Here is an example of calculating complexity:</p>

    <ul>
        <li>1 word: Complexity = 1</li>
        <li>2 words: Complexity = 5</li>
        <li>3 words: Complexity = 16</li>
        <li>More than 3 words: Complexity = 40</li>
    </ul>

    <p>Moreover, the following elements are not considered the words:</p>
    <ul>
        <li>Dates</li>
        <li>Lines are shorter than 4 characters</li>
        <li>Numbers shorter than 6 characters</li>
    </ul>

    <p>If you need to avoid splitting your query into words by spaces, use double quotes. Phrases in double quotes are treated as one word.</p>
    <div class="note">
        <strong>Note:</strong> The limit on the frequency of requests from one IP is 3 requests per second. If you need to run more queries, you can combine multiple queries into one or create a separate key in the /app tab.
    </div>

    <h2>Request parameters</h2>
    <table class="parameters-table">
        <thead>
            <tr>
                <th>Parameter</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>'token'</strong></td>
                <td>The token that you receive after executing the command <code>/api</code>.</td>
            </tr>
            <tr>
                <td><strong>'request'</strong></td>
                <td>A line with your request or an array of lines with several requests.</td>
            </tr>
            <tr>
                <td><strong>'limit'</strong></td>
                <td>Search limit (default 100). The number is from 100 to 10,000. It determines the number of returned results and the search range in the database.</td>
            </tr>
            <tr>
                <td><strong>'lang'</strong></td>
                <td>The language code on which there will be the results of the request (by default <code> en </ Сode>).</td>
            </tr>
            <tr>
                <td><strong>'type'</strong></td>
                <td>Type of reporting: <code>json</code>, <code>short</code>, <code>html</code> (By default <code>json</code>).</td>
            </tr>
            <tr>
                <td><strong>'bot_name'</strong></td>
                <td>The name of the bot in the format <code> @name </sode> (it is necessary to indicate if the bot does not apply to the main group of mirrors).</td>
            </tr>
        </tbody>
    </table>

    <h2>Examples of requests</h2>
    <div class="example">
        <p><strong>Example 1:</strong></p>
        <pre>
{"token":"987654321:b42vAQjW", "request":"google"}
        </pre>
    </div>
    <div class="example">
        <p><strong>Example 2:</strong></p>
        <pre>
{"token":"987654321:b42vAQjW", "request":"Petya Ivanov ", "lang": "ru"}
        </pre>
    </div>
    <div class="example">
        <p><strong>Example 3:</strong></p>
        <pre>
{"token":"987654321:b42vAQjW", "request":"example@gmail.com", "limit": 300}
        </pre>
    </div>
    <div class="example">
        <p><strong>Example 4:</strong></p>
        <pre>
{"token":"987654321:b42vAQjW", "request":"Elon Reeve Musk", "limit": 100, "lang":"ru"}
        </pre>
    </div>
    <div class="example">
        <p><strong>Example 5:</strong></p>
        <pre>
{"token":"987654321:b42vAQjW", "request":"example@gmail.com\nElon Reeve Musk"}
        </pre>
    </div>
    <div class="example">
        <p><strong>Example 6:</strong></p>
        <pre>
{"token":"987654321:b42vAQjW", "request":["example@gmail.com","Elon Reeve Musk"]}
        </pre>
    </div>

    <h2>Пример кода (Python)</h2>
    <div class="example">
        <p>Пример использования API на языке Python:</p>
        <pre>
import requests

data = {"token":"987654321:Vg41g0qY", "request":"test request", "limit": 100, "lang":"ru"}
url = 'https://leakosintapi.com/'
response = requests.post(url, json=data)
print(response.json())
        </pre>
    </div>

    <p><strong>Please note:</strong> The query data is sent in JSON format. If you send in the form of a request parameters, you will get a 501 error.</p>

    <div class="example">
        <p>An example of a telegram bout based on the API:</p>
        <pre>
import requests
from random import randint
try:
    import telebot
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
except ModuleNotFoundError:
    input("There is no necessary library. Complete the command line command: PIP Install Pytelegrambotapi")

url = "https://leakosintapi.com/"
bot_token = "" #Insert here the token received from @botfather
api_token = ""  #Insert here the token received from Leakosint
lang = "ru"
limit = 300

#In this function, you can check whether the user has access to
def user_access_test(user_id):
    return(True)

#Function for generating reports
cash_reports = {}
def generate_report(query, query_id):
    global cash_reports, url, bot_token, api_token, limit, lang
    data =  {"token":api_token, "request":query.split("\n")[0], "limit": limit, "lang":lang}
    response = requests.post(url, json=data).json()
    print(response)
    if "Error code" in response:
        print("Error:"+response["Error code"])
        return(None)
    cash_reports[str(query_id)] = []
    for database_name in response["List"].keys():
        text = [f"&lt;b&gt;{database_name}&lt;/b&gt;",""]
        text.append(response["List"][database_name]["InfoLeak"]+"\n")
        if database_name!="No results found":
            for report_data in response["List"][database_name]["Data"]:
                for column_name in report_data.keys():
                    text.append(f"&lt;b&gt;{column_name}&lt;/b&gt;:  {report_data[column_name]}")
                text.append("")
        text = "\n".join(text)
        if len(text)>3500:
            text = text[:3500]+text[3500:].split("\n")[0]+"\n\nSome data did not fit this message"
        cash_reports[str(query_id)].append(text)
    return(cash_reports[str(query_id)])

#Function for creating an inline keyboard
def create_inline_keyboard(query_id, page_id, count_page):
    markup = InlineKeyboardMarkup()
    if page_id<0:
        page_id=count_page
    elif page_id>count_page-1:
        page_id=page_id%count_page
    if count_page==1:
        return markup
    markup.row_width = 3
    markup.add(InlineKeyboardButton(text = "<<", callback_data=f"/page {query_id} {page_id-1}"),
               InlineKeyboardButton(text = f"{page_id+1}/{count_page}", callback_data="page_list"),
               InlineKeyboardButton(text = ">>", callback_data=f"/page {query_id} {page_id+1}"))
    return markup

bot = telebot.TeleBot(bot_token)
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am a telegram-boot that can search for databases.", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    user_id = message.from_user.id
    if not(user_access_test(user_id)):
        bot.send_message(message.chat.id, "You have no access to the bot")
        return()
    if message.content_type == "text":
        query_id = randint(0,9999999)
        report = generate_report(message.text,query_id)
        markup = create_inline_keyboard(query_id,0,len(report))
        if report==None:
            bot.reply_to(message, "The bot does not work at the moment.", parse_mode="Markdown")
        try:
            bot.send_message(message.chat.id, report[0], parse_mode="html", reply_markup=markup) #, reply_markup=markup
        except telebot.apihelper.ApiTelegramException:
            bot.send_message(message.chat.id, text = report[0].replace("&lt;b&gt;","").replace("&lt;/b&gt;",""), reply_markup=markup)
        
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call: CallbackQuery):
    global cash_reports
    if call.data.startswith("/page "):
        query_id, page_id = call.data.split(" ")[1:]
        if not(query_id in cash_reports):
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="The results of the request have already been deleted")
        else:
            report = cash_reports[query_id]
            markup = create_inline_keyboard(query_id,int(page_id),len(report))
            try:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=report[int(page_id)], parse_mode="html", reply_markup=markup)
            except telebot.apihelper.ApiTelegramException:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=report[int(page_id)].replace("&lt;b&gt;","").replace("&lt;/b&gt;",""), reply_markup=markup)
while True:
    try:
        bot.polling()
    except:
        pass
        </pre>
    </div>

</div>

</body>
</html>
