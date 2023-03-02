import requests
import pytz
import time
from yahoo_fin.stock_info import get_quote_table
from deep_translator import GoogleTranslator
import pandas as pd
import random
from datetime import datetime
from schema import TOKEN, USER_AGENTS
import os

if not ('id—list.csv' in os.listdir()):
    pd.DataFrame(columns=['id']).to_csv('id-list.csv', index=False, header=True)

hong_kong = pytz.timezone('Asia/Hong_Kong')
mountain = pytz.timezone('Canada/Mountain')

translator_zh = GoogleTranslator(target='zh-TW')
translator_en = GoogleTranslator(target='en')
tele_token = ''
impo = '💥'

def get_response():
    cur_time = int(datetime.now(mountain).timestamp())
    token = random.choice(TOKEN)
    user_agent = random.choice(USER_AGENTS)
    header = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'User-Agent': user_agent,
    }
    print(user_agent)
    url = f'https://www.zhitongcaijing.com/immediately/content-list.html?type=all&roll=gt&token={token}&last_update_time={cur_time}&platform=web'
    resp = requests.get(url, headers=header)
    print(f'Code: {resp.status_code}')
    if resp.status_code == 200:
        print(f'Text: {resp.text}')
        if resp.text == '非法请求':
            return False
        else:
            return resp.json()['data']['list']
    else:
        return False


def send_message(whole_paragraph):
    payload = {'chat_id': 0, 'text': whole_paragraph, 'parse_mode': 'HTML',
               'disable_web_page_preview': True}
    response = requests.get(f'https://api.telegram.org/bot{tele_token}/sendMessage', data=payload)


def erase_region(text):
    if '.HK' in text:
        text = text.replace('.HK', '')
    if '.US' in text:
        text = text.replace('.US', '')
    if '.SZ' in text:
        text = text.replace('.SZ', '')
    if '.SH' in text:
        text = text.replace('.SH', '')
    return text


