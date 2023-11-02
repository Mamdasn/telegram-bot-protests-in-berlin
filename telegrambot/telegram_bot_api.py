import requests
from credentials import config
import datetime 

token = config.TG_BOT_TOKEN
base_link = f'https://api.telegram.org/bot{token}'

# webhook = 'https://api.telegram.org/bot{token}/setWebhook
# delete a webhook = 'https://api.telegram.org/bot{token}/deleteWebhook'
# get updates = 'https://api.telegram.org/bot{token}/getUpdates'

#def message_format_for_postgres1(queries, page_number=1, length_of_message=3500):
#    queries = [f"{q}\n" for q in queries]
#    queries_len = [len(q) for q in queries]
#    
#    # Concatenate the queries into pages
#    pages = []
#    current_page = ''
#    for query in queries:
#        if len(current_page) + len(query) <= length_of_message:
#            current_page += query
#        else:
#            pages.append(current_page)
#            current_page = query
#    if current_page:
#        pages.append(current_page)
#    
#    number_of_pages = len(pages)
#    
#    # Return the requested page number and the number of pages
#    if page_number > 0 and page_number <= number_of_pages:
#        return pages[page_number - 1], number_of_pages
#    else:
#        return '', number_of_pages

def get_next_period_of_time(number_of_days, start_date=None):
    if not start_date:
        start_date = datetime.datetime.today()
    date_list = [(start_date + datetime.timedelta(days=i)).strftime('%d.%m.%y') for i in range(number_of_days)]
    return date_list

def get_calender(start_date):
    number_of_days = 24
    days=[[]]
    years = []
    for i, d in enumerate(get_next_period_of_time(number_of_days=number_of_days, start_date=start_date)):
        row = i // 4
        if len(days)==row:
            days.append([])
        exact_date = start_date + datetime.timedelta(days=i)
        date = exact_date.strftime("%d.%m.%Y")
        month = date.split('.')[1]
        day   = date.split('.')[0]
        years.append(str(exact_date.year))
        short_month_name = exact_date.strftime('%b')
        days[row].append({'text': f"{short_month_name}. {day}", 'callback_data': f'/date {date}'})
    days.append([])
    today = datetime.datetime.today()
    print('start_date:', start_date.strftime("%d.%m.%Y"), 'today:', today.strftime("%d.%m.%Y"))
    if start_date.strftime("%d.%m.%Y")!=today.strftime("%d.%m.%Y"):
        previous_start_date = start_date + datetime.timedelta(days=-number_of_days)
        days[-1].append({'text': f"<", 'callback_data': f'/calender {previous_start_date}'})
    days[-1].append({'text': f"{', '.join(set(years))}", 'callback_data': f'/calender {start_date}'})
    next_start_date = start_date + datetime.timedelta(days=number_of_days)
    days[-1].append({'text': f">", 'callback_data': f'/calender {next_start_date}'})
    reply_markup = {'inline_keyboard': days}
    print('reply_markup:', reply_markup)
    return reply_markup, set(years)

def get_remaining_days_in_current_month():
    now = datetime.datetime.now()
    next_month = datetime.datetime(now.year, now.month + 1, 1) if now.month != 12 else datetime.datetime(now.year + 1, 1, 1)
    last_day_of_current_month = next_month - datetime.timedelta(days=1)
    remaining_days = [day for day in range(now.day, last_day_of_current_month.day + 1)]
    return remaining_days

def message_format_for_postgres(queries, page_number=1, length_of_message=4000):
    queries = [f"{q}\n" for q in queries]
    queries_len = [len(q) for q in queries]
    query_indexes_for_current_page = [[]]
    number_of_pages = 1
    for i, ql in enumerate(queries_len):
        length_of_current_page = sum([queries_len[qicp] for qicp in query_indexes_for_current_page[-1]])
        if length_of_current_page + ql > length_of_message:
            if i == 0:
                break
            number_of_pages += 1
            query_indexes_for_current_page.append([])
            
        query_indexes_for_current_page[-1].append(i)
            
    page = ''.join(
                [queries[i] for i in query_indexes_for_current_page[page_number-1]]
                ) if page_number <= number_of_pages else ''
    return page, number_of_pages

