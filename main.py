import uvicorn
from fastapi import FastAPI, HTTPException, Request
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (Configuration,
                                  ApiClient,
                                  MessagingApi,
                                  ReplyMessageRequest,
                                  TextMessage)
from linebot.v3.webhooks import (MessageEvent,
                                 TextMessageContent)
from linebot.v3.exceptions import InvalidSignatureError
import google.generativeai as genai

app = FastAPI()

# ข้อมูล token และ channel secret สำหรับ LINE
ACCESS_TOKEN = "lN7Y052k/1pu9LH3wnpVlERBLWMdX3SA1eH6rcP4PH8Oxx5bMywQt+HIhM0vk2JvNKsACaNrdefBJc0qg8S64r2f9EXB2Vmp/Mo7KM0+s9EMB3rz6EM1h2ddfrTSL56tA3MfC6Gj3mPxt9A2hpFIzAdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "217d962e5761277120cbca39e946f69e"

# ข้อมูล Gemini api key
GEMINI_API_KEY = "AIzaSyDU7uJSHak0Vt0Qcxpgb62Sa67WbH69WiY"

# การเชื่อมต่อ และตั้งค่าข้อมูลเพื่อเรียกใช้งาน LINE Messaging API
configuration = Configuration(access_token=ACCESS_TOKEN)
handler = WebhookHandler(channel_secret=CHANNEL_SECRET)

# การเชื่อมต่อ และตั้งค่าข้อมูลเพื่อเรียกใช้งาน Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


@app.get('/')
async def greeting():
    return "Hello from Backend 🙋‍♂️"


# Endpoint สำหรับการสร้าง Webhook
@app.post('/message')
async def message(request: Request):
    # การตรวจสอบ headers จากการขอเรียกใช้บริการว่ามาจากทาง LINE Platform จริง
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        raise HTTPException(
            status_code=400, detail="X-Line-Signature header is missing")

    # ข้อมูลที่ส่งมาจาก LINE Platform
    body = await request.body()

    try:
        # เรียกใช้งาน Handler เพื่อจัดข้อความจาก LINE Platform
        handler.handle(body.decode("UTF-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")


# Function สำหรับจัดการข้อมูลที่ส่งมากจาก LINE Platform
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    # เชื่อมต่อไปยัง LINE Messaging API ผ่าน API Client
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        # นำข้อมูลส่งไปยัง Gemini เพื่อทำการประมวลผล และสร้างคำตอบ และส่งตอบกลับมา
        gemini_response = model.generate_content(event.message.text)

        # Reply ข้อมูลกลับไปยัง LINE
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text=gemini_response.text)]
            )
        )


if __name__ == "__main__":
    uvicorn.run("main:app",
                port=8000,
                host="0.0.0.0")
