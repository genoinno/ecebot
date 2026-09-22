import discord
from discord import ui
from models.book import Book
from utils import RECORD_CHANNEL_ID, get_records_stats

class LibraryDropdown(discord.ui.Select):
    def __init__(
        self,
        medium: discord.Embed | discord.Message | None,
        books: list[Book],
        user: discord.Member,
    ):
        self.embed = medium
        self.books = books
        self.user = user
        options = [
            discord.SelectOption(
                label=book.title,
                value=book.identifiers.isbn_13[0],
                description="By " + book.main_author,
                emoji=book.emoji,
            )
            for book in self.books
        ]
        super().__init__(
            placeholder="Select a book...", min_values=1, max_values=1, options=options
        )


class BookshelfDropdown(LibraryDropdown):
    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return interaction.response.send_message(
                f"Hey! you are not {self.user.name}.\n*Shoo!*", ephemeral=True
            )

        book = [
            book for book in self.books if book.isbn == self.values[0]
        ][0]
        
        img = book.get_cover_url("large")
        self.embed.clear_fields()
        self.embed.title = f"**{book.title}**"
        self.embed.url = book.url
        self.embed.description = (
            book.description[:297] + f"[...]({book.url})"
            if len(book.description) >= 300
            else book.description
        )
        self.embed.add_field(
            name="Published", value=f"**[{book.published_year}]({book.url})**"
        ).add_field(name="Author", value=book.main_author).add_field(
            name="Available",
            value=(
                "Yes" if book.available else "No"
            ),
        ).set_footer(
            text=book.publishers[0]
        ).set_thumbnail(
            url=book.get_author_image_url("large")
        ).set_image(
            url=img
        )
        await interaction.response.edit_message(embed=self.embed)


class BookshelfDropdownView(discord.ui.View):
    def __init__(self, embed: discord.Embed, books: list[Book], user: discord.Member):
        super().__init__()
        self.add_item(BookshelfDropdown(embed, books, user))


class BorrowingDropdown(LibraryDropdown):
    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return interaction.response.send_message(
                f"Hey! you are not {self.user.name}.\n*Shoo!*", ephemeral=True
            )


class BorrowingDropdownView(discord.ui.View):
    def __init__(
        self, message: discord.Message, books: list[Book], user: discord.Member
    ):
        super().__init__()
        self.add_item(BorrowingDropdown(message, books, user))


class AgreementView(discord.ui.View):
    positive = "Agree!"
    negative = "Nevermind..."
    def __init__(self, user: discord.User):
        super().__init__()
        self.user = user

    @discord.ui.button(label=positive, style=discord.ButtonStyle.green, custom_id="agree")
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You cannot press this button!", ephemeral=True
            )
            return

    @discord.ui.button(label=negative, style=discord.ButtonStyle.danger, custom_id="disagree")
    async def abort(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You cannot press this button!", ephemeral=True
            )
            return

        await interaction.response.send_message("Okay we understand...", ephemeral=True)

class BorrowingForm(ui.Modal, title="Borrowing Form"):
    name = ui.TextInput(
        label="Fullname", 
        placeholder="Enter your fullname",
    )
    phone = ui.TextInput(
        label="Phone Number",
        placeholder="Enter your phone number (e.g, 08773847183287)"
    )
    kelas = ui.TextInput(
        label="Class",
        placeholder="Enter your Class (e.g, XIII SIJA 2 )"
    )

    def __init__(self, **kwargs):
        self.book = kwargs.pop("selected_book")
        default_name = kwargs.pop("default_name", None)
        default_phone = kwargs.pop("default_phone", None)
        default_kelas = kwargs.pop("default_kelas", None)
        super().__init__(**kwargs)
        if default_name:
            self.name.default = default_name
        if default_phone:
            self.phone.default = default_phone
        if default_kelas:
            self.kelas.default = default_kelas

        self.add_item(
            ui.TextInput(label="Book", required=False, default=self.book.title)
        )