def parse_message(msg):
    """
    Parses a message object received from the Telegram API.

    Args:
        msg (dict): A dictionary representing a Telegram message.

    Returns:
        chat_id (int): The ID of the chat the message was sent in.
        message_info (list): A list containing information about the message.
        message_type (str): Either 'callback_query' or 'message'.
    """
    # inline_query check
    inline_query = msg.get('inline_query')
    if inline_query:
        search_query = inline_query.get('query')
        inline_query_id = inline_query.get('id')
        return inline_query_id, search_query, 'inline_query'

    # callback_data check
    callback_query = msg.get('callback_query')
    if callback_query:
        callback_query_id = callback_query.get('id')
        callback_query_data = callback_query.get('data')
        message = callback_query.get('message')
        callback_query_message_id = message.get('message_id')
        reply_to_message = message.get('reply_to_message', None)
        if reply_to_message == None:
            return None, None, None
        message_id = reply_to_message.get('message_id')
        message_text = reply_to_message.get('text')
        dice = reply_to_message.get('dice')
        dice_value = dice.get('value') if dice else None
        from_user = reply_to_message.get('from')
        chat_id = from_user.get('id')

        message_info = [message_text, message_id, callback_query_data, callback_query_message_id, dice_value]
        return chat_id, message_info, 'callback_query'


    # message check
    message = msg.get('message')
    if message:
        chat = message.get('chat')
        chat_id = chat.get('id')
        chat_type = chat.get('type')
        if chat_type == 'private': 
            message_id = message.get('message_id')
            txt = message.get('text')
            dice = message.get('dice')
            dice_value = dice.get('value') if dice else None
            message_info = [txt, message_id, dice_value]
            return chat_id, message_info, 'message'

    return None, None, None
    
def sendChatAction(chat_id, action='typing'): 
    """
    Parameters:
    ----------
    chat_id (str):
        Unique identifier for the target chat or username of the target channel
    action (str):
        Type of action to broadcast. Choose one, depending on what the user is about to receive: typing for text messages, upload_photo for photos, record_video or upload_video for videos, record_voice or upload_voice for voice notes, upload_document for general files, choose_sticker for stickers, find_location for location data, record_video_note or upload_video_note for video notes.
    ----------
    Return:
        Request response
    """
    url = f"{base_link}/sendChatAction"
    payload = {'chat_id': chat_id, 'action': action}
    r = requests.post(url, json=payload)
    return r

def send_message(chat_id, text, reply_to_message_id=None, reply_markup=None):
    """
    Parameters:
    ----------
    chat_id (str):
        Unique identifier for the target chat or username of the target channel
    reply_to_message_id (str):
        If the message is a reply, ID of the original message
    reply_markup (str):
        Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
    ----------
    Return:
        Request response
    """
    sendChatAction(chat_id, action='typing')
    url = f"{base_link}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = reply_markup
    r = requests.post(url, json=payload)
    return r

def deleteMessage(chat_id, message_id):
    """
    Parameters:
    ----------
    chat_id (str):
        Unique identifier for the target chat or username of the target channel
    message_id (str):
        Identifier of the message to delete
    ----------
    Return:
        Request response
    """
    url = f"{base_link}/deleteMessage"
    payload = {'chat_id': chat_id, 'message_id': message_id}
    r = requests.post(url, json=payload)
    return r

def editMessageText(chat_id, message_id, text, reply_markup=None):
    """
    Parameters:
    ----------
    chat_id (str):
        Unique identifier for the target chat or username of the target channel
    message_id (str):
        Required if inline_message_id is not specified. Identifier of the message to edit
    ----------
    Return:
        Request response
    """
    #sendChatAction(chat_id, action='typing')
    url = f"{base_link}/editMessageText"
    payload = {'chat_id': chat_id, 'message_id': message_id, 'text': text, 'parse_mode': 'HTML'}
    if reply_markup:
        payload['reply_markup'] = reply_markup
    r = requests.post(url, json=payload)
    return r

def answerInlineQuery(inline_query_id, results):
    url = f"{base_link}/answerInlineQuery"
    payload = {'inline_query_id': inline_query_id, 'results': results, 'cache_time': 300}
    r = requests.post(url, json=payload)
    return r

def sendVideo(chat_id, fileaddress, message_id=None, caption=None):
    sendChatAction(chat_id, action='upload_video')
    url = f"{base_link}/sendVideo"
    payload = {
        'chat_id': chat_id,
        'parse_mode': 'HTML',
        'allow_sending_without_reply': True,
        'supports_streaming': True,
        'reply_to_message_id': message_id,
        'caption': caption,
    }
    with open(fileaddress, 'rb') as video:
        files = {
            'video': video.read(),
        }
    with requests.Session() as session:
        r = session.post(url, data=payload, files=files)
    return r


