from code import interact
from typing import List, Optional
import discord
import discord.app_commands.commands
from discord import Interaction, app_commands
from discord.ext import commands

#from ..main import Main


from src.guild_manager import GuildManager
from src.util import hmac_sha256


class TTSCog(commands.Cog):
    def __init__(self, main):
        self.main = main

        #discord.app_commands.commands._populate_choices(self.VoiceCommands.slash_voice_set._params, self.main.engine.get_speakers())
        self.main.bot.tree.add_command(self.voice())

    @commands.command()
    async def join(self, ctx):
        if ctx.message.guild:
            if ctx.message.author.voice is None:
                await ctx.message.reply("VCに参加してください。")
                return
            elif ctx.message.guild.voice_client:
                await ctx.message.guild.voice_client.move_to(ctx.message.author.voice.channel)
                await ctx.message.channel.send('VCに参加しました。')
            else:
                await ctx.message.author.voice.channel.connect()
                await ctx.message.channel.send('VCに参加しました。\n> 利用規約: https://kuroneko6423.com/rule/VOICEVOX/ \n> 利用規約に同意した方のみご利用ください\n> 配信サービスで利用する場合サポートサーバーでできればお問い合わせください\n> バグなどを発見した場合はサポートサーバーで報告をお願いします\n> \n> お知らせ: 現在ExVoiceの設定をする予定が未定です。詳しくはサポートサーバーまでよろしくお願いします')
            guild_manager = GuildManager.get(ctx.message.guild)
            guild_manager.ch = ctx.message.channel
            guild_manager.queue.enqueue(
                self.main.engine.tts(
                    "接続しました。利用規約を読んでご使用ください。", guild_manager.voice, self.main
                )
            )
    
    @app_commands.command(name="join")
    async def slash_join(self, interaction: Interaction):
        if not interaction.guild:
            await interaction.response.send_message("このコマンドはサーバーのみで実行できます。")
            return

        if not interaction.user.voice:
            await interaction.response.send_message("VCに参加してください。")
            return

        perms = interaction.user.voice.channel.permissions_for(interaction.guild.me)
        if not (perms.connect and perms.speak):
            await interaction.response.send_message("ボットに`接続`と`発言`の権限がありません。", ephemeral=True)
            return

        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(interaction.user.voice.channel)
            await interaction.response.send_message('VCに参加しました。')
        else:
            await interaction.user.voice.channel.connect()
            await interaction.response.send_message('VCに参加しました。\n> 利用規約: https://kuroneko6423.com/rule/VOICEVOX/ \n> 利用規約に同意した方のみご利用ください\n> 配信サービスで利用する場合サポートサーバーでできればお問い合わせください\n> バグなどを発見した場合はサポートサーバーで報告をお願いします\n> \n> お知らせ: 現在ExVoiceの設定をする予定が未定です。詳しくはサポートサーバーまでよろしくお願いします')
    
        guild_manager = GuildManager.get(interaction.guild)
        guild_manager.ch = interaction.channel  
        guild_manager.queue.enqueue(
            self.main.engine.tts(
                "接続しました。利用規約を読んでご使用ください。", guild_manager.voice, self.main
            )
        )


    @commands.command()
    async def dc(self, ctx):
        if ctx.message.guild:
            guild_manager = GuildManager.get(ctx.message.guild)
            if ctx.message.guild.voice_client is None:
                return await ctx.message.channel.send("VCに参加していません")
            else:
                try:
                    await ctx.message.guild.voice_client.disconnect()
                except:
                    await ctx.message.channel.send("VCから切断できませんでした")
                else:
                    guild_manager.ch = None
                    guild_manager.queue.queue.clear()
                    await ctx.message.channel.send("切断しました")

    @app_commands.command(name="disconnect")
    async def slash_dc(self, interaction: Interaction):
        if interaction.guild:
            guild_manager = GuildManager.get(interact.guild)
            if interaction.guild.voice_client is None:
                return await interaction.response.send_message("VCに参加していません", ephemeral=True)
            else:
                try:
                    await interaction.guild.voice_client.disconnect()
                except:
                    await interaction.response.send_message("VCから切断できませんでした", ephemeral=True)
                else:
                    guild_manager.ch = None
                    guild_manager.queue.queue.clear()
                    await interaction.response.send_message("切断しました")

    @commands.command()
    async def setvoice(self, ctx, speaker = None):
        if ctx.message.guild:
            if not speaker:
                await ctx.message.reply(f", ".join(self.main.engine.get_speakers().keys()), allowed_mentions=None)
                return
            guild_manager = GuildManager.get(ctx.message.guild)
            if speaker in self.main.engine.get_speakers().keys():
                guild_manager.voice = self.main.engine.get_speakers()[speaker]
                await ctx.message.reply(f"{speaker}に設定しました。")
            else:
                await ctx.message.reply(f"その音声は存在しません。\nリスト：" + ", ".join(self.main.engine.get_speakers().keys()), allowed_mentions=None)

    class voice(app_commands.Group):
        stats = app_commands.Group(name='voice', description='読み上げる声の設定です。')

        @app_commands.command(
            name="list",
            description="設定可能な声の一覧を表示します。"
        )
        async def slash_voice_list(self, interaction: Interaction):
            embed = discord.Embed(
                title="設定可能な声の一覧", 
                color=0xfc1c32,
                description="\n".join(self.main.engine.get_speakers().keys())
            )
            await interaction.response.send_message(embed=embed)


        @app_commands.command(
            name="set",
            description="読み上げする声を変更します。"
        )
        @app_commands.describe(speaker="設定する声")
        async def slash_voice_set(self, interaction: Interaction, speaker: str):
            if speaker in self.main.engine.get_speakers().keys():
                guild_manager = GuildManager.get(interaction.guild)
                guild_manager.voice = self.main.engine.get_speakers()[speaker]
                await interaction.response.send_message(f"{speaker}に設定しました。")    
                return
            else:
                await interaction.response.send_message(f"その音声は存在しません。\n`/speaker list`で設定可能な声一覧を確認してください。", ephemeral=True)
        
    @commands.command()
    async def dict(self, ctx):
        await ctx.send("https://cyclone.cron.jp/dict/edit?token=" + hmac_sha256(f"{ctx.guild.id}".encode('utf-8'),
                                                                                self.main.config.secret.encode(
                                                                                    'utf-8')) + "&server_id=" + str(
            ctx.guild.id))

    @app_commands.command(
        name="dict",
        description="サーバー辞書の編集URLを表示します"
    )
    async def slash_dict(self, interaction: Interaction):
        await interaction.response.send_message(
            "https://cyclone.cron.jp/dict/edit?token=" + hmac_sha256(
                f"{interaction.guild.id}".encode('utf-8'),
                self.main.config.secret.encode('utf-8')
            ) + "&server_id=" + str(interaction.guild.id),
            ephemeral=True
        )


    @commands.command()
    async def gdict(self, ctx):
        await ctx.send("https://cyclone.cron.jp/dict/edit?token=" + hmac_sha256(f"0".encode('utf-8'),
                                                                                self.main.config.secret.encode(
                                                                                    'utf-8')) + "&server_id=0")

    @app_commands.command(
        name="gdict",
        description="全体辞書の編集URLを表示します(運営のみ)"
    )
    async def slash_gdict(self, interaction: Interaction):
        await interaction.response.send_message(
            "https://cyclone.cron.jp/dict/edit?token=" + hmac_sha256(
                f"0".encode('utf-8'),
                self.main.config.secret.encode('utf-8')
            ) + "&server_id=0",
            ephemeral=True
        )
