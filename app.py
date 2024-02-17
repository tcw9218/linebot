# import finlab
# from finlab import data
from flask import Flask, request, abort
import requests, os
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage, FollowEvent, UnfollowEvent
from io import BytesIO
# import psycopg2

# finlab.login('7SHZu9Y2jRV/TJ6outOrHEaZHKZiatjOO1joDGtwd8b42GNYOrA650bwvHlXqbyy#free')
# data.get('price:收盤價')


LINE_CHANNEL_SECRET = "f2fe89950508f5bb231d88482d19d6b5"
LINE_CHANNEL_ACCESS_TOKEN = "m05ZcFrzG9ojmIKaVvh9joYAcq0QYSIfWvjYILZ2m+ypIOhUXQtI98pHG4RSvX1YASaCp2defX5dAviryAb7YHW/OjYkIcyUloeQQImUVul8p/O0t030gwSl6zE5cxbLUHDmgS80xiAFSAGJswP/jAdB04t89/1O/w1cDnyilFU="
# DATABASE_URL = "~~~~~あなたのデータベースURL~~~~~" # 後ほどHerokuでPostgreSQLデータベースURLを取得
# HEROKU_APP_NAME = "~~~~~あなたのHerokuアプリ名~~~~~" # 後ほど作成するHerokuアプリ名

app = Flask(__name__)
# Heroku = "https://{}.herokuapp.com/".format(HEROKU_APP_NAME)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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
    # 初回のみデータベースのテーブル作成
    # with get_connection() as conn:
    #     with conn.cursor() as cur:
    #         conn.autocommit = True
    #         cur.execute('CREATE TABLE IF NOT EXISTS users(user_id TEXT)')
    
    # LINE botをフォローしているアカウントのうちランダムで一人にプッシュ通知
    # push()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
### End