import asyncio
import os
import textwrap
import typing

import toml

import voxelbotutils as vbu
from discord.ext import commands, tasks


from cogs import utils


class EconomyCommands(vbu.Cog):
    def __init__(self, bot: vbu.Bot):
        super().__init__(bot)
        self.bot: vbu.Bot
        # Let's clean up the items cache
        try:
            self.bot.items.clear()
            self.logger.info("\t* Clearing items cache... success")

        # No cache to clean? then we don't need to do anything
        except AttributeError:
            self.logger.warn("\t* Clearing items cache... failed - No items cached")

        # Load each location from ./config/locations
        directory = r"config\items"
        items = []
        for filename in os.listdir(directory):
            if filename.endswith(".toml"):
                items.append(
                    utils.Item.from_dict(toml.load(os.path.join(directory, filename)))
                )
        self.bot.items = {
            "shop": {i.id: i for i in items if i.shop_settings.buyable},
            "auction": {i.id: i for i in items if i.shop_settings.auctionable},
            "all": {i.id: i for i in items},
        }
        self.logger.info("\t* Caching items... success")

        # No user cache? Let's create it
        if not hasattr(self.bot, "user_cache"):
            self.bot.user_cache = {}
            self.logger.info("\t* Creating user cache... success")

        # Now let's start the update db from user cache task
        self.update_db_from_user_cache.start()
        self.logger.info("\t* Starting update db from user cache task... success")

        # Now we clean up the begging cache
        try:
            self.bot.begging.clear()
            self.logger.info("\t* Clearing begging cache... success")

        # No cache to clean? then we don't need to do anything
        except AttributeError:
            self.logger.warn(
                "\t* Clearing begging cache... failed - No begging information cached"
            )

        # Load each location from ./config/locations
        directory = r"config\begging\locations"
        begging_locations = []
        for filename in os.listdir(directory):
            if filename.endswith(".toml"):
                begging_locations.append(
                    utils.begging.BeggingLocation.from_dict(
                        self.bot, toml.load(os.path.join(directory, filename))
                    )
                )

        # Put the locations into the bot's begging cache
        self.bot.begging = {
            "locations": begging_locations,
        }

    def cog_unload(self):
        self.update_db_from_user_cache.cancel()

    async def get_user_cache(
        self, user_id: int, db: typing.Optional[vbu.DatabaseConnection]
    ) -> utils.CachedUser:
        """
        Returns user's cached information, if any. Otherwise returns data from the database.

        Args:
            user_id (`int`): The user's ID.
            db (:class:`voxelbotutils.DatabaseConnection`): The database connection.

        Returns:
            `dict`: The user's cache.
        """

        # If the user is already cached, return it
        try:
            return self.bot.user_cache[user_id]

        # Otherwise, let's create it
        except KeyError:

            # Get the user's skills
            user_skill_rows = await db(
                "SELECT * FROM user_skill WHERE user_id = $1", user_id
            )
            user_skills = [utils.Skill(**i) for i in user_skill_rows]

            # Now let's get the user's pp
            try:
                pp_rows = await db("SELECT * FROM user_pp WHERE user_id = $1", user_id)
                user_pp = utils.Pp(**pp_rows[0])

            # apparently the user doesn't have pp? Let's create one
            except IndexError:
                user_pp = utils.Pp(user_id)

            # Now we add this to the user cache
            self.bot.user_cache[user_id] = utils.CachedUser(
                user_id, user_skills, user_pp
            )

            # we do a little logging. it's called: "We do a little logging"
            self.logger.info(f"\t* Creating user cache for {user_id}... success")

            # and return the user cache
            return self.bot.user_cache[user_id]

    @tasks.loop(seconds=30.0)
    async def update_db_from_user_cache(self) -> None:
        """
        This task updates the database from the user cache every minute.
        """

        self.logger.info("Updating database from user cache...")

        # Establish a connection to the database
        async with vbu.DatabaseConnection() as db:

            # Iterate through all cached users
            for user_id, user_cache in self.bot.user_cache.items():

                # Iterate through all of their skills
                skill: utils.Skill
                for skill in user_cache.skills:

                    # Update the user's skill
                    await db(
                        """INSERT INTO user_skill VALUES ($1, $2, $3)
                        ON CONFLICT (user_id, name) DO UPDATE SET
                        experience = user_skill.experience + $3""",
                        user_id,
                        skill.name,
                        skill.experience,
                    )

                    # Log our update
                    self.logger.info(
                        f"\t* Updating user cache for {user_id} - {skill.name!r}... success"
                    )

                # Update the user's pp
                await db(
                    """INSERT INTO user_pp VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id) DO UPDATE SET name = $2,
                    size = $3, multiplier = $4""",
                    user_id,
                    user_cache.pp.name,
                    user_cache.pp.size,
                    user_cache.pp.multiplier,
                )

                # Log our update
                self.logger.info(
                    f"Updating user cache for {user_id}'s pp: {user_cache!r}... success"
                )

    @vbu.command(name="beg")
    @vbu.bot_has_permissions(
        embed_links=True,
        read_messages=True,
        send_messages=True,
        use_external_emojis=True,
    )
    @commands.has_permissions(
        read_messages=True,
        send_messages=True,
        use_slash_commands=True,
    )
    async def _beg_command(self, ctx: vbu.Context):
        """
        Beg for inches, earn items, and get a large pp in the process!
        """

        async with vbu.DatabaseConnection() as db:

            # Get the user's cache
            cache: utils.CachedUser = await self.get_user_cache(ctx.author.id, db)
            begging = cache.get_skill("BEGGING")

            # Set up the begging locations with the user's current begging level
            locations = utils.begging.BeggingLocations(
                begging.level, *self.bot.begging["locations"]
            )

            # Build the message
            components = vbu.MessageComponents(
                vbu.ActionRow(locations.to_select_menu())
            )
            content = textwrap.dedent(
                f"""
                <:thonk:881578428506185779> **Where are you begging?**
                Level up `BEGGING` unlock new locations!
                **Current level:** {utils.readable.int_formatting.int_to_roman(begging.level)}
            """
            )

            # Send the message
            message: vbu.InteractionMessage = await ctx.send(
                content, components=components
            )

            try:
                # Wait for a response
                payload: vbu.ComponentInteractionPayload = await self.bot.wait_for(
                    "component_interaction",
                    check=lambda p: p.message.id == message.id
                    and p.user.id == ctx.author.id,
                    timeout=60.0,
                )
            except asyncio.TimeoutError:
                components.disable_components()
                content = (
                    content + "\n\\🟥 **You took too long to respond** 😔 `waited 60.0s`"
                )
                return await message.edit(content=content, components=components)


def setup(bot: vbu.Bot):
    x = EconomyCommands(bot)
    bot.add_cog(x)
