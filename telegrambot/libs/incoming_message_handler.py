import asyncio
import datetime
from random import choice as pick_randomly

from .telegram_bot_api import (
    answerCallbackQuery,
    answerInlineQuery,
    editMessageText,
    parse_message,
    send_message,
    setMessageReaction,
)
from .tools_collection import get_calender  # get_next_period_of_time,
from .tools_collection import (
    make_reply_markup_page_control,
    message_format_for_postgres,
)

fetcher = None


def set_fetcher(created_fetcher):
    """
    Sets the global fetcher by the given fetcher value

    :param created_fetcher: The created fetcher in the main thread for the communication with postgresql.
    :type page_number: Fetchpostgres

    :return: None
    :rtype: NoneType
    """
    global fetcher
    fetcher = created_fetcher


def message_and_reply_markup_format(page_number, queries, command):
    """
    Formats the given queries into a paginated message and generates reply markup for page control.

    This function takes a list of queries, formats them for display, and organizes them into a paginated structure. It also generates a reply markup for navigating between pages.

    :param page_number: The current page number in the pagination.
    :type page_number: int
    :param queries: A list of query results to be formatted and displayed.
    :type queries: list
    :param command: The original command or query that initiated the request.
    :type command: str

    :return: A tuple containing the reply markup for pagination and the formatted message string.
    :rtype: tuple

    The function utilizes a 'fetcher' module to format query results and handles the pagination logic internally, returning both the paginated text and the navigation controls.
    """
    queries_formatted = fetcher.format_postgre_queries(queries)
    page, number_of_pages = message_format_for_postgres(queries_formatted, page_number)
    reply_markup = make_reply_markup_page_control(page_number, number_of_pages, command)
    return reply_markup, page


def manage_messages(msg):
    """
    Manages incoming messages, parses them, and routes them to appropriate handlers based on chat type.

    This function acts as a central message handler in a Telegram bot, processing incoming messages and directing them to specific functions based on the type of chat or query.

    :param msg: The incoming message from Telegram.
    :type msg: dict

    :return: None. The function processes messages and triggers other functions without returning a value.
    :rtype: NoneType

    The function handles different types of interactions like callback queries, private messages, group messages, and inline queries. It uses a 'parse_message' function to extract necessary information and then calls the relevant handler such as 'handle_callback_query', 'handle_message', or 'handle_inline_query'.

    Exception handling is implemented to catch and log any errors during message processing.
    """
    try:
        parsed_message = parse_message(msg)
        if parsed_message:
            chat_id, message_info, chat_type = parsed_message
            if chat_type == "callback_query":
                handle_callback_query(chat_id, message_info)
            elif chat_type in ("private", "group", "supergroup"):
                handle_message(chat_id, message_info, chat_type)
            elif chat_type == "inline_query":
                handle_inline_query(inline_query_id=chat_id, message_info=message_info)
    except Exception as e:
        print(e)


