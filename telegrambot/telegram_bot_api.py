import aiohttp
import asyncio
from credentials import config

token = config.TG_BOT_TOKEN
base_link = f'https://api.telegram.org/bot{token}'

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
        return self._getitem(self.message, 'message_id')
    @property
    def message_text(self):
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
    def callback_query_message_chat(self):
        return self._getitem(self.callback_query_message, 'chat')
    @property
    def callback_query_message_chat_id(self):
        return self._getitem(self.callback_query_message_chat, 'id')
    @property
    def callback_query_reply_to_message(self):
        return self._getitem(self.callback_query_message, 'reply_to_message')
    @property
    def callback_query_reply_to_message_message_id(self):
        return self._getitem(self.callback_query_reply_to_message, 'message_id')
    @property
    def my_chat_member(self):
        return self._getitem(self._message, 'my_chat_member')
    @property
    def my_chat_member_chat(self):
        return self._getitem(self.my_chat_member, 'chat')
    @property
    def my_chat_member_chat_title(self):
        return self._getitem(self.my_chat_member_chat, 'title')
    @property
    def my_chat_member_chat_type(self):
        return self._getitem(self.my_chat_member_chat, 'type')
    @property
    def my_chat_member_from(self):
        return self._getitem(self.my_chat_member, 'from')
    @property
    def my_chat_member_from_first_name(self):
        return self._getitem(self.my_chat_member_from, 'first_name')

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
        message_info = [msg.callback_query_reply_to_message_message_id,
                        msg.callback_query_data,
                        msg.callback_query_message_id]
        return msg.callback_query_message_chat_id, message_info, 'callback_query'
    if msg.chat_type == 'private':
        return msg.chat_id, msg.message_info, 'private'
    if msg.chat_type == 'group':
        return msg.chat_id, msg.message_info, 'group'

async def post_json(url, json_data):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json_data) as response:
            return await response.text()

async def sendChatAction(chat_id, action='typing'):
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
    r = asyncio.create_task(post_json(url, payload))
    return await r

async def send_message(chat_id, text, reply_to_message_id=None, reply_markup=None):
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
    asyncio.create_task(sendChatAction(chat_id, action='typing'))
    url = f"{base_link}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'disable_web_page_preview': True, 'parse_mode': 'HTML'}
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = reply_markup
    r = asyncio.create_task(post_json(url, payload))
    return await r

async def deleteMessage(chat_id, message_id):
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
    r = asyncio.create_task(post_json(url, payload))
    return await r

async def editMessageText(chat_id, message_id, text, reply_markup=None):
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
    url = f"{base_link}/editMessageText"
    payload = {'chat_id': chat_id, 'message_id': message_id, 'text': text, 'disable_web_page_preview': True, 'parse_mode': 'HTML'}
    if reply_markup:
        payload['reply_markup'] = reply_markup
    r = asyncio.create_task(post_json(url, payload))
    return await r

async def answerInlineQuery(inline_query_id, results):
    url = f"{base_link}/answerInlineQuery"
    payload = {'inline_query_id': inline_query_id, 'results': results, 'cache_time': 200}
    r = asyncio.create_task(post_json(url, payload))
    return await r
