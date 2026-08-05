import os
import discord
from discord.ext import commands
from discord import app_commands


# ==================================================
# 設定
# ==================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# 允許填寫、編輯的身分組 ID
ALLOWED_ROLE_ID = int(os.getenv("ALLOWED_ROLE_ID", "0"))

# Sign In 面板所在的頻道 ID
SIGNIN_CHANNEL_ID = int(os.getenv("SIGNIN_CHANNEL_ID", "0"))


# ==================================================
# Bot
# ==================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ==================================================
# 權限檢查
# ==================================================

def has_signin_role(member: discord.Member) -> bool:

    return any(
        role.id == ALLOWED_ROLE_ID
        for role in member.roles
    )


# ==================================================
# Sign In 表格
# ==================================================

class SignInModal(discord.ui.Modal):

    def __init__(
        self,
        edit_message_id=None,
        default_name="",
        default_student_id="",
        default_note=""
    ):

        self.edit_message_id = edit_message_id

        super().__init__(
            title="Sign In"
        )

        self.name_input = discord.ui.TextInput(
            label="姓名",
            placeholder="請輸入姓名",
            default=default_name,
            required=True,
            max_length=50
        )

        self.student_id_input = discord.ui.TextInput(
            label="學號",
            placeholder="請輸入學號",
            default=default_student_id,
            required=True,
            max_length=50
        )

        self.note_input = discord.ui.TextInput(
            label="備註",
            placeholder="請輸入備註",
            default=default_note,
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=500
        )

        self.add_item(self.name_input)
        self.add_item(self.student_id_input)
        self.add_item(self.note_input)


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        # ==========================================
        # 再次檢查身分組
        # ==========================================

        if not isinstance(interaction.user, discord.Member):

            await interaction.response.send_message(
                "❌ 無法確認你的身分組。",
                ephemeral=True
            )

            return


        if not has_signin_role(interaction.user):

            await interaction.response.send_message(
                "🔒 你沒有權限填寫或編輯 Sign In。",
                ephemeral=True
            )

            return


        # ==========================================
        # 建立 Embed
        # ==========================================

        embed = discord.Embed(
            title="📋 Sign In 資料",
            color=discord.Color.green()
        )

        embed.add_field(
            name="姓名",
            value=self.name_input.value,
            inline=False
        )

        embed.add_field(
            name="學號",
            value=self.student_id_input.value,
            inline=False
        )

        embed.add_field(
            name="備註",
            value=self.note_input.value or "無",
            inline=False
        )

        embed.set_footer(
            text=f"最後修改：{interaction.user.display_name}"
        )


        # ==========================================
        # 編輯原本資料
        # ==========================================

        if self.edit_message_id:

            try:

                channel = interaction.guild.get_channel(
                    SIGNIN_CHANNEL_ID
                )

                if channel is None:

                    await interaction.response.send_message(
                        "❌ 找不到 Sign In 頻道。",
                        ephemeral=True
                    )

                    return


                message = await channel.fetch_message(
                    self.edit_message_id
                )

                await message.edit(
                    embed=embed,
                    view=SignInView()
                )

                await interaction.response.send_message(
                    "✅ Sign In 資料已更新！",
                    ephemeral=True
                )

                return

            except Exception as e:

                print("編輯錯誤:", e)

                await interaction.response.send_message(
                    "❌ 編輯失敗，可能是原本的資料已被刪除。",
                    ephemeral=True
                )

                return


        # ==========================================
        # 新增資料
        # ==========================================

        channel = interaction.guild.get_channel(
            SIGNIN_CHANNEL_ID
        )

        if channel is None:

            await interaction.response.send_message(
                "❌ 找不到 Sign In 頻道。",
                ephemeral=True
            )

            return


        await channel.send(
            embed=embed,
            view=SignInView()
        )


        await interaction.response.send_message(
            "✅ Sign In 完成！",
            ephemeral=True
        )


# ==================================================
# 編輯按鈕
# ==================================================

