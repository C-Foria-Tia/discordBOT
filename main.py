import os
import discord
from discord.ext import commands

# 1. Botの基本設定と権限
intents = discord.Intents.default()
intents.message_content = True  # メッセージ内容を読み取る権限
intents.guilds = True
intents.members = True          # BANするために必要

bot = commands.Bot(command_prefix="!", intents=intents)

# 2. 【即BAN】トラップワード リスト
BAN_WORDS = [
    "野獣先輩", "YJSPY", "yjspy", "やじゅうせんぱい", "ヤジュウセンパイ",
    "死ね", "タヒね", "しね", "シネ", "殺す", "殺すぞ",
    "田所浩二", "114514", "114,514", "いいよこいよ", "いいよ！こいよ！",
    "1919", "810", "114514810", "淫夢"
]

# 3. 【ルンバお掃除】自動削除ワード リスト（「冷えてるか」を除外）
DELETE_WORDS = [
    # 暴言・不適切ワード
    "障害者", "ガイジ", "キチガイ", "きちがい",
    "ゴミ", "カス", "雑魚", "ざこ", "不細工", "ぶさいく",
    "頭悪い", "低能", "無能", "語彙力ないね",
    "何がありがとうなの？", "はい論破",
    # 淫夢語録（日常で使われにくいもの）
    "逝きすぎ", "いきすぎ", "イキすぎ", "イクイク", "いくいく",
    "ヌッ！", "ぬっ！", "王道を往く", "悔い上げて", 
    "悔い改めて", "歪みねぇな", "だらしねぇな", "そうだよ（便乗）", 
    "そうだよ", "これもうわかんねぇな"
]

@bot.event
async def on_ready():
    print(f"治安維持Bot {bot.user.name} が起動しました。清掃を開始します。")

@bot.event
async def on_message(message):
    # Bot自身、または他のBotのメッセージは無視
    if message.author == bot.user or message.author.bot:
        return

    # スペース（空白）をすべて消去して、スペース空けによる検知回避を無効化
    content = message.content.replace(" ", "").replace("　", "")

    # --- トラップ機能：即BANチェック ---
    for ban_word in BAN_WORDS:
        if ban_word in content:
            try:
                await message.guild.ban(message.author, reason=f"禁止ワード（淫夢/荒らし）「{ban_word}」の送信による自動BAN")
                await message.delete()
                print(f"【BAN】{message.author} を禁止ワード「{ban_word}」検知により追放しました。")
                return
            except discord.Forbidden:
                print(f"【権限エラー】{message.author} をBANする権限がBotにありません。")
            except discord.HTTPException:
                print("BAN処理中にエラーが発生しました。")

    # --- ルンバ機能：自動削除チェック ---
    for delete_word in DELETE_WORDS:
        if delete_word in content:
            try:
                await message.delete()
                warning = await message.channel.send(
                    f"{message.author.mention} 治安維持のため、ルンバが不適切な表現を清掃しました。", 
                    delete_after=5
                )
                print(f"【清掃】{message.author} のメッセージ（禁止ワード: {delete_word}）を削除しました。")
                return
            except discord.Forbidden:
                print("【権限エラー】メッセージを削除する権限がBotにありません。")

    await bot.process_commands(message)

# 4. Botの起動（環境変数からトークンを取得）
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("【エラー】DISCORD_TOKEN が設定されていません。")
    else:
        bot.run(token)