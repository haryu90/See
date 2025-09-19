import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from flask import Flask
from threading import Thread

# --- Flask 웹서버 설정 ---
app = Flask('')

@app.route('/')
def home():
    return "봇이 잘 실행 중입니다!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- 디스코드 봇 설정 ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
DATA_FILE = "data.json"

data = {
    "total_reviews": 0,
    "user_review_counts": {},     # {user_id: count}
    "maker_review_counts": {},    # {maker_id: count}
    "reviews": {}                 # {"userID:makerID": "후기내용"}
}

def load_data():
    global data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

class Review(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="후기", description="제작자에게 후기를 남깁니다. /후기 @제작자 후기내용")
    @app_commands.describe(maker="후기를 받을 제작자", content="후기 내용")
    async def 후기(self, interaction: discord.Interaction, maker: discord.Member, content: str):
        user = interaction.user
        user_id = str(user.id)
        maker_id = str(maker.id)
        key = f"{user_id}:{maker_id}"

        # 후기 중복 체크 - 덮어쓰기 방지, 기존 후기 삭제 후 새로 추가
        if key in data["reviews"]:
            await interaction.response.send_message(f"❗ 이미 {maker.mention}님께 작성한 후기가 있습니다. 삭제 후 다시 작성해주세요.", ephemeral=True)
            return

        # 후기 저장
        data["reviews"][key] = content
        data["total_reviews"] += 1
        data["user_review_counts"][user_id] = data["user_review_counts"].get(user_id, 0) + 1
        data["maker_review_counts"][maker_id] = data["maker_review_counts"].get(maker_id, 0) + 1

        save_data()

        # 후기 메시지
        await interaction.response.send_message(
            f"{user.mention} 님의 {maker.mention} 후기: {content}"
        )

        # 통계 임베드 (footer에 한 줄로)
        embed = discord.Embed(color=discord.Color.dark_gray())
        footer_text = f"전체 후기 수: {data['total_reviews']} | {user.name} 작성 수: {data['user_review_counts'][user_id]} | {maker.name} 받은 수: {data['maker_review_counts'][maker_id]}"
        embed.set_footer(text=footer_text)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="후기삭제", description="작성한 후기를 삭제합니다. /후기삭제 @제작자")
    @app_commands.describe(maker="삭제할 후기의 제작자")
    async def 후기삭제(self, interaction: discord.Interaction, maker: discord.Member):
        user = interaction.user
        user_id = str(user.id)
        maker_id = str(maker.id)
        key = f"{user_id}:{maker_id}"

        if key not in data["reviews"]:
            await interaction.response.send_message(f"❗ {maker.mention}님에게 작성한 후기가 없습니다.", ephemeral=True)
            return

        # 후기 삭제 및 통계 감소
        del data["reviews"][key]
        data["total_reviews"] -= 1
        data["user_review_counts"][user_id] = max(data["user_review_counts"].get(user_id, 1) - 1, 0)
        data["maker_review_counts"][maker_id] = max(data["maker_review_counts"].get(maker_id, 1) - 1, 0)

        save_data()

        await interaction.response.send_message(f"{user.mention} 님이 {maker.mention}님께 작성한 후기를 삭제했습니다.")

        # 삭제 후 통계 임베드
        embed = discord.Embed(color=discord.Color.dark_gray())
        footer_text = f"전체 후기 수: {data['total_reviews']} | {user.name} 작성 수: {data['user_review_counts'].get(user_id, 0)} | {maker.name} 받은 수: {data['maker_review_counts'].get(maker_id, 0)}"
        embed.set_footer(text=footer_text)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Review(bot))

@bot.event
async def setup_hook():
    await setup(bot)

@bot.event
async def on_ready():
    load_data()
    print(f"✅ 로그인됨: {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 슬래시 명령어 동기화 완료: {len(synced)}개")
    except Exception as e:
        print(f"❌ 슬래시 명령어 동기화 실패: {e}")

TOKEN = os.getenv("Token_")
if not TOKEN:
    print("ERROR: 환경변수 Token_이 설정되지 않았습니다!")
    exit(1)

def main():
    keep_alive()  # Flask 웹서버 실행
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
