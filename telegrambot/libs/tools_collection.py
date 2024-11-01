import datetime


def get_next_period_of_time(number_of_days, start_date=None):
    """
    Generate a list of dates for a given number of days starting from a specified date.

    :param number_of_days: The number of days to include in the list.
    :type number_of_days: int
    :param start_date: The date to start from. If None, today's date is used.
    :type start_date: datetime.datetime, optional
    :return: A list of dates in the format 'DD.MM.YY'.
    :rtype: list[str]
    """
    if not start_date:
        start_date = datetime.datetime.today()
    date_list = [
        (start_date + datetime.timedelta(days=i)).strftime("%d.%m.%y")
        for i in range(number_of_days)
    ]
    return date_list


def get_calender(start_date):
    """
    Generate a calendar layout for a 24-day period starting from a given date.

    :param start_date: The date to start the calendar from.
    :type start_date: datetime.datetime
    :return: A tuple containing the calendar layout and the set of years in the period.
    :rtype: (dict, set[str])
    """
    number_of_days = 24
    days = [[]]
    years = []
    for i, d in enumerate(
        get_next_period_of_time(number_of_days=number_of_days, start_date=start_date)
    ):
        row = i // 4
        if len(days) == row:
            days.append([])
        exact_date = start_date + datetime.timedelta(days=i)
        date = exact_date.strftime("%d.%m.%Y")
        # month = date.split(".")[1]
        day = date.split(".")[0]
        years.append(str(exact_date.year))
        short_month_name = exact_date.strftime("%b")
        days[row].append(
            {"text": f"{short_month_name}. {day}", "callback_data": f"/date {date}"}
        )
    days.append([])
    today = datetime.datetime.today()
    if start_date.strftime("%d.%m.%Y") != today.strftime("%d.%m.%Y"):
        previous_start_date = start_date + datetime.timedelta(days=-number_of_days)
        days[-1].append(
            {"text": "<", "callback_data": f"/calender {previous_start_date}"}
        )
    days[-1].append(
        {"text": f"{', '.join(set(years))}", "callback_data": f"/calender {start_date}"}
    )
    next_start_date = start_date + datetime.timedelta(days=number_of_days)
    days[-1].append({"text": ">", "callback_data": f"/calender {next_start_date}"})
    reply_markup = {"inline_keyboard": days}
    return reply_markup, set(years)


def get_remaining_days_in_current_month():
    """
    Calculate the remaining days in the current month from today.

    :return: A list of remaining days in the current month.
    :rtype: list[int]
    """
    now = datetime.datetime.now()
    next_month = (
        datetime.datetime(now.year, now.month + 1, 1)
        if now.month != 12
        else datetime.datetime(now.year + 1, 1, 1)
    )
    last_day_of_current_month = next_month - datetime.timedelta(days=1)
    remaining_days = [day for day in range(now.day, last_day_of_current_month.day + 1)]
    return remaining_days


def message_format_for_postgres(queries, page_number=1, length_of_message=3000):
    """
    Format a list of queries for display, splitting into pages if necessary.

    :param queries: A list of SQL queries.
    :type queries: list[str]
    :param page_number: The page number to display, defaults to 1.
    :type page_number: int, optional
    :param length_of_message: The maximum length of the message, defaults to 3000.
    :type length_of_message: int, optional
    :return: A tuple containing the formatted page of queries and the total number of pages.
    :rtype: (str, int)
    """
    queries = [f"{q}\n" for q in queries]
    queries_len = [len(q) for q in queries]
    query_indexes_for_current_page = [[]]
    number_of_pages = 1
    for i, ql in enumerate(queries_len):
        length_of_current_page = sum(
            [queries_len[qicp] for qicp in query_indexes_for_current_page[-1]]
        )
        if length_of_current_page + ql > length_of_message:
            if i == 0:
                break
            number_of_pages += 1
            query_indexes_for_current_page.append([])

        query_indexes_for_current_page[-1].append(i)

    page = (
        "".join([queries[i] for i in query_indexes_for_current_page[page_number - 1]])
        if page_number <= number_of_pages
        else ""
    )
    return page, number_of_pages


def make_reply_markup_page_control(page_number, number_of_pages, command):
    """
    Create a reply markup for page control in an interactive interface.

    :param page_number: The current page number.
    :type page_number: int
    :param number_of_pages: The total number of pages available.
    :type number_of_pages: int
    :param command: The command to execute when a page control is activated.
    :type command: str
    :return: The reply markup for controlling pages.
    :rtype: dict
    """
    reply_markup = ""
    next_page = {"text": ">", "callback_data": f"page {page_number + 1} {command}"}
    previous_page = {"text": "<", "callback_data": f"page {page_number - 1} {command}"}
    if 2 <= page_number < number_of_pages:
        reply_markup = {"inline_keyboard": [[previous_page, next_page]]}
    elif (page_number == number_of_pages) and (1 < number_of_pages):
        reply_markup = {
            "inline_keyboard": [
                [previous_page],
            ]
        }
    elif (page_number == 1) and (1 < number_of_pages):
        reply_markup = {
            "inline_keyboard": [
                [next_page],
            ]
        }
    return reply_markup
