import os
import unicodedata
import discord
from discord.ext import commands

# 1. Botの基本設定と権限（Intents）
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- ワードリストの設定 ---

# 2. 【即捕食（BAN）】対象ワード リスト
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

def normalize_text(text: str) -> str:
    """全角・半角の揺れや大文字小文字を統一する"""
    return unicodedata.normalize('NFKC', text).lower()

@bot.event
async def on_ready():
    print(f"【起動完了】{bot.user} が獲物を探して目を光らせています...")

@bot.event
async def on_message(message: discord.Message):
    # Bot自身の発言は無視
    if message.author.bot:
        return

    content_normalized = normalize_text(message.content)

    # --------------------------------------------------
    # 1. 捕食（即BAN処理）
    # --------------------------------------------------
    for word in BAN_WORDS:
        word_normalized = normalize_text(word)
        if word_normalized in content_normalized:
            # 該当メッセージを削除
            try:
                await message.delete()
            except discord.HTTPException:
                pass

            # BANされる罪人（ユーザー）への送別メッセージ（DM）
            dm_notice = (
                f"【捕食通知】\n"
                f"あなたは禁止ワード『{word}』を放ったため、弱肉強食の理により食されました。\n"
                f"ごちそうさまでした。二度とお目にかかることはないでしょう。"
            )

            # 先にDMを送信する（拒否されている場合はログを出してスキップ）
            try:
                await message.author.send(dm_notice)
                print(f"【捕食】{message.author} にDM（宣告）を送信しました。")
            except discord.Forbidden:
                print(f"【警告】{message.author} のDMが閉じているため、直接捕食へ移行します。")
            except discord.HTTPException as e:
                print(f"【DM送信エラー】: {e}")

            # サーバーから追放（BAN）を実行
            try:
                await message.guild.ban(
                    message.author,
                    reason=f"禁止ワード『{word}』の検出により子分BOTが捕食（BAN）しました。"
                )
                
                # チャンネルにも捕食報告を残す（5秒後に自動消去）
                eat_msg = await message.channel.send(
                    f"🍖 **捕食完了:** {message.author.mention} は禁止ワードを放ったため、美味しく食されました。ごちそうさでした！"
                )
                await eat_msg.delete(delay=5)
                print(f"【捕食完了】{message.author} をBAN（完食）しました。")

            except discord.Forbidden:
                await message.channel.send("【エラー】捕食しようとしましたが、権限が足りず食べ残してしまいました（BOTより権限が高いか同等です）。")
            except discord.HTTPException as e:
                await message.channel.send(f"【エラー】捕食処理に失敗しました: {e}")

            return  # 捕食が完了したら処理終了

    # --------------------------------------------------
    # 2. 清掃（メッセージ削除処理）
    # --------------------------------------------------
    for word in DELETE_WORDS:
        word_normalized = normalize_text(word)
        if word_normalized in content_normalized:
            try:
                await message.delete()
                clean_msg = await message.channel.send(
                    f"🧹 **清掃完了:** {message.author.mention} の不適切な発言をルンバがキレイに清掃しました。"
                )
                await clean_msg.delete(delay=5)
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                print(f"【削除エラー】: {e}")
            return

    await bot.process_commands(message)

# 起動
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("【エラー】DISCORD_TOKEN が設定されていません。")
