from flask.wrappers import Response
from flask import Flask
from flask import request, abort
from telegram_bot_api import parse_message, \
                                send_message, \
                                deleteMessage, \
                                editMessageText, \
                                message_format_for_postgres, \
                                answerInlineQuery, \
                                sendVideo
from threading import Thread
import datetime
from time import sleep
from postgres_api import Fetchpostgres 
from postgresconf.config import config as pconfig
from credentials import config

token = config.TG_BOT_TOKEN

params = pconfig()
print('Trying to connect to the postgres backend.', end='')
for _ in range(100):
    try:
        print('.', end='.')
        fetcher = Fetchpostgres(params)
        print()
        print('Postgres connection established.')
        break
    except:
        pass
        print()
        print("Waiting for the postgres to load!")
    sleep(3)

app = Flask(__name__)

def manage_messages(msg):
    try:
        parsed_message = parse_message(msg)
        chat_id, message_info, chat_type = parsed_message
        if chat_type == 'callback_query':
            handle_callback_query(chat_id, message_info)
        elif chat_type == 'message':
            handle_message(chat_id, message_info)
        elif chat_type == 'inline_query':
            handle_inline_query(inline_query_id=chat_id, message_info=message_info)
    except Exception as e:
        print(e)
        
def make_reply_markup_page_control(page_number, number_of_pages):
    reply_markup=''
    if 2<=page_number<number_of_pages:
        reply_markup = {'inline_keyboard': [[{'text': 'Next page', 'callback_data': f'page {page_number+1}'}], [{'text': 'Previous page', 'callback_data': f'page {page_number-1}'}]]}
    elif (page_number==number_of_pages) and (1<number_of_pages):
            reply_markup = {'inline_keyboard': [[{'text': 'Previous page', 'callback_data': f'page {page_number-1}'}], ]}
    elif (page_number==1) and (1<number_of_pages):
            reply_markup = {'inline_keyboard': [[{'text': 'Next page', 'callback_data': f'page {page_number+1}'}], ]}
    return reply_markup

def handle_commands(message):
    queries = []
    if message:
        if not message.startswith('/'):
            message = f"/search {message}"
        if message == '/today':
            date = datetime.datetime.today().strftime("%Y.%m.%d")
            queries = fetcher.getBySpecificDate(date)
        elif message == '/tomorrow':
            date = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime("%Y.%m.%d")
            queries = fetcher.getBySpecificDate(date)
        elif message == '/info':
            queries = ["If you have any suggestions, comments, or questions, please don't hesitate to reach out to me. Reach me at reach.s.farhad@gmail.com"]
        elif message.startswith('/search'):
            search_query = message.split(' ', 1)[-1].split(',')
            print(search_query)
            queries = fetcher.get_query_any_column(search_query, columns=['Aufzugsstrecke', 'Versammlungsort', 'Thema', 'PLZ', 'Datum'])
            if not queries:
                queries = ["There's nothing to show."]
        elif message.startswith('/date'):
            date = message.split(' ', 1)[-1]
            try:
                date_query = datetime.datetime.strptime(date, '%d.%m.%Y').strftime("%Y.%m.%d")
                queries = fetcher.getBySpecificDate(date_query)
            except:
                queries = ['This command should be used as follows:\n/date Day.Month.Year']
    return queries
    
def handle_inline_query(inline_query_id, message_info):
    search_query = message_info.split(',')
    queries = fetcher.get_query_any_column(search_query, columns=['Aufzugsstrecke', 'Versammlungsort', 'Thema', 'PLZ', 'Datum'])
    results=[]
    if queries:
        for q in queries[:45]:
            results.append({ 
                    'type': 'article', \
                    'id' : f'{q[0]}', \
                    'title': f"{q[4]}", \
                    'input_message_content': {'message_text': fetcher.format_postgres_output(q), 'parse_mode': 'HTML'}, \
                    'description': f"{q[1].strftime('%d.%m.%Y.') if q[1] else ''}{q[2].strftime('%H:%M')} {'to' if q[2] else '' } {q[3].strftime('%H:%M')} - {f'{q[5]}; {q[6]}' if q[5] else ''}{q[7] if q[7] else ''}", \
                    })
    else:
        results.append({ 
                    'type': 'article', \
                    'id' : '0', \
                    'title': "There's nothing to show.", \
                    'input_message_content': {'message_text': "There's nothing to show.", 'parse_mode': 'HTML'}, \
                    })
    r = answerInlineQuery(
            inline_query_id=inline_query_id, 
            results=results
            )
    print(r)

