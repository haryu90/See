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
    "user_review_counts": {},
    "maker_review_counts": {}
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

        data["total_reviews"] += 1
        data["user_review_counts"][user_id] = data["user_review_counts"].get(user_id, 0) + 1
        data["maker_review_counts"][maker_id] = data["maker_review_counts"].get(maker_id, 0) + 1

        save_data()

        await interaction.response.send_message(
            f"{user.mention} 님의 {maker.mention} 후기: {content}"
        )

        embed = discord.Embed(color=discord.Color.dark_gray())
        embed.add_field(name=" 전체 후기 수", value=str(data["total_reviews"]), inline=True)
        embed.add_field(name=f"{user.name}님의 작성 수", value=str(data["user_review_counts"][user_id]), inline=True)
        embed.add_field(name=f"{maker.name}님이 받은 수", value=str(data["maker_review_counts"][maker_id]), inline=True)

        await interaction.followup.send(embed=embed)

# 기존 코드 위에 추가

@bot.event
async def setup_hook():
    await setup(bot)

async def setup(bot):
    await bot.add_cog(Review(bot))



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
    keep_alive()  # 웹서버 시작
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
