from flask.wrappers import Response
from flask import Flask
from flask import request, abort
import json
from telegram_bot_api import parse_message, \
                                send_message, \
                                deleteMessage, \
                                editMessageText, \
                                message_format_for_postgres, \
                                answerInlineQuery, \
                                sendVideo, \
                                get_calender, \
                                get_next_period_of_time
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
        if parsed_message:
            chat_id, message_info, chat_type = parsed_message
            if chat_type == 'callback_query':
                handle_callback_query(chat_id, message_info)
            elif chat_type == 'private message':
                handle_message(chat_id, message_info)
            elif chat_type == 'inline_query':
                handle_inline_query(inline_query_id=chat_id, message_info=message_info)
    except Exception as e:
        print(e)

def make_reply_markup_page_control(page_number, number_of_pages, command):
    reply_markup=''
    next_page = {'text': '>', 'callback_data': f'page {page_number+1} {command}'}
    previous_page = {'text': '<', 'callback_data': f'page {page_number-1} {command}'}
    if 2<=page_number<number_of_pages:
        reply_markup = {'inline_keyboard': [[previous_page, next_page]]}
    elif (page_number==number_of_pages) and (1<number_of_pages):
            reply_markup = {'inline_keyboard': [[previous_page], ]}
    elif (page_number==1) and (1<number_of_pages):
            reply_markup = {'inline_keyboard': [[next_page], ]}
    return reply_markup

def message_and_reply_markup_format(page_number, queries, command):
    queries_formatted = fetcher.format_postgre_queries(queries)
    page, number_of_pages = message_format_for_postgres(queries_formatted, page_number)
    reply_markup = make_reply_markup_page_control(page_number, number_of_pages, command)
    return reply_markup, page

def handle_commands(message):
    queries = []
    reply_markup = ''
    if message:
        if (message == '/today') or (message == 'Today 🪧'):
            date = datetime.datetime.today().strftime("%Y.%m.%d")
            queries = fetcher.getBySpecificDate(date)
        elif (message == '/tomorrow') or (message == 'Tomorrow 🪧'):
            date = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime("%Y.%m.%d")
            queries = fetcher.getBySpecificDate(date)
        elif (message.startswith('/calender')) or (message == 'Calender 🗓️'):
            start_date = datetime.datetime.today()
            if message.startswith('/calender'):
                start_date_string = ' '.join(message.split(' ')[1:])
                start_date = datetime.datetime.strptime(start_date_string, "%Y-%m-%d %H:%M:%S.%f")
            reply_markup, years = get_calender(start_date)
            queries = [f"Choose a date in {' or '.join(years)}"]
        elif (message == '🔎'):
            queries = ["Send me a text to search:"]
        elif (message == '/weekend') or (message == 'Weekend 🪧'):
            queries = []
            for i in range(7):
                date = datetime.datetime.today() + datetime.timedelta(days=i)
                if date.weekday() in (5, 6):
                    date = date.strftime("%Y.%m.%d")
                    queries.extend( fetcher.getBySpecificDate(date))
        elif (message == '/week') or (message == 'This Week 🪧'):
            queries = []
            for i in range(7):
                date = (datetime.datetime.today() + datetime.timedelta(days=i)).strftime("%Y.%m.%d")
                queries.extend( fetcher.getBySpecificDate(date))
        elif (message == '/info') or (message == 'Info 💁'):
            queries = ["If you have any suggestions, comments, or questions, please don't hesitate to reach out to me. Reach me at reach.s.farhad@gmail.com"]
        elif message.startswith('/date'):
            date = message.split(' ', 1)[-1]
            try:
                date_query = datetime.datetime.strptime(date, '%d.%m.%Y').strftime("%Y.%m.%d")
                queries = fetcher.getBySpecificDate(date_query)
            except:
                queries = ['This command should be used as follows:\n/date Day.Month.Year']
        elif (message == '/help') or (message=='Help ❔'):
            reply="""◾️What can this bot do?
<b>/start</b>: start the bot
<b>[query]</b>: get a list of protests with the query in their description.
<b>/search [query]</b>: get a list of protests with the query in their description. (The same as the one above)
For example: <i>'/search ukraine'</i> or <i>'ukraine'</i>
<b>/today</b>: get a list of today's protests
<b>/tomorrow</b>: get a list of tomorrow's protests
<b>/saturday</b>: get a list of the upcoming saturday's protests
<b>/week</b>: get a list of this week's protests
<b>/date [dd.mm.yyyy]</b>: get a list of protests on that specific date.
For example: <i>'/date 01.05.2030'</i>
<b>/help</b>: see the manual
<b>/info</b>: contact me
With the following command you can search and select a specific protest info in any chat:
<b>@ProtestsBerlinBot [query]</b>: get the protest records with the query in their description or if the query is a date, the records on that date.
For example: <i>'@ProtestsBerlinBot ukraine'</i>"""
            queries = [reply]

        elif not message.startswith('/'):
            message = f"/search {message}"

        if message.startswith('/search'):
            search_query = message.split(' ', 1)[-1].split(',')
            print(search_query)
            queries = fetcher.get_query_any_column(search_query, columns=['Aufzugsstrecke', 'Versammlungsort', 'Thema', 'PLZ', 'Datum'])
            if not queries:
                queries = ["There's nothing to show."]
    return queries, reply_markup

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
    _, message_id, callback_query_data, callback_query_message_id = message_info
    reply_markup = ''
    page_number = 1
    is_pagenumber_in_callback_query = callback_query_data.split()[0] == 'page'
    if isinstance(callback_query_data, str) and is_pagenumber_in_callback_query:
        page_number = int(callback_query_data.split()[1])

    if is_pagenumber_in_callback_query:
        command = ' '.join(callback_query_data.split()[2:])
        queries, reply_markup = handle_commands(command)
    else:
        command = callback_query_data
        queries, reply_markup = handle_commands(command)
    print('callback_query_data:', callback_query_data)
    print('command:', command)
    reply_markup_page, reply = message_and_reply_markup_format(page_number, queries, command)
    if reply_markup_page:
        reply_markup = reply_markup_page
    editMessageText(
        chat_id=chat_id,
        message_id=callback_query_message_id,
        text=reply,
        reply_markup=reply_markup
    )

def handle_message(chat_id, message_info):
    message, message_id = message_info
    queries, reply_markup_main = handle_commands(message)
    # keyboard = [["/today", "/tomorrow"], ["/help", "/info"]]
    keyboard = [["Today 🪧", "Tomorrow 🪧", "🔎"],
                ["This Week 🪧", "Weekend 🪧", "Calender 🗓️"],
                ["Help ❔", "Info 💁"]]
    reply_keyboard_markup = {"keyboard": keyboard, "resize_keyboard": True, "input_field_placeholder": "Select one:"}

    if len(queries)>0:
            reply_markup_page, page = message_and_reply_markup_format(page_number=1, queries=queries, command=message)
            reply_markup = reply_keyboard_markup
            if reply_markup_main:
                reply_markup = reply_markup_main
            elif reply_markup_page:
                reply_markup = reply_markup_page

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
    msg_str = json.dumps(msg)
    msg_http_code = str(msg)
    print(msg_str)
    print(msg_http_code)
    with open('message-logger.txt', 'a') as f:
        f.write(str(datetime.datetime.now()))
        f.write(', ')
        f.write(msg_http_code)
        f.write('\n')
        f.write(msg_str)
        f.write('\n')
        f.close()
    manage_messages(msg)
    return Response('Ok', status=200)

def main():
    pass


if __name__ == "__main__":


    app.run(host="0.0.0.0", port=5000)
