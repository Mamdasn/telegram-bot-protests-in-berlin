import requests
from credentials import config
import datetime

token = config.TG_BOT_TOKEN
base_link = f'https://api.telegram.org/bot{token}'

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

class Message:
    def __init__(self, message: dict):
        self._message = message
    @staticmethod
    def _getitem(dic, key):
        keys = key if isinstance(key, tuple) else (key,)
        query = dic
        for k in keys:
            if not isinstance(query, dict): return None
            query = query.get(k)
        return query
    @property
    def message(self):
        return self._getitem(self._message, 'message')
    @property
    def chat(self):
        return self._getitem(self.message, 'chat')
    @property
    def chat_id(self):
        return self._getitem(self.message, ('chat', 'id'))
    @property
    def chat_type(self):
        return self._getitem(self.message, ('chat', 'type'))
    @property
    def message_id(self):
        if self.chat_type == 'private':
            return self._getitem(self.message, 'message_id')
    @property
    def message_text(self):
        if self.chat_type == 'private':
            return self._getitem(self.message, 'text')
    @property
    def message_info(self):
        return (self.message_text, self.message_id)
    @property
    def inline_query(self):
        return self._getitem(self._message, 'inline_query')
    @property
    def query(self):
        return self._getitem(self.inline_query, 'query')
    @property
    def query_id(self):
        return self._getitem(self.inline_query, 'id')
    @property
    def callback_query(self):
        return self._getitem(self._message, 'callback_query')
    @property
    def callback_query_id(self):
        return self._getitem(self.callback_query, 'id')
    @property
    def callback_query_data(self):
        return self._getitem(self.callback_query, 'data')
    @property
    def callback_query_message(self):
        return self._getitem(self.callback_query, 'message')
    @property
    def callback_query_message_id(self):
        return self._getitem(self.callback_query_message, 'message_id')
    @property
    def callback_query_reply_to_message(self):
        return self._getitem(self.callback_query_message, 'reply_to_message')
    @property
    def callback_query_reply_to_message_message_id(self):
        return self._getitem(self.callback_query_reply_to_message, 'message_id')
    @property
    def callback_query_reply_to_message_text(self):
        return self._getitem(self.callback_query_reply_to_message, 'text')
    @property
    def callback_query_reply_to_message_from(self):
        return self._getitem(self.callback_query_reply_to_message, 'from')
    @property
    def callback_query_reply_to_message_from_chat_id(self):
        return self._getitem(self.callback_query_reply_to_message_from, 'id')

def parse_message(msg):
    """
    Parses a message object received from the Telegram API.

    Args:
        msg (dict): A dictionary representing a Telegram message.

    Returns:
        chat_id (int): The ID of the chat the message was sent in.
        message_info (list): A list containing information about the message.
        message_type (str): 'private message' to indicate the type of the returned message.
    """
    msg = Message(msg)
    if msg.inline_query:
        return msg.query_id, msg.query, 'inline_query'
    if msg.callback_query:
        message_info = [msg.callback_query_reply_to_message_text,
                        msg.callback_query_reply_to_message_message_id,
                        msg.callback_query_data,
                        msg.callback_query_message_id]
        return msg.callback_query_reply_to_message_from_chat_id, message_info, 'callback_query'
    if msg.chat_type == 'private':
        return msg.chat_id, msg.message_info, 'private message'

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
