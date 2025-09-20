import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from flask import Flask
from threading import Thread
import asyncio

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
    "maker_review_counts": {},
    "reviews": {}
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

        data["reviews"][key] = content
        data["total_reviews"] += 1
        data["user_review_counts"][user_id] = data["user_review_counts"].get(user_id, 0) + 1
        data["maker_review_counts"][maker_id] = data["maker_review_counts"].get(maker_id, 0) + 1

        save_data()

        await interaction.response.send_message(
            f"{user.mention} 님의 {maker.mention} 후기:\n{content}"
        )

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

        del data["reviews"][key]
        data["total_reviews"] -= 1
        data["user_review_counts"][user_id] = max(data["user_review_counts"].get(user_id, 1) - 1, 0)
        data["maker_review_counts"][maker_id] = max(data["maker_review_counts"].get(maker_id, 1) - 1, 0)

        save_data()

        await interaction.response.send_message(f"{user.mention} 님이 {maker.mention}님께 작성한 후기를 삭제했습니다.")

    @app_commands.command(name="후기갯수", description="후기 통계를 확인합니다. 제작자 역할이 있는 사람들의 받은 후기를 모두 보여줍니다.")
    async def 후기갯수(self, interaction: discord.Interaction):
        user = interaction.user
        user_id = str(user.id)

        maker_role_id = 1413435981474041876  # 실제 제작자 역할 ID 입력
        maker_role = interaction.guild.get_role(maker_role_id)

        if not maker_role:
            await interaction.response.send_message("❌ 제작자 역할을 찾을 수 없습니다.", ephemeral=True)
            return

        embed = discord.Embed(title=" 후기 통계", color=discord.Color.blue())
        embed.add_field(name="전체 후기 수", value=str(data['total_reviews']), inline=False)
        embed.add_field(name=f"{user.name} 작성 수", value=str(data['user_review_counts'].get(user_id, 0)), inline=False)

        for member in maker_role.members:
            maker_id = str(member.id)
            received_count = data['maker_review_counts'].get(maker_id, 0)
            embed.add_field(name=f"{member.display_name} 받은 수", value=str(received_count), inline=True)

        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="후기리셋", description="모든 후기를 초기화합니다. 관리자만 사용 가능.")
    async def 후기리셋(self, interaction: discord.Interaction):
        # 관리자 권한 체크
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ 이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)
            return

        # 데이터 초기화
        data["total_reviews"] = 0
        data["user_review_counts"] = {}
        data["maker_review_counts"] = {}
        data["reviews"] = {}

        save_data()

        await interaction.response.send_message("✅ 모든 후기가 초기화되었습니다.")




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


class CloseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="티켓 닫기", style=discord.ButtonStyle.gray, emoji="<a:a9:1413823289771561040>")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("티켓을 닫는 중입니다...", ephemeral=True)
        await asyncio.sleep(2)
        await interaction.channel.delete()

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


class CloseButton(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="티켓 닫기",
                       style=discord.ButtonStyle.gray,  # ButtonStyle.black은 없음
                       emoji="<a:a9:1413823289771561040>")
    async def close_ticket(self, interaction: discord.Interaction,
                           button: discord.ui.Button):
        await interaction.response.send_message("티켓을 닫는 중입니다...", ephemeral=True)
        await asyncio.sleep(2)
        await interaction.channel.delete()


# 티켓 패널 생성 함수
async def create_ticket_panel(ctx,
                              panel_title,
                              options: dict,
                              category,
                              embed_color=0xFFD1DC,
                              author_icon=""):

    class TicketDropdown(discord.ui.Select):

        def __init__(self):
            select_options = [
                discord.SelectOption(label=label,
                                     value=label,
                                     emoji=options[label].get("emoji"))
                for label in options
            ]
            super().__init__(placeholder=" 원하는 항목을 선택해주세요!",
                             options=select_options,
                             min_values=1,
                             max_values=1)

        async def callback(self, interaction: discord.Interaction):
            label = self.values[0]
            data = options[label]

            if not category or not isinstance(category,
                                              discord.CategoryChannel):
                await interaction.response.send_message("❌ 카테고리를 찾을 수 없습니다.",
                                                        ephemeral=True)
                return

            user_name = interaction.user.name.replace(" ", "-").lower()
            topic = label

            # 이모지 및 공백 제거 (필요시)
            for emoji in ["🚨", " ", "🧡", "🩷", "💙", "🩵"]:
                topic = topic.replace(emoji, "")
            topic = topic.strip()

            channel_name = f"{user_name}의-{topic}".replace(" ", "-").lower()

            overwrites = {
                interaction.guild.default_role:
                discord.PermissionOverwrite(view_channel=False),
                interaction.user:
                discord.PermissionOverwrite(view_channel=True,
                                            send_messages=True,
                                            read_message_history=True)
            }

            for role_id in data.get("roles", []):
                role = interaction.guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True)

            for user_id in data.get("users", []):
                member = interaction.guild.get_member(user_id)
                if member:
                    overwrites[member] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True)

            ticket_channel = await interaction.guild.create_text_channel(
                name=channel_name, overwrites=overwrites, category=category)

            embed = discord.Embed(
                title=" 티켓이 생성되었어요!",
                description=
                f"{interaction.user.mention}님, 잠시만 기다려주세요. 담당자가 곧 도와드릴게요!",
                color=embed_color)
            embed.set_footer(text="문의해주셔서 감사합니다!")

            await ticket_channel.send(embed=embed, view=CloseButton())
            await interaction.response.send_message(
                f"티켓이 생성되었습니다 {ticket_channel.mention}", ephemeral=True)

    class TicketView(discord.ui.View):

        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(TicketDropdown())

    embed = discord.Embed(title=panel_title,
                          description=" 아래 메뉴에서 원하는 항목을 선택하여 티켓을 생성해주세요!",
                          color=embed_color)
    embed.set_author(name="바다 티켓봇 ")
    embed.set_footer(text="바다 전용 티켓함")

    await ctx.send(embed=embed, view=TicketView())