def handle_commands(message):
    """
    Handles the commands received in a message and generates responses for a Telegram bot.

    This function interprets the input message as a command and provides appropriate responses, which can include fetching data from a database, generating a custom keyboard, or sending predefined responses. It supports a variety of commands for different functionalities.

    :param message: The message text received from the user, which may contain commands or other queries.
    :type message: str

    :return: A tuple containing a list of response strings (queries) and a reply markup if applicable.
    :rtype: tuple

    Supported Commands:
       | - "/start": Greeting message and bot introduction.
       | - "/today", "Today ✊": Fetches events for the current day.
       | - "/tomorrow", "Tomorrow 📢": Fetches events for the next day.
       | - "/week", "Week 📣": Fetches events for the current week.
       | - "/weekend", "Weekend 🪧": Fetches events for the upcoming weekend.
       | - "/date [dd.mm.yyyy]": Fetches events for a specific date.
       | - "Register a Protest": Provides a like to register a protest meeting notice.
       | - "/info", "Info/Donation 💁": Provides contact information.
       | - "/help", "Help ❔": Displays help information.
       | - "/search", "🔎": Initiates a search based on the provided query.
       | - Any other text: Treated as a search query.

    The function also handles date-specific queries and provides a mechanism for calendar-based event selection.

    Note:
        The function relies on an external 'fetcher' module to retrieve data from a database based on the commands.
    """
    queries = []
    reply_markup = ""
    if message:
        if message == "/start":
            queries = [
                "Hey there,\nThis bot is made to provide you access to the up-to-date protest events in Berlin."
            ]
        elif (message == "/today") or (message == "Today ✊"):
            date = datetime.datetime.today().strftime("%Y.%m.%d")
            queries = fetcher.getBySpecificDate(date)
        elif (message == "/tomorrow") or (message == "Tomorrow 📢"):
            date = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime(
                "%Y.%m.%d"
            )
            queries = fetcher.getBySpecificDate(date)
        elif (message.startswith("/calender")) or (message == "Calendar 🗓️"):
            start_date = datetime.datetime.today()
            if message.startswith("/calender"):
                start_date_string = " ".join(message.split(" ")[1:])
                start_date = datetime.datetime.strptime(
                    start_date_string, "%Y-%m-%d %H:%M:%S.%f"
                )
            reply_markup, years = get_calender(start_date)
            queries = [f"Choose a date in {' or '.join(years)}"]
        elif (message == "/weekend") or (message == "Weekend 🪧"):
            queries = []
            for i in range(7):
                date = datetime.datetime.today() + datetime.timedelta(days=i)
                if date.weekday() in (5, 6):
                    date = date.strftime("%Y.%m.%d")
                    queries.extend(fetcher.getBySpecificDate(date))
        elif (message == "/week") or (message == "Week 📣"):
            queries = []
            for i in range(7):
                date = (
                    datetime.datetime.today() + datetime.timedelta(days=i)
                ).strftime("%Y.%m.%d")
                queries.extend(fetcher.getBySpecificDate(date))
        elif (message == "/info") or (message == "Info/Donation 💁"):
            queries = [
                "If you have any suggestions, comments, or questions, please don't hesitate to reach out to me. Reach me at reach.s.farhad@gmail.com\nMy ton coin wallet address for donations: \nUQAqLrv2LMWy0gD6obOSCX9C5g_YCRvjjDqo7Ui1JYPz6aOh"
            ]
        elif message == "Register a Protest":
            queries = [
                "For instructions on registering a Versammlungsanzeige refer to here: https://www.berlin.de/polizei/service/versammlungsbehoerde"
            ]
        elif message.startswith("/date"):
            date = message.split(" ", 1)[-1]
            try:
                date_query = datetime.datetime.strptime(date, "%d.%m.%Y").strftime(
                    "%Y.%m.%d"
                )
                queries = fetcher.getBySpecificDate(date_query)
            except Exception as e:
                print(e)
                queries = [
                    "This command should be used as follows:\n/date Day.Month.Year"
                ]
        elif (message == "/help") or (message == "Help ❔"):
            reply = """◾️What can this bot do?
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

        elif message == "/search":
            queries = [
                "Search through protests in Berlin by sending: \n/search query \nTo get the manual, send /help."
            ]
        elif message == "🔎":
            queries = ["Send me a text to search:"]
        elif not message.startswith("/"):
            message = f"/search {message}"

        if message.startswith("/search") and (message != "/search"):
            search_query = message.split(" ", 1)[-1].split(",")
            print(search_query)
            queries = fetcher.get_query_any_column(
                search_query,
                columns=["Aufzugsstrecke", "Versammlungsort", "Thema", "PLZ", "Datum"],
            )
        if not queries:
            queries = ["There's nothing to show."]
    return queries, reply_markup


def handle_message(chat_id, message_info, chat_type="private"):
    """
    Processes and responds to a message received in a Telegram chat.

    This function handles user messages, generates a custom keyboard for interaction, and sends a response message. It has different behaviors for private and group chats.

    :param chat_id: Unique identifier for the target chat or username of the target channel.
    :type chat_id: int
    :param message_info: Tuple containing the message text and message ID.
    :type message_info: tuple
    :param chat_type: Type of the chat, defaults to "private". Can also be "group".
    :type chat_type: str, optional

    The function generates a custom keyboard layout for private chats and handles commands differently in group chats. It uses the `handle_commands` and `send_message` functions to process the commands and send responses.

    :return: None. The function sends messages and handles responses asynchronously.
    :rtype: NoneType

    Note:
        In group chats, the function only processes messages that start with "/" (commands).
    """
    message, message_id, _ = message_info

    if not message:
        return

    keyboard = [
        ["Today ✊", "Tomorrow 📢", "🔎"],
        ["Week 📣", "Weekend 🪧", "Calendar 🗓️"],
        [
            "Info/Donation 💁",
            {
                "text": "Source Code 📟",
                "web_app": {
                    "url": "https://github.com/Mamdasn/telegram-bot-protests-in-berlin"
                },
            },
        ],
    ]
    emojies = [
        "🕊",
    ]

    reply_keyboard_markup = {
        "keyboard": keyboard,
        "resize_keyboard": True,
        "input_field_placeholder": "Select one:",
    }

    # Commands explicitly meant for bots in groups (e.g., /command@bot_username).
    if chat_type in ("group", "supergroup"):
        if "@" not in message:
            return
        else:
            # To remove @telegrambot_username from `/search@telegrambot_username query`
            bot_username_start = message.rfind("@")
            bot_username_end = message.find(" ", bot_username_start)
            if bot_username_end == -1:
                message = message[:bot_username_start]
            else:
                message = message[:bot_username_start] + message[bot_username_end:]
            reply_keyboard_markup = None

    queries, reply_markup_main = handle_commands(message)

    if len(queries) > 0:
        reply_markup_page, page = message_and_reply_markup_format(
            page_number=1, queries=queries, command=message
        )

        if reply_markup_main:
            reply_markup = reply_markup_main
        elif reply_markup_page:
            reply_markup = reply_markup_page
        else:
            reply_markup = reply_keyboard_markup

        reaction = [{"type": "emoji", "emoji": pick_randomly(emojies)}]
        r = asyncio.run(setMessageReaction(chat_id, message_id, reaction))
        print("React response:", r)
        r = asyncio.run(
            send_message(
                chat_id=chat_id,
                text=page,
                reply_to_message_id=message_id,
                reply_markup=reply_markup,
                link_preview_options={"is_disabled": True},
            )
        )
        print("Sent response:", r)


def handle_inline_query(inline_query_id, message_info):
    """
    Processes an inline query received in a Telegram chat and sends back results.

    The function is used for handling inline queries that allow users to search for and select from a list of results within the Telegram chat interface.

    :param inline_query_id: Unique identifier for the received inline query.
    :type inline_query_id: str
    :param message_info: The query string that the user has entered in the inline query.
    :type message_info: str

    The function processes the search query, fetches relevant results from a database, formats them, and sends them back to the user as inline query results.

    :return: None. The function sends inline query responses asynchronously.
    :rtype: NoneType

    Note:
        The function formats the fetched data into a specific structure required by Telegram for inline query results.
    """
    search_query = message_info.split(",")
    queries = fetcher.get_query_any_column(
        search_query,
        columns=["Aufzugsstrecke", "Versammlungsort", "Thema", "PLZ", "Datum"],
    )
    results = []
    if queries:
        for q in queries[:45]:
            results.append(
                {
                    "type": "article",
                    "id": f"{q[0]}",
                    "title": f"{q[4]}",
                    "input_message_content": {
                        "message_text": fetcher.format_postgres_output(q),
                        "parse_mode": "HTML",
                    },
                    "description": f"{q[1].strftime('%d.%m.%Y.') if q[1] else ''}{q[2].strftime('%H:%M')} {'to' if q[2] else '' } {q[3].strftime('%H:%M')} - {f'{q[5]}; {q[6]}' if q[5] else ''}{q[7] if q[7] else ''}",
                }
            )
    else:
        results.append(
            {
                "type": "article",
                "id": "0",
                "title": "There's nothing to show.",
                "input_message_content": {
                    "message_text": "There's nothing to show.",
                    "parse_mode": "HTML",
                },
            }
        )
    r = asyncio.run(answerInlineQuery(inline_query_id=inline_query_id, results=results))
    print(r)


def handle_callback_query(chat_id, message_info):
    """
    Processes a callback query received from a Telegram chat interaction.

    This function handles the callback query by extracting relevant information from it, determining the appropriate response, and then sending this response back to the Telegram chat. It also supports pagination through callback queries.

    :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername).
    :type chat_id: int
    :param message_info: Tuple containing information about the callback query and the related message.
                         Structure: (callback_query_id, message_id, callback_query_data, callback_query_message_id).
    :type message_info: tuple

    The function parses the callback query data, checks if it contains pagination information, and processes the command accordingly. It then formats a reply message and updates the message text in the Telegram chat using the 'editMessageText' function.

    :return: None. The function performs its operations asynchronously and sends responses directly to the Telegram chat.
    :rtype: NoneType

    Note:
        The function relies on 'answerCallbackQuery' to send an acknowledgement to the callback query and 'editMessageText' to modify the message based on the callback query's data.
    """
    (
        callback_query_id,
        message_id,
        callback_query_data,
        callback_query_message_id,
    ) = message_info
    reply_markup = ""
    page_number = 1
    is_pagenumber_in_callback_query = callback_query_data.split()[0] == "page"
    if isinstance(callback_query_data, str) and is_pagenumber_in_callback_query:
        page_number = int(callback_query_data.split()[1])

    if is_pagenumber_in_callback_query:
        command = " ".join(callback_query_data.split()[2:])
        queries, reply_markup = handle_commands(command)
    else:
        command = callback_query_data
        queries, reply_markup = handle_commands(command)
    print("callback_query_data:", callback_query_data)
    print("command:", command)
    reply_markup_page, reply = message_and_reply_markup_format(
        page_number, queries, command
    )
    if reply_markup_page:
        reply_markup = reply_markup_page
    asyncio.run(answerCallbackQuery(callback_query_id, text=""))
    r = asyncio.run(
        editMessageText(
            chat_id=chat_id,
            message_id=callback_query_message_id,
            text=reply,
            reply_markup=reply_markup,
            link_preview_options={"is_disabled": True},
        )
    )
    print(r)