def get_msg():
    data = get_response()
    df_id = pd.read_csv('id-list.csv')
    id_list = df_id['id'].to_list()
    if data != False:
        print(f'Length of Data: {len(data)}')
        if len(data) != 0:
            for i in range(len(data)):
                id = data[i]['immediately_id']
                if not (id in id_list):
                    print(f'id {id} does not in id_list')
                    important = data[i]['important']
                    type = data[i]['type']
                    news_time = data[i]['create_time_desc']
                    whole_paragraph = f'<i>Zhitong</i>\n{news_time}\n'
                    content = data[i]['content']
                    if '</b>' in content:
                        title = content.split('</b>')[0]
                        if '【' in title:
                            title = title.replace('【', '')
                        if '】' in title:
                            title = title.replace('】', '')
                        if '<b>' in title:
                            title = title.replace('<b>', '')
                        text = content.split('</b>')[1]
                        if '智通财经APP获悉，' in text:
                            text = text.replace('智通财经APP获悉，', '')
                        if '智通財經APP訊，' in text:
                            text = text.replace('智通財經APP訊，', '')
                        title_zh = translator_zh.translate(title)
                        title_en = translator_en.translate(title)
                        text_zh = translator_zh.translate(text)
                        text_en = translator_en.translate(text)
                        if important:
                            whole_paragraph += f'{impo}Original{impo}\n【{title_zh}】\n{text_zh}\n'
                        else:
                            whole_paragraph += f'Original\n【{title_zh}】\n{text_zh}\n'
                        whole_paragraph += f'\nGoogle Translate\n【{title_en}】\n{text_en}\n'
                    else:
                        title = content
                        title_zh = translator_zh.translate(title)
                        title_en = translator_en.translate(title)
                        if important:
                            whole_paragraph += f'{impo}Original{impo}\n{title_zh}\n'
                        else:
                            whole_paragraph += f'Original\n{title_zh}\n'
                        whole_paragraph += f'\nGoogle Translate\n{title_en}\n'
                    # extract code
                    if ('（' in title_zh) or ('(' in title_zh):
                        if '(' in title_zh:
                            list_msg = title_zh.split('(')
                        else:
                            list_msg = title_zh.split('（')
                        list_stock_code = []
                        j = 0
                        for i in range(len(list_msg)):
                            msg_dummy = list_msg[i-j]
                            if ('.SH' in msg_dummy) | ('.SZ' in msg_dummy) | ('.HK' in msg_dummy) | ('.US' in msg_dummy):
                                if ')' in msg_dummy:
                                    stock_code = msg_dummy.split(')')[0]
                                else:
                                    stock_code = msg_dummy.split('）')[0]
                                if '.HK' in msg_dummy:
                                    stock_code = stock_code[1:]
                                list_stock_code.append(stock_code)
                            else:
                                list_msg.remove(msg_dummy)
                                j += 1

                        if len(list_stock_code) != 0:
                            # whole_paragraph += f'\n相關股票: \n'
                            whole_paragraph += f'Ticker: \n'
                            for ticker in list_stock_code:
                                # stock price and add link
                                if '.HK' in ticker:
                                    code_choice = ticker.replace('.HK', '')
                                    quote_table = get_quote_table(ticker)
                                    df_quote = pd.DataFrame(quote_table, index=[0])
                                    current_price = round(df_quote.loc[0, 'Quote Price'], 2)
                                    up_down = round(((df_quote.loc[0, 'Quote Price'] / df_quote.loc[
                                        0, 'Previous Close']) - 1) * 100, 2)
                                    up_down_str = str(up_down) + '%'
                                    if up_down >= 0:
                                        whole_paragraph += f'<a href="https://www.tradingview.com/chart/?symbol={code_choice}">{code_choice}</a> ' + 'HK ' + f'{current_price} +{up_down_str}\n'
                                    else:
                                        whole_paragraph += f'<a href="https://www.tradingview.com/chart/?symbol={code_choice}">{code_choice}</a> ' + 'HK ' + f'{current_price} {up_down_str}\n'
                                elif '.US' in ticker:
                                    code_choice = ticker.replace('.US', '')
                                    quote_table = get_quote_table(code_choice)
                                    df_quote = pd.DataFrame(quote_table, index=[0])
                                    current_price = round(df_quote.loc[0, 'Quote Price'], 2)
                                    up_down = round(((df_quote.loc[0, 'Quote Price'] / df_quote.loc[
                                        0, 'Previous Close']) - 1) * 100, 2)
                                    up_down_str = str(up_down) + '%'
                                    if up_down >= 0:
                                        whole_paragraph += f'<a href="https://www.tradingview.com/chart/?symbol={code_choice}">{code_choice}</a> ' + 'US ' + f'{current_price} +{up_down_str}\n'
                                    else:
                                        whole_paragraph += f'<a href="https://www.tradingview.com/chart/?symbol={code_choice}">{code_choice}</a> ' + 'US ' + f'{current_price} {up_down_str}\n'
                                elif '.SH' in ticker:
                                    code_choice = ticker.replace('.SH', '')
                                    whole_paragraph += f'<a href="https://www.tradingview.com/chart/?symbol={code_choice}">{code_choice}</a> ' + 'SH\n'
                                elif '.SZ' in ticker:
                                    code_choice = ticker.replace('.SZ', '')
                                    whole_paragraph += f'<a href="https://www.tradingview.com/chart/?symbol={code_choice}">{code_choice}</a> ' + 'SZ\n'
                                else:
                                    whole_paragraph += f'{ticker}\n'
                    print(whole_paragraph)
                    whole_paragraph = erase_region(whole_paragraph)
                    send_message(whole_paragraph)

                    df_id = pd.concat([df_id, pd.DataFrame({'id': id}, index=[0])], axis=0)
                    df_id.to_csv('id-list.csv', index=False, header=True)


while True:
    try:
        get_msg()
    except:
        pass
    time.sleep(3)