app = Flask(__name__)

configuration = Configuration(access_token=os.getenv('access_token'))
line_handler = WebhookHandler(os.getenv('Channel_secret'))

def get_new():
  url = "https://money.udn.com/money/vipbloomberg/time?from=edn_navibar"
  headers = {"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"}

  response = requests.get(url, headers = headers)

  soup = BeautifulSoup(response.text, 'lxml')
  news_list=[]
  x= soup.find_all("div",class_="story__content story__content story__content--key")
  for i,item in enumerate(x) :
    if i >= 10:
      break
    title = item.find('h3').text.strip()
    link = item.find('a')['href']
    news_list.append(f"{i+1}. {title}\n{link}")

  return "\n\n".join(news_list)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_msg = event.message.text

    # 使用者輸入「新聞」才觸發爬蟲
    if "新聞" in user_msg:
        news = get_new()
        reply_text = f"最新 Bloomberg 新聞：\n\n{news}"
    else:
        reply_text = "請輸入「新聞」取得最新財經消息。"

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
