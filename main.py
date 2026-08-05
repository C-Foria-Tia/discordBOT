import asyncio
import os
import random
import signal
import sys
import unicodedata
import discord
from discord.ext import commands

# --- 設定項目 ---

# 捕食ログ（処分記録）を投稿するチャンネルID
RECORD_CHANNEL_ID = 1531955600819359808

# 自動リブート（クリーンシャットダウン）までの時間（秒）
# 例: 85800秒 = 23時間50分（GitHub Actionsの6時間制限なら 20700秒 = 5時間45分 などに調整）
LIFETIME_SECONDS = 20700  

# 1. Botの基本設定と権限（Intents）
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 2. 【即捕食（BAN）】対象ワード リスト
BAN_WORDS = [
    "野獣先輩", "YJSPY", "yjspy", "やじゅうせんぱい", "ヤジュウセンパイ",
    "死ね", "タヒね", "しね", "シネ", "殺す", "殺すぞ",
    "田所浩二", "114514", "114,514", "いいよこいよ", "いいよ！こいよ！",
    "1919", "810", "114514810"
]

# 3. 【ルンバお掃除】自動削除ワード リスト
DELETE_WORDS = [
    "障害者", "ガイジ", "キチガイ", "きちがい",
    "ゴミ", "カス", "雑魚", "ざこ", "不細工", "ぶさいく",
    "頭悪い", "低能", "無能", "語彙力ないね",
    "何がありがとうなの？", "はい論破",
    "逝きすぎ", "いきすぎ", "イキすぎ", "イクイク", "いくいく",
    "ヌッ！", "ぬっ！", "王道を往く", "悔い上げて", 
    "悔い改めて", "歪みねぇな", "だらしねぇな", "そうだよ（便乗）"
]

def normalize_text(text: str) -> str:
    """全角・半角の揺れや大文字小文字を統一する"""
    return unicodedata.normalize('NFKC', text).lower()

def bite_text(text: str, chance: float = 0.25) -> str:
    """文章全体から多種多様な噛み・ドモリを発生させ、言い直す関数"""
    if random.random() > chance:
        return text

    replacements = {
        "でした": ["でひた", "でふた", "でしゅた"],
        "しました": ["ひました", "しやした", "しまひた"],
        "ます": ["まふ", "ましゅ", "まつ"],
        "ごちそうさま": ["ごひちそうさま", "ごちほうさま", "ごちそうしゃま"],
        "禁止": ["きんひ", "きんしぃ"],
        "捕食": ["ほほく", "ほふぉく"],
        "清掃": ["ふぇいそう", "せいそうっ"],
        "美味しく": ["おいひく", "おひしく"],
        "食されました": ["たべられまひた", "くわれまひた"],
        "二度と": ["にろと", "に、二度と"],
        "ありません": ["ありまひぇん", "ありやせん"],
        "完了": ["かんりょうっ", "か、完了"],
        "ルンバ": ["るんばっ", "ル、ルンバ"],
        "弱肉強食": ["じゃくにくきょうしょくっ", "じゃく、弱肉強食"],
    }

    bitten = text
    bitten_flag = False

    for original, changed in replacements.items():
        if original in bitten:
            if isinstance(changed, list):
                bitten = bitten.replace(original, random.choice(changed), 1)
            else:
                bitten = bitten.replace(original, changed, 1)
            bitten_flag = True

    particles = ["は", "が", "を", "に"]
    for p in particles:
        if p in bitten and random.random() < 0.3:
            bitten = bitten.replace(p, f"{p}、{p}", 1)
            bitten_flag = True
            break

    if bitten_flag:
        fix_phrases = [
            "……あ、コホン！……違います、です！",
            "……っ！……じゃなくて、です！",
            "……噛みました。……ゲホン、です！",
            "……あふっ！……気を取り直して、です！",
            "……〜〜〜っ！……噛んでないです、です！"
        ]
        bitten += f" {random.choice(fix_phrases)}"
    else:
        bitten += "……あ、噛みました。"

    return bitten


# --- 自動シャットダウン（リブート）タスク ---
async def scheduled_graceful_shutdown(delay: int):
    """指定時間経過後に安全にDiscord接続を閉じる"""
    await asyncio.sleep(delay)
    print(f"\n【定期リブート】稼働時間（{delay}秒）に達したため、安全なシャットダウンシーケンスを開始します...")
    await bot.close()


