import asyncio
from functools import partial
from time import sleep

import aiohttp

from .credentials import config

token = config.TG_BOT_TOKEN
base_link = f"https://api.telegram.org/bot{token}"


class Message:
    """
    A class to represent and process a Telegram message.

    This class provides a structured way to access various components of a message received in Telegram. It uses properties to access specific parts of the message, such as text, chat information, callback queries, and more.

    Attributes:
        _tg_response (dict): The original message dictionary received from Telegram.

    The class provides properties to access different elements of the message:
        | - `message`: The main message content.
        | - `chat`: Information about the chat.
        | - `chat_id`: Unique identifier for the chat.
        | - `chat_type`: Type of the chat (e.g., private, group).
        | - `message_id`: Unique message identifier.
        | - `message_text`: Text of the message.
        | - `message_info`: Tuple containing message text and message ID.
        | - `inline_query`: Inline query information, if any.
        | - `query`: The inline query text.
        | - `query_id`: Inline query identifier.
        | - `callback_query`: Callback query information, if any.
        | - `callback_query_id`: Callback query identifier.
        | - `callback_query_data`: Data associated with the callback query.
        | - `callback_query_message`: Message associated with the callback query.
        | - `callback_query_message_id`: Message ID of the callback query message.
        | - `callback_query_message_chat`: Chat information of the callback query message.
        | - `callback_query_message_chat_id`: Chat ID of the callback query message.
        | - `callback_query_reply_to_message`: Original message replied to by the callback query.
        | - `callback_query_reply_to_message_message_id`: Message ID of the replied-to message.
        | - `my_chat_member`: Information about changes in chat member status.
        | - `my_chat_member_chat`: Chat information related to the chat member status change.
        | - `my_chat_member_chat_title`: Title of the chat related to the chat member status change.
        | - `my_chat_member_chat_type`: Type of the chat related to the chat member status change.
        | - `my_chat_member_from`: User information of the member whose status in the chat has changed.
        | - `my_chat_member_from_first_name`: First name of the user whose chat member status has changed.
        | - `callback_query_message_info`: A tuple containing various pieces of information about the callback query message.

    Methods:
        _getitem(dic, key): A static method to safely extract a nested value from a dictionary using a key or a tuple of nested keys.
        _extract_tg_response(key): A method to safely extract a nested value by feeding the telegram response dictionary and a key or a tuple of nested keys to _getitem method.
    """

    def __init__(self, tg_response: dict):
        self._tg_response = tg_response
        self._extract_tg_response = partial(self._getitem, self._tg_response)

    @staticmethod
    def _getitem(query, key):
        keys = key if isinstance(key, tuple) else (key,)
        for k in keys:
            if not isinstance(query, dict):
                return None
            query = query.get(k)
        return query

    @property
    def message(self):
        return self._extract_tg_response("message")

    @property
    def message_date(self):
        return self._extract_tg_response(("message", "date"))

    @property
    def chat(self):
        return self._extract_tg_response(("message", "chat"))

    @property
    def chat_id(self):
        return self._extract_tg_response(("message", "chat", "id"))

    @property
    def chat_type(self):
        return self._extract_tg_response(("message", "chat", "type"))

    @property
    def message_id(self):
        return self._extract_tg_response(("message", "message_id"))

    @property
    def message_text(self):
        return self._extract_tg_response(("message", "text"))

    @property
    def message_info(self):
        return (self.message_text, self.message_id, self.message_date)

    @property
    def inline_query(self):
        return self._extract_tg_response("inline_query")

    @property
    def query(self):
        return self._extract_tg_response(("inline_query", "query"))

    @property
    def query_id(self):
        return self._extract_tg_response(("inline_query", "id"))

    @property
    def callback_query(self):
        return self._extract_tg_response("callback_query")

    @property
    def callback_query_id(self):
        return self._extract_tg_response(("callback_query", "id"))

    @property
    def callback_query_data(self):
        return self._extract_tg_response(("callback_query", "data"))

    @property
    def callback_query_message(self):
        return self._extract_tg_response(("callback_query", "message"))

    @property
    def callback_query_message_id(self):
        return self._extract_tg_response(("callback_query", "message", "message_id"))

    @property
    def callback_query_message_chat(self):
        return self._extract_tg_response(("callback_query", "message", "chat"))

    @property
    def callback_query_message_chat_id(self):
        return self._extract_tg_response(("callback_query", "message", "chat", "id"))

    @property
    def callback_query_reply_to_message(self):
        return self._extract_tg_response(
            ("callback_query", "message", "reply_to_message")
        )

    @property
    def callback_query_reply_to_message_message_id(self):
        return self._extract_tg_response(
            ("callback_query", "message", "reply_to_message", "message_id"),
        )

    @property
    def my_chat_member(self):
        return self._extract_tg_response("my_chat_member")

    @property
    def my_chat_member_chat(self):
        return self._extract_tg_response(("my_chat_member", "chat"))

    @property
    def my_chat_member_chat_title(self):
        return self._extract_tg_response(("my_chat_member", "chat", "title"))

    @property
    def my_chat_member_chat_type(self):
        return self._extract_tg_response(("my_chat_member", "chat", "type"))

    @property
    def my_chat_member_from(self):
        return self._extract_tg_response(("my_chat_member", "from"))

    @property
    def my_chat_member_from_first_name(self):
        return self._extract_tg_response(("my_chat_member", "from", "first_name"))

    @property
    def callback_query_message_info(self):
        return (
            self.callback_query_id,
            self.callback_query_reply_to_message_message_id,
            self.callback_query_data,
            self.callback_query_message_id,
        )


def parse_message(msg):
    """
    Parses a message object received from the Telegram API and extracts relevant information.

    This function analyzes a Telegram message dictionary to determine the type of message (inline query, callback query, private, or group) and extracts essential information such as chat ID, message content, and message type.

    :param msg: A dictionary representing a Telegram message, typically received from the Telegram API.
    :type msg: dict

    :return: A tuple containing the chat ID, message information, and the type of message.
             The structure of the returned tuple varies depending on the message type.
    :rtype: tuple

    The function handles different types of Telegram messages:
        | - Inline queries: Returns the query ID, query text, and message type as "inline_query".
        | - Callback queries: Returns the chat ID of the callback message, callback query information, and message type as "callback_query".
        | - Private and group chats: Returns the chat ID, message information, and chat type ("private" or "group").

    Example:
        | For an inline query, it returns (query_id, query_text, "inline_query").
        | For a callback query, it returns (chat_id, callback_query_info, "callback_query").
        | For standard messages, it returns (chat_id, message_info, chat_type).

    Note:
        The function relies on the 'Message' class to process the raw message dictionary into a more structured format.
    """
    msg = Message(msg)
    if msg.inline_query:
        return msg.query_id, msg.query, "inline_query"
    if msg.callback_query:
        return (
            msg.callback_query_message_chat_id,
            msg.callback_query_message_info,
            "callback_query",
        )
    if msg.chat_type == "private":
        return msg.chat_id, msg.message_info, "private"
    elif msg.chat_type == "group":
        return msg.chat_id, msg.message_info, "group"
    elif msg.chat_type == "supergroup":
        return msg.chat_id, msg.message_info, "supergroup"