# 각 패널별 역할/유저 ID와 이모지 포함 예시


@bot.command()
async def 신고함(ctx):
    category = ctx.channel.category
    if not category:
        await ctx.send("❌ 이 채널은 카테고리 안에 있어야 합니다!")
        return

    options = {
        "신고함": {
            "emoji": "🚨",
            "roles": [1413530966340927640],
            "users": []
        }
    }
    await create_ticket_panel(ctx,
                              "바다다 문의센터",
                              options,
                              category,
                              embed_color=0xFFD1DC)


@bot.command()
async def 하류(ctx):
    category = ctx.channel.category
    if not category:
        await ctx.send("❌ 이 채널은 카테고리 안에 있어야 합니다!")
        return

    options = {
        "하류 문의사항": {
            "emoji": "<a:a_O:1413444184672571543>",
            "roles": [],
            "users": [1409169549819121839]
        },
        "하류 구매하기": {
            "emoji": "<a:a_O:1413444184672571543>",
            "roles": [],
            "users": [1409169549819121839]
        }
    }
    await create_ticket_panel(ctx,
                              "<a:a_O:1413444184672571543> 하류 티켓함",
                              options,
                              category,
                              embed_color=0xC6E2FF)


@bot.command()
async def 유메(ctx):
    category = ctx.channel.category
    if not category:
        await ctx.send("❌ 이 채널은 카테고리 안에 있어야 합니다!")
        return

    options = {
        "유메 문의사항": {
            "emoji": "<a:a_S:1413444202456551454>",
            "roles": [],
            "users": [1016659263055216661]
        },
        "유메 구매하기": {
            "emoji": "<a:a_S:1413444202456551454>",
            "roles": [],
            "users": [1016659263055216661]
        }
    }
    await create_ticket_panel(ctx,
                              "<a:a_S:1413444202456551454> 유메 티켓함",
                              options,
                              category,
                              embed_color=0xE0BBE4)


@bot.command()
async def 말차 (ctx):
    category = ctx.channel.category
    if not category:
        await ctx.send("❌ 이 채널은 카테고리 안에 있어야 합니다!")
        return

    options = {
        "말차 문의사항": {
            "emoji": "<a:a_B:1413444207581859860>",
            "roles": [],
            "users": [1315709432440815680]
        },
        "말차 구매하기": {
            "emoji": "<a:a_B:1413444207581859860>",
            "roles": [],
            "users": [1315709432440815680]
        }
    }
    await create_ticket_panel(ctx,
                              "<a:a_B:1413444207581859860> 말차라떼름 티켓함",
                              options,
                              category,
                              embed_color=0xB5EAEA)

@bot.command()
async def 역지(ctx, member: discord.Member):
    role_id = 1418386242025820320  # 부여할 역할 ID
    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send("❌ 역할을 찾을 수 없습니다.")
        return

    # 허용 역할 ID (명령어 사용 가능 역할)
    allowed_role_ids = [1418933302932410469]  # 여기에 허용할 역할 ID 넣기

    # 권한 체크
    author_roles = [r.id for r in ctx.author.roles]
    if (not ctx.author.guild_permissions.manage_roles and 
        not any(rid in allowed_role_ids for rid in author_roles)):
        await ctx.send("❌ 이 명령어를 사용할 권한이 없습니다.")
        return

    try:
        await member.add_roles(role)
        await ctx.send(f"{member.mention}님 `{role.name}`지급 완료! ")
    except discord.Forbidden:
        await ctx.send("❌ 권한이 부족해서 역할을 부여할 수 없습니다.")
    except Exception as e:
        await ctx.send(f"오류가 발생했습니다: {e}")


TOKEN = os.getenv("Token_")
if not TOKEN:
    print("ERROR: 환경변수 Token_이 설정되지 않았습니다!")
    exit(1)

def main():
    keep_alive()  # Flask 웹서버 실행
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
