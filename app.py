from flask import Flask, request
import os

import requests

app = Flask(__name__)

# ====== НАСТРОЙКИ ======
GROUP_TOKEN = os.environ.get("VK_GROUP_TOKEN", "").strip()
CONFIRMATION_TOKEN = os.environ.get("VK_CONFIRMATION_TOKEN", "").strip()
API_VERSION = "5.199"

COMMENT_TEXT = (
    "💛 Хотите заказать? Это просто:\n\n"
    "Напишите нам:\n"
    "👉 Telegram — https://t.me/Home_ecomm_chat\n"
    "👉 МАКС — https://max.ru/u/f9LHodD0cOJLvfkeeIZYbgvw2yDirTgrbs57bD6-XoHF4pOyv9Rhv-mLuG4\n\n"
    "Пришлите ссылку на пост или скрин ✨\n\n"
    "📦 Подписывайтесь на канал:\n"
    "Telegram — https://t.me/home_ecomm\n"
    "МАКС — https://max.ru/id504212586564_biz"
)

# Чтобы не было дублей при повторной отправке одного и того же события
processed_posts = set()


def create_comment(owner_id: int, post_id: int, message: str):
    if not GROUP_TOKEN:
        return {"error": "VK_GROUP_TOKEN is not configured"}

    url = "https://api.vk.com/method/wall.createComment"
    data = {
        "owner_id": owner_id,
        "post_id": post_id,
        "message": message,
        "from_group": 1,
        "access_token": GROUP_TOKEN,
        "v": API_VERSION,
    }

    response = requests.post(url, data=data, timeout=20)
    return response.json()


@app.route("/vk/callback", methods=["POST"])
def callback():
    data = request.json

    print("=== NEW REQUEST ===")
    print(data)

    if not data:
        return "no data"

    event_type = data.get("type")
    print("EVENT TYPE:", event_type)

    # Шаг подтверждения Callback API
    if event_type == "confirmation":
        if not CONFIRMATION_TOKEN:
            return "VK_CONFIRMATION_TOKEN is not configured", 503
        return CONFIRMATION_TOKEN

    # Новый пост на стене сообщества
    if event_type == "wall_post_new":
        post = data.get("object", {})
        post_id = post.get("id")
        owner_id = post.get("owner_id")

        if not post_id or not owner_id:
            return "ok"

        # Защита от дублей
        unique_key = f"{owner_id}_{post_id}"
        if unique_key in processed_posts:
            return "ok"

        processed_posts.add(unique_key)

        result = create_comment(owner_id, post_id, COMMENT_TEXT)
        print("Комментарий отправлен:", result)

        return "ok"

    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
