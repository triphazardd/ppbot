import discord
from discord.ext import commands
import json, random, asyncio
import userdata as ud


class important(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot


    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 60*60*24, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def daily(self, ctx):
        async with ctx.typing():
            embed,pp,exception = await ud.create_embed(ctx)
            if exception:
                return await ud.handle_exception(ctx,exception)
            growsize = random.randrange(40, 80)*await pp.multiplier()
            await pp.size_add(growsize)
            embed.description = f'{ctx.author.mention} received their daily **{growsize} inches!**'
        return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(important(bot))