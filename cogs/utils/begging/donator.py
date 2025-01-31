from dataclasses import dataclass
import typing
import random


__all__ = (
    "DonatorQuotes",
    "Donator",
    "Donators",
)


class DonatorQuotes:
    """
    Represents the quotes that can be said by a donator.

    Attributes:
        name (`str`): The name of the donator.
        success (`list` of `str`): A list of quotes used when a user get's a reward. This will be formatted with the user's reward.
            E.g:
            "You got {}!" > "You got a <emoji:123456789> **Example Item**!"
            "Sure, here's {}. Have a nice day" > "Sure, here's <emoji:123456789> **Example Item**. Have a nice day"
        fail (`list` of `str`): A list of quotes used when a user doesn't get a reward.
    """

    def __init__(self, *, success: typing.List[str], fail: typing.List[str]):
        """
        Represents the quotes that can be said by a donator.

        Args:
            success (`list` of `str`): A list of quotes used when a user get's a reward. This will be formatted with the user's reward.
                E.g:
                "You got {}!" > "You got a <emoji:123456789> **Example Item**!"
                "Sure, here's {}. Have a nice day" > "Sure, here's <emoji:123456789> **Example Item**. Have a nice day"
            fail (`list` of `str`): A list of quotes used when a user doesn't get a reward.
        """
        self.success = success
        self.fail = fail


class Donator:
    """
    Represents a "donator". This is a person/character with it's own name, icon_url, and quotes.

    Attributes:
        name (`str`): The name of the donator.
        icon_url (`str`): The URL of the donator's icon. Square size recommended.
        quotes (`DonatorQuotes`): The quotes that can be said by the donator.
    """

    def __init__(
        self, name: str, *, icon_url: typing.Optional[str] = None, quotes: DonatorQuotes
    ):
        """
        Represents a "donator". This is a person/character with it's own name, icon_url, and quotes.

        Attributes:
            name (`str`): The name of the donator.
            icon_url (`str`): The URL of the donator's icon. Square size recommended.
            quotes (`DonatorQuotes`): The quotes that can be said by the donator.
        """

        self.name = name
        self.icon_url = icon_url
        self.quotes = quotes

    @classmethod
    def from_dict(cls, data: dict):
        """
        Creates a `Donator` from a dictionary.

        Args:
            data (`dict`): A dictionary containing the data to create the `Donator` from.

        Returns:
            `Donator`: The `Donator` created from the dictionary.
        """

        return cls(
            data["name"],
            icon_url=data.get("icon_url", None),
            quotes=DonatorQuotes(**data["quotes"]),
        )


@dataclass
class Donators:
    """
    Represents a list of `Donator`s.

    Attributes:
        donators (`list` of `Donator`): The list of `Donator`s.
    """

    donators: typing.List[Donator]

    def __init__(self, *donators: Donator):
        """
        Represents a list of `Donator`s.

        Args:
            donators (`list` of `Donator`): The list of `Donator`s.
        """

        self.donators = donators

    @classmethod
    def from_dict(cls, data: dict):
        """
        Creates a `Donators` from a dictionary.

        Args:
            data (`dict`): A dictionary containing the data to create the `Donators` from.

        Returns:
            `Donators`: The `Donators` created from the dictionary.
        """

        return cls(
            *[Donator.from_dict(donator) for donator in data["donators"]],
        )

    def get_donator(self, name: str) -> typing.Union[Donator, None]:
        """
        Gets a `Donator` from the list of `Donator`s.

        Args:
            name (`str`): The name of the `Donator` to get.

        Returns:
            `Donator`: The `Donator` with the given name.
            or `None`: if no `Donator` with the given name exists.
        """

        return next((x for x in self.donators if x.name == name))

    def get_random_donator(self) -> typing.Union[Donator, None]:
        """
        Gets a random `Donator` from the list of `Donator`s.

        Returns:
            `Donator`: A random `Donator`.
            or `None`: if there are no `Donator`s in the list.
        """

        return random.choice(self.donators) if self.donators else None