async def post_json(url, json_data):
    """
    Asynchronously sends a POST request with JSON data and retries on failure.

    This function is a utility to send asynchronous POST requests to a specified URL with JSON-formatted data.
    If the request fails (status code not 200), it retries up to 5 times with a 0.5-second delay between attempts.

    :param url: The URL to which the request is to be sent.
    :type url: str
    :param json_data: The JSON data to be sent in the POST request.
    :type json_data: dict

    :return: The result of the asynchronous operation to post json payload.
    :rtype: Coroutine
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json_data) as response:
            for i in range(5):
                if response.status != 200:
                    sleep(0.5)
                    continue
                else:
                    return await response.text()


async def send_chat_action(chat_id, action="typing"):
    """
    Asynchronously sends a chat action to a Telegram chat.

    This function is used to send various chat actions to inform users in a chat about the ongoing activity (e.g., typing, uploading a photo).

    :param chat_id: Unique identifier for the target chat or username of the target channel.
    :type chat_id: str
    :param action: Type of action to broadcast (e.g., 'typing', 'upload_photo').
    :type action: str, optional

    :return: The result of the asynchronous operation to send a chat action.
    :rtype: Coroutine
    """
    url = f"{base_link}/sendChatAction"
    payload = {"chat_id": chat_id, "action": action}
    r = asyncio.create_task(post_json(url, payload))
    return await r


async def send_message(
    chat_id,
    text,
    reply_to_message_id=None,
    reply_markup=None,
    link_preview_options=None,
):
    """
    Asynchronously sends a message to a Telegram chat.

    This function allows sending a text message to a specified chat in Telegram. Additional parameters allow specifying a reply and custom keyboards.

    :param chat_id: Unique identifier for the target chat or username of the target channel.
    :type chat_id: str
    :param text: The text of the message to be sent.
    :type text: str
    :param reply_to_message_id: If the message is a reply, ID of the original message.
    :type reply_to_message_id: str, optional
    :param reply_markup: Additional interface options in JSON-serialized format.
    :type reply_markup: str, optional
    :param link_preview_options: A dictionary to control link preview behavior. It can include 'is_disabled' (bool) to enable or disable link previews.
    :type link_preview_options: dict, optional

    :return: The result of the asynchronous operation to send a message.
    :rtype: Coroutine
    """

    await asyncio.create_task(send_chat_action(chat_id, action="typing"))
    url = f"{base_link}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if link_preview_options:
        payload["link_preview_options"] = link_preview_options
    r = asyncio.create_task(post_json(url, payload))
    return await r


async def delete_message(chat_id, message_id):
    """
    Asynchronously deletes a message from a Telegram chat.

    This function is used to delete a message in a Telegram chat based on its unique message ID.

    :param chat_id: Unique identifier for the target chat or username of the target channel.
    :type chat_id: str
    :param message_id: Identifier of the message to delete.
    :type message_id: str

    :return: The result of the asynchronous operation to delete a sent message.
    :rtype: Coroutine
    """
    url = f"{base_link}/deleteMessage"
    payload = {"chat_id": chat_id, "message_id": message_id}
    r = asyncio.create_task(post_json(url, payload))
    return await r


async def edit_message_text(
    chat_id, message_id, text, reply_markup=None, link_preview_options=None
):
    """
    Asynchronously edits the text of a message in a Telegram chat.

    This function allows editing the text of an existing message in a Telegram chat. It requires the message ID and the new text. Optionally, it can also update the reply markup.

    :param chat_id: Unique identifier for the target chat or username of the target channel.
    :type chat_id: str
    :param message_id: Identifier of the message to edit.
    :type message_id: str
    :param text: New text to replace the existing message content.
    :type text: str
    :param reply_markup: Additional interface options in JSON-serialized format.
    :type reply_markup: str, optional
    :param link_preview_options: A dictionary to control link preview behavior. It can include 'is_disabled' (bool) to enable or disable link previews.
    :type link_preview_options: dict, optional

    :return: The result of the asynchronous operation to edit a sent message.
    :rtype: Coroutine
    """

    url = f"{base_link}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if link_preview_options:
        payload["link_preview_options"] = link_preview_options
    r = asyncio.create_task(post_json(url, payload))
    return await r


async def answer_callback_query(callback_query_id, text):
    """
    Asynchronously sends a response to a callback query in Telegram.

    This function is used to provide feedback to a user who initiated a callback query in a Telegram bot interaction.

    :param callback_query_id: Unique identifier for the callback query.
    :type callback_query_id: str
    :param text: Text of the notification to be shown to the user.
    :type text: list

    :return: The result of the asynchronous operation to send the callback query.
    :rtype: Coroutine
    """
    url = f"{base_link}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id, "text": text}
    r = asyncio.create_task(post_json(url, payload))
    return await r


async def answer_inline_query(inline_query_id, results):
    """
    Asynchronously sends a response to an inline query in Telegram.

    This function is used to send results in response to an inline query made by a user in a Telegram bot. Inline queries allow users to select from a list of results and send them into the chat.

    :param inline_query_id: Unique identifier for the answered query.
    :type inline_query_id: str
    :param results: A list of results for the inline query. Each item in the list should be a type of InlineQueryResult.
    :type results: list

    :return: The result of the asynchronous operation to send the inline query.
    :rtype: Coroutine
    """
    url = f"{base_link}/answerInlineQuery"
    payload = {
        "inline_query_id": inline_query_id,
        "results": results,
        "cache_time": 200,
    }
    r = asyncio.create_task(post_json(url, payload))
    return await r


async def set_message_reaction(chat_id, message_id, reaction, is_big=False):
    """
    Asynchronously sets a reaction emoji to a specific message in a Telegram chat.

    This function enables a Telegram bot to react to a message within a chat using a specified emoji. The `is_big` parameter allows the choice of a larger animation for the reaction, enhancing the visibility of the reaction.

    :param chat_id: Unique identifier for the target chat or username of the target channel.
    :type chat_id: str
    :param message_id: The identifier of the message to react to.
    :type message_id: str
    :param reaction: The emoji used for the reaction, represented by a value from `ReactionTypeEmoji`.
    :type reaction: str
    :param is_big: Indicates whether the reaction animation should be displayed in a larger size. Defaults to False, showing a standard-sized animation.
    :type is_big: bool, optional

    :return: The result of the asynchronous operation to react to a message.
    :rtype: Coroutine
    """
    url = f"{base_link}/setMessageReaction"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reaction": reaction,
        "is_big": is_big,
    }

    r = asyncio.create_task(post_json(url, payload))
    return await r
