import finlab
from finlab import data
from flask import Flask, request, abort
import requests, os
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage, FollowEvent, UnfollowEvent
from io import BytesIO
import pandas as pd

FINLAB_TOKEN = os.environ["FINLAB_TOKEN"]
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

def search_and_extract(df, search_column, search_values, result_column):
    """
    Search for rows in a DataFrame based on values in a specified column,
    and extract values from another specified column for the matching rows.

    Parameters:
    - df: DataFrame
    - search_column: str, the column to search for values
    - search_values: list or array, values to use as keys for searching
    - result_column: str, the column from which to extract values for matching rows

    Returns:
    - DataFrame with search values and corresponding result values
    """
    result_values = []

    for value_to_search in search_values:
        matching_row = df[df[search_column] == value_to_search]

        if not matching_row.empty:
            result_value = matching_row[result_column].values[0]
            result_values.append(result_value)
        else:
            result_values.append(None)

    result_df = pd.DataFrame({search_column: search_values, result_column: result_values})
    return result_df

def finlab_setting():
    finlab.login(FINLAB_TOKEN)
    data.set_storage(data.FileStorage( "./db"))

def calculate_top10_TWpricetock():
    price = data.get('price:收盤價')
    market_cap = data.get('etl:market_value')
    company_basic_info = data.get('company_basic_info')

    sorted_market = market_cap.T.sort_values(by=market_cap.index[-1], ascending=False).T
    sorted_price = price.T.sort_values(by=price.index[-1], ascending=False).T

    top10_price_df =  sorted_price.iloc[-1, :10].to_frame().reset_index(drop=True)

    top10_price  = sorted_price.columns[:10]

    df_with_company_name = search_and_extract(company_basic_info, 'stock_id', top10_price, '公司簡稱')
    df_with_price = pd.concat([df_with_company_name, top10_price_df[top10_price_df.columns]], axis=1)
    last_column_label = df_with_price.columns[-1]

    df_with_price = df_with_price.rename(columns={last_column_label: 'Price'})
    return df_with_price


app = Flask(__name__)
# Heroku = "https://{}.herokuapp.com/".format(HEROKU_APP_NAME)


# header = {
#     "Content_Type": "application/json",
#     "Authorization": "Bearer " + LINE_CHANNEL_ACCESS_TOKEN
# }

@app.route("/")
def hello_world():
    return "hello world!"


# アプリにPOSTがあったときの処理
@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


# botにメッセージを送ったときの処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))
    print("返信完了!!\ntext:", event.message.text)

@handler.add(UnfollowEvent)
def handle_unfollow(event):
    with get_connection() as conn:
        with conn.cursor() as cur:
            conn.autocommit = True
            cur.execute('DELETE FROM users WHERE user_id = %s', [event.source.user_id])
    print("userIdの削除OK!!")

# アプリの起動
if __name__ == "__main__":
    finlab_setting()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

### End