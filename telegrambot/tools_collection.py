import datetime

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