class SignInView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )


    @discord.ui.button(
        label="✏️ 編輯",
        style=discord.ButtonStyle.primary,
        custom_id="signin_edit_button"
    )
    async def edit_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # ==========================================
        # 檢查身分組
        # ==========================================

        if not isinstance(interaction.user, discord.Member):

            await interaction.response.send_message(
                "❌ 無法確認你的身分組。",
                ephemeral=True
            )

            return


        if not has_signin_role(interaction.user):

            await interaction.response.send_message(
                "🔒 你沒有權限編輯 Sign In。",
                ephemeral=True
            )

            return


        # ==========================================
        # 取得原本資料
        # ==========================================

        message = interaction.message

        if message is None or not message.embeds:

            await interaction.response.send_message(
                "❌ 找不到原本的 Sign In 資料。",
                ephemeral=True
            )

            return


        embed = message.embeds[0]

        default_name = ""
        default_student_id = ""
        default_note = ""


        for field in embed.fields:

            if field.name == "姓名":
                default_name = field.value

            elif field.name == "學號":
                default_student_id = field.value

            elif field.name == "備註":
                default_note = field.value

                if default_note == "無":
                    default_note = ""


        # ==========================================
        # 打開編輯表格
        # ==========================================

        await interaction.response.send_modal(
            SignInModal(
                edit_message_id=message.id,
                default_name=default_name,
                default_student_id=default_student_id,
                default_note=default_note
            )
        )


# ==================================================
# Sign In 面板
# ==================================================

class SignInPanelView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )


    @discord.ui.button(
        label="Sign In",
        style=discord.ButtonStyle.success,
        custom_id="signin_open_button"
    )
    async def signin_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # ==========================================
        # 檢查身分組
        # ==========================================

        if not isinstance(interaction.user, discord.Member):

            await interaction.response.send_message(
                "❌ 無法確認你的身分組。",
                ephemeral=True
            )

            return


        if not has_signin_role(interaction.user):

            await interaction.response.send_message(
                "🔒 你沒有權限填寫 Sign In。",
                ephemeral=True
            )

            return


        # ==========================================
        # 開啟表格
        # ==========================================

        await interaction.response.send_modal(
            SignInModal()
        )


# ==================================================
# Slash Command
# ==================================================

@bot.tree.command(
    name="signin",
    description="建立 Sign In 面板"
)
async def signin(
    interaction: discord.Interaction
):

    # ==========================================
    # 只有管理員可以建立面板
    # ==========================================

    if not isinstance(interaction.user, discord.Member):

        await interaction.response.send_message(
            "❌ 無法確認權限。",
            ephemeral=True
        )

        return


    if not interaction.user.guild_permissions.administrator:

        await interaction.response.send_message(
            "❌ 只有管理員可以使用這個指令。",
            ephemeral=True
        )

        return


    # ==========================================
    # 檢查頻道
    # ==========================================

    if interaction.channel_id != SIGNIN_CHANNEL_ID:

        await interaction.response.send_message(
            "❌ 請在指定的 Sign In 頻道使用 `/signin`。",
            ephemeral=True
        )

        return


    # ==========================================
    # 建立面板
    # ==========================================

    embed = discord.Embed(
        title="📋 Sign In",
        description=(
            "請按下面的 **Sign In** 按鈕填寫資料。\n\n"
            "🔒 只有指定身分組可以填寫與編輯。\n"
            "👀 其他人只能查看。"
        ),
        color=discord.Color.blue()
    )


    await interaction.response.send_message(
        embed=embed,
        view=SignInPanelView()
    )


# ==================================================
# Bot 啟動
# ==================================================

@bot.event
async def on_ready():

    print("--------------------------------")
    print(f"✅ Bot 已登入：{bot.user}")
    print(f"🆔 Bot ID：{bot.user.id}")
    print("--------------------------------")


# ==================================================
# 初始化
# ==================================================

async def setup():

    # 讓按鈕在 Bot 重啟後仍然有效
    bot.add_view(SignInPanelView())
    bot.add_view(SignInView())

    # 同步 Slash Commands
    await bot.tree.sync()


async def main():

    await setup()

    await bot.start(TOKEN)


if __name__ == "__main__":

    import asyncio

    asyncio.run(main())
