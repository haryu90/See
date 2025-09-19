import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# 디스코드 설정
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # 멤버 정보 사용 가능해야 멘션 처리됨

bot = commands.Bot(command_prefix="!", intents=intents)

# 데이터 저장 파일 경로
DATA_FILE = "data.json"

# 기본 데이터 구조
data = {
    "total_reviews": 0,
    "user_review_counts": {},     # {user_id: count}
    "maker_review_counts": {}     # {maker_id: count}
}

# 데이터 로드
def load_data():
    global data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

# 데이터 저장
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# 후기 기능
class Review(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="후기", description="제작자에게 후기를 남깁니다. /후기 @제작자 후기내용")
    @app_commands.describe(maker="후기를 받을 제작자", content="후기 내용")
    async def 후기(self, interaction: discord.Interaction, maker: discord.Member, content: str):
        user = interaction.user
        user_id = str(user.id)
        maker_id = str(maker.id)

        # 통계 카운트 증가
        data["total_reviews"] += 1
        data["user_review_counts"][user_id] = data["user_review_counts"].get(user_id, 0) + 1
        data["maker_review_counts"][maker_id] = data["maker_review_counts"].get(maker_id, 0) + 1

        # 저장
        save_data()

        # 일반 채팅 메시지로 후기 출력
        await interaction.response.send_message(
            f"{user.mention} 님의 {maker.mention} 후기: {content}"
        )

        # 통계 임베드 작게 출력 (inline + 회색)
        embed = discord.Embed(color=discord.Color.dark_gray())
        embed.add_field(name=" 전체 후기 수", value=str(data["total_reviews"]), inline=True)
        embed.add_field(name=f"{user.name}님의 작성 수", value=str(data["user_review_counts"][user_id]), inline=True)
        embed.add_field(name=f"{maker.name}님이 받은 수", value=str(data["maker_review_counts"][maker_id]), inline=True)

        await interaction.followup.send(embed=embed)

# 봇에 명령어 Cog 추가
async def setup(bot):
    await bot.add_cog(Review(bot))

# 봇 실행 준비
@bot.event
async def on_ready():
    load_data()
    print(f"✅ 로그인됨: {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 슬래시 명령어 동기화 완료: {len(synced)}개")
    except Exception as e:
        print(f"❌ 슬래시 명령어 동기화 실패: {e}")

# 봇 실행
def main():
    bot.run(Token_)

if __name__ == "__main__":
    main()