def handle_callback_query(chat_id, message_info):
    message, message_id, callback_query_data, callback_query_message_id = message_info
    queries = handle_commands(message)
    if not queries:
        reply = "There's nothing to show."
    else:
        page_number = int(callback_query_data.split()[-1])
        queries_formatted = fetcher.format_postgre_queries(queries)
        page, number_of_pages = message_format_for_postgres(queries_formatted, page_number=page_number)
        reply_markup = make_reply_markup_page_control(page_number, number_of_pages)
        reply = page
        
    editMessageText(
        chat_id=chat_id,
        message_id=callback_query_message_id,
        text=reply,
        reply_markup='' if not queries else reply_markup
    )

def handle_message(chat_id, message_info):
    message, message_id = message_info
    queries = handle_commands(message) 
    keyboard = [["/today", "/tomorrow"], ["/help", "/info"]]
    reply_keyboard_markup = {"keyboard": keyboard, "resize_keyboard": True, "input_field_placeholder": "Select one: [/help to explore more options]"}
    
    if len(queries)>0:
            page_number = 1
            queries_formatted = fetcher.format_postgre_queries(queries)
            page, number_of_pages = message_format_for_postgres(queries_formatted, page_number = 1)
            reply_markup = make_reply_markup_page_control(page_number, number_of_pages)
            reply_markup = reply_markup if reply_markup else reply_keyboard_markup
            r = send_message(
                    chat_id=chat_id, 
                    text=page,
                    reply_to_message_id=message_id,
                    reply_markup=reply_markup
                    )
            print(r)
    elif message == '/start':
        send_message(
            chat_id=chat_id,
            text='Hey there,\nThis bot is made to provide you access to the up-to-date protest events in Berlin.',
            reply_to_message_id=message_id,
            reply_markup=reply_keyboard_markup
        )
    elif message == '/help':
        reply="""◾️What can this bot do?
<b>/start</b>: start the bot
<b>/search [search query]</b>: get the protests with the query in their description. 
For example: <i>/search ukraine</i>
<b>/today</b>: get today's protests
<b>/tomorrow</b>: get tomorrow's protests 
<b>/date [dd.mm.yyyy]</b>: get the protests on that specific date. 
For example: <i>/date 01.05.2030</i>
<b>/help</b>: see the manual
<b>/info</b>: contact me
<b>@ProtestsBerlinBot [search query]</b>: get the protest records with the query in their description or if the query is a date, it returns the records on that date. 
For example: <i>@ProtestsBerlinBot ukraine</i>"""
        send_message(
            chat_id=chat_id,
            text=reply,
            reply_to_message_id=message_id
        )
#        sendVideo(
#                chat_id=chat_id,
#                message_id=message_id,
#                fileaddress='help-telegram-bot.mp4',
#                caption="""◾️What can this bot do?
#<b>/start</b>: start the bot
#<b>/search [search query]</b>: get the protests with the query in their description. For example: /search ukraine 
#<b>/today</b>: get today's protests
#<b>/tomorrow</b>: get tomorrow's protests 
#<b>/date [dd.mm.yyyy]</b>: get the protests on that specific date. For example: /date 01.05.2030
#<b>/help</b>: see the manual
#<b>/info</b>: contact me
#<b>@ProtestsBerlinBot [search query]</b>: get the protest records with the query in their description or if the query is a date, it returns the records on that date. For example @ProtestsBerlinBot ukraine"""
#                )
    else:
        send_message(
            chat_id=chat_id,
            text="Send me the correct message to proceed.",
            reply_to_message_id=message_id,
            reply_markup=reply_keyboard_markup
        )
    
@app.before_request
def block_method():
    ip = str(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
    if request.method == 'GET':
        with open('blocked-ips.txt', 'a') as f:
            f.write(ip)
            f.write('\n')
            f.close()
        abort(403)
    elif request.args != {}:
        abort(403)

@app.route('/', methods=['POST'])
def index():
    msg = request.get_json(force=True)
    print(str(msg))
    with open('message-logger.txt', 'a') as f:
        f.write(str(datetime.datetime.now()))
        f.write(', ')
        f.write(str(msg))
        f.write('\n')
        f.close()
        manage_messages(msg)
    return Response('Ok', status=200)

def main():
    pass
 

if __name__ == "__main__": 


    app.run(host="0.0.0.0", port=5000)