@bot.event
async def on_ready():
    print(f"【起動完了】{bot.user} が獲物を探して目を光らせています...")
    # 起動と同時にタイマーを開始
    bot.loop.create_task(scheduled_graceful_shutdown(LIFETIME_SECONDS))

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    content_normalized = normalize_text(message.content)

    # 1. 捕食（即BAN処理）
    detected_ban_words = [
        word for word in BAN_WORDS 
        if normalize_text(word) in content_normalized
    ]

    if detected_ban_words:
        try:
            await message.delete()
        except discord.HTTPException:
            pass

        words_str = "』『".join(detected_ban_words)

        raw_dm_notice = (
            f"【捕食通知】\n"
            f"あなたは禁止ワード『{words_str}』を放ったため、弱肉強食の理により食されました。\n"
            f"ごちそうさまでした。二度とお目にかかることはないでしょう。"
        )
        dm_notice = bite_text(raw_dm_notice, chance=0.25)

        try:
            await message.author.send(dm_notice)
            print(f"【捕食】{message.author} にDM（宣告）を送信しました。")
        except discord.Forbidden:
            print(f"【警告】{message.author} のDMが閉じているため、直接捕食へ移行します。")
        except discord.HTTPException as e:
            print(f"【DM送信エラー】: {e}")

        try:
            reason_words = ", ".join(detected_ban_words)
            await message.guild.ban(
                message.author,
                reason=f"禁止ワード（{reason_words}）の検出により子分BOTが捕食（BAN）しました。"
            )
            
            raw_channel_eat_text = f"🍖 **捕食完了:** {message.author.mention} は禁止ワードを放ったため、美味しく食されました。ごちそうさでした！"
            channel_eat_text = bite_text(raw_channel_eat_text, chance=0.25)
            eat_msg = await message.channel.send(channel_eat_text)
            await eat_msg.delete(delay=5)

            record_channel = bot.get_channel(RECORD_CHANNEL_ID)
            if record_channel:
                title_text = bite_text("📜 【捕食アーカイブ】処分ユーザー記録", chance=0.25)
                desc_text = "弱肉強食の理により、新たな荒らしが食されました。ごちそうさでした！"
                footer_text = bite_text("弱肉強食の理により、サーバーの平和は保たれた…", chance=0.25)

                embed = discord.Embed(
                    title=title_text,
                    description=desc_text,
                    color=discord.Color.dark_red()
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                embed.add_field(name="対象ユーザー", value=f"{message.author.mention} (`{message.author.name}`)", inline=False)
                embed.add_field(name="検出ワード", value=f"`{reason_words}`", inline=False)
                embed.set_footer(text=footer_text)
                
                await record_channel.send(embed=embed)

            print(f"【捕食完了】{message.author} をBAN（完食）しました。")

        except discord.Forbidden:
            raw_err_msg = "【エラー】捕食しようとしましたが、権限が足りず食べ残してしまいました（BOTより権限が高いか同等です）。"
            err_msg = bite_text(raw_err_msg, chance=0.35)
            await message.channel.send(err_msg)
        except discord.HTTPException as e:
            await message.channel.send(f"【エラー】捕食処理に失敗しました: {e}")

        return

    # 2. 清掃（メッセージ削除処理）
    for word in DELETE_WORDS:
        if normalize_text(word) in content_normalized:
            try:
                await message.delete()
                raw_clean_text = f"🧹 **清掃完了:** {message.author.mention} の不適切な発言をルンバがキレイに清掃しました。"
                clean_text = bite_text(raw_clean_text, chance=0.25)
                clean_msg = await message.channel.send(clean_text)
                await clean_msg.delete(delay=5)
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                print(f"【削除エラー】: {e}")
            return

    await bot.process_commands(message)


# メイン実行部
async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("【エラー】DISCORD_TOKEN が設定されていません。")
        sys.exit(1)

    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
        print("BOTsystemd[1]: Reached target Shutdown.（Exit Code 0）。")
        sys.exit(0)
    except (KeyboardInterrupt, SystemExit):
        print("【手動停止】外部シグナルにより正常終了します。")
        sys.exit(0)
    except Exception as e:
        print(f"【予期せぬ例外】: {e}")
        sys.exit(1)
