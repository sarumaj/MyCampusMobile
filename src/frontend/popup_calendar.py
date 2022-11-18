# -*- coding: utf-8 -*-

import re
import webbrowser
from datetime import datetime
from fnmatch import fnmatch
from typing import Any

import asynckivy
from kivy.metrics import dp
from kivy.properties import ListProperty, ObjectProperty
from kivymd.color_definitions import colors
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.chip import MDChip
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import IconLeftWidget, OneLineIconListItem, TwoLineIconListItem
from kivymd.uix.pickers import MDDatePicker, MDTimePicker


class SearchTag(MDChip):
    """
    Chip widget used to diplay applied filters.
    """


class EventDescription(MDLabel):
    """
    Widegt holding the description of a calendar event.
    """

    def on_ref_press(self, ref):
        """
        Called whenever user interacts with a markdown link.

        Positional arguments:
            ref: str,
                content of the markdown link.
        """

        # change the hue of the link
        self.text = self.text.replace(
            "[ref={1}][color={0}]{1}[/color][/ref]".format(
                colors["LightGreen"]["500"], ref
            ),
            "[ref={1}][color={0}]{1}[/color][/ref]".format(
                colors["LightGreen"]["900"], ref
            ),
        )
        webbrowser.open(ref)
        return super().on_ref_press(ref)


class CalendarEventCard(MDCard):
    """
    Widget dsiplaying a calendar event.
    """

    def __init__(
        self, *, dtstart: str, dtend: str, summary: str, description: str, **kwargs
    ):
        """
        Creates calendar event widget.

        Keyword arguments:
            dtstart: str,
                start date and time.

            dtend: str,
                end date and time.

            summary: str,
                event summary (title).

            description: str,
                event description.

            **kwargs: dict[str,Any],
                keyword arguments fo the kivymd.uix.card.MDCard class
        """

        description = re.sub(
            r"(https://.*?)(?=\s|$)",
            "[u][ref=\\1][color={0}]\\1[/color][/ref][/u]".format(
                colors["LightGreen"]["500"]
            ),
            description,
        )
        super().__init__(**kwargs)
        # box for time ranges
        time_range = MDBoxLayout(
            orientation="horizontal",
            adaptive_height=True,
            size_hint=(1, None),
        )
        time_range.add_widget(
            TwoLineIconListItem(
                IconLeftWidget(icon="calendar-start-outline"),
                text="From:",
                secondary_text=dtstart,
                divider="Inset",
            )
        )
        time_range.add_widget(
            TwoLineIconListItem(
                IconLeftWidget(icon="calendar-end-outline"),
                text="To:",
                secondary_text=dtend,
                divider="Inset",
            )
        )
        self.add_widget(time_range)
        # summary
        self.add_widget(
            OneLineIconListItem(
                IconLeftWidget(icon="clock-time-eight-outline"),
                text="Summary:",
                divider="Inset",
            )
        )
        padder = MDBoxLayout(
            orientation="vertical", adaptive_height=True, padding=(dp(70), 0, dp(10), 0)
        )
        padder.add_widget(EventDescription(text=summary))
        self.add_widget(padder)
        # decription
        self.add_widget(
            OneLineIconListItem(
                IconLeftWidget(icon="fountain-pen-tip"),
                text="Description:",
                divider="Inset",
            )
        )
        padder = MDBoxLayout(
            orientation="vertical", adaptive_height=True, padding=(dp(70), 0, dp(10), 0)
        )
        padder.add_widget(EventDescription(text=description))
        self.add_widget(padder)


class CalendarEventContent(MDBoxLayout):
    """
    Content of the calendar event view dialog.
    """

    # reference to the dialog
    dialog = ObjectProperty(None)
    # smallest start date and time (datetime) in the event set
    start = ObjectProperty(None)
    # highest end date and time (datetime) in the event set
    end = ObjectProperty(None)
    # reference to asynchronous content loader necessary
    # to abort loading on specified conditions
    asyncloader = ObjectProperty(None)

    def __init__(self, *, dialog: MDDialog, **kwargs: dict[str, Any]):
        """
        Constructor.

        Key word arguments:
            dialog: kivymd.uix.dialog.MDDialog,
                reference to the implementing dialog instance.

            **kwargs: dict[str,Any],
                keyword arguments passed to the kivymd.uix.boxlayout.MDBoxLayout class.
        """

        self.dialog = dialog
        super().__init__(**kwargs)
        if len(self.events) > 0:
            self.end = max([ev["dtend"] for ev in self.events])
            self.start = min([ev["dtstart"] for ev in self.events])
        for tag in self.initial_tags:
            chip = SearchTag(text=tag)
            chip.bind(on_press=self.remove_search_tag)
            self.ids.stack.add_widget(chip)
        self.init_ui()

    @property
    def events(self) -> tuple[dict[str, Any]]:
        """
        Access point to the events of the calendar dialog.

        Returns:
            tuple[dict[str,Any]]
        """

        return self.dialog.events

    @property
    def initial_tags(self) -> tuple[str]:
        """
        Access point to the initial tags of the calendar dialog.

        Returns:
            tuple[str]
        """

        return self.dialog.initial_tags

    def init_ui(self):
        """
        Method to initialize the user interface components.
        """

        async def set_items():
            """
            Asynchronous worker creating widegts for each calendar event.
            """

            def filter_fn(event):
                """
                Filters events by wildcard patterns and time range.

                Positional arguments:
                    event: dict[str,Any],
                    {
                        "dtstart": datetime,
                        "dtend": datetime,
                        "summary": str,
                        "decription": str
                    }
                """

                return all(
                    (
                        len(self.ids.stack.children) > 0
                        and [
                            fnmatch(event["summary"].decode(), chip.text)
                            for chip in self.ids.stack.children
                        ]
                        or [False]
                    )
                    + [
                        event["dtstart"] >= self.start
                        if isinstance(self.start, datetime)
                        else True
                    ]
                    + [
                        event["dtend"] <= self.end
                        if isinstance(self.end, datetime)
                        else True
                    ]
                )

            # iterate over matching events
            for cnt, event in enumerate(list(filter(filter_fn, self.events))):
                await asynckivy.sleep(0)
                # update dialog title
                self.dialog.title = re.compile(r"\(\d+\)").sub(
                    f"({cnt})", self.dialog.title
                )
                # create event widget
                card = CalendarEventCard(
                    dtstart=event["dtstart"].strftime("%d-%m-%Y %H:%M"),
                    dtend=event["dtend"].strftime("%d-%m-%Y %H:%M"),
                    summary=event["summary"].decode(),
                    description=event["description"].decode()
                    if event.get("description")
                    else "",
                )
                self.ids.table_layout.add_widget(card)

        # create abortable asynchronous loader
        self.asyncloader = asynckivy.start(set_items())

    def refresh(self):
        """
        Method to enforce reload of contents.
        """

        self.ids.table_layout.clear_widgets()
        self.init_ui()
        self.ids.refresh_layout.refresh_done()

    def create_search_tag(self):
        """
        Method to create a chip tag displaying the filter pattern.
        """

        # cancel asynchronouse loader if running
        if self.asyncloader is not None:
            self.asyncloader.cancel()

        self.ids.search.focus = True
        # retrieve the widlcard pattern from the text input field
        search_phrase = self.ids.search.text
        # check if search phrase contains '*'
        if (
            "*"
            not in search_phrase[
                :: len(search_phrase) > 1 and len(search_phrase) - 1 or 1
            ]
        ):
            search_phrase = "*" + search_phrase + "*" if search_phrase else "*"
        # add filter if not present yet
        if not any(
            [stacked.text == search_phrase for stacked in self.ids.stack.children]
        ):
            chip = SearchTag(text=search_phrase)
            chip.bind(on_press=self.remove_search_tag)
            self.ids.stack.add_widget(chip)
        # clear text input field
        self.ids.search.text = ""
        # reinitialize the gui components
        self.ids.table_layout.clear_widgets()
        self.init_ui()

    def remove_search_tag(self, bound_instance: MDChip):
        """
        Method to remove search tag from stack.

        Positional arguments:
            bound_instance: kivymd.uix.chip.MDChip,
                chip widget to remove.
        """

        # cancle asynchronous loader if running
        if self.asyncloader is not None:
            self.asyncloader.cancel()
        # remove chip from stack
        self.ids.stack.remove_widget(bound_instance)
        # clear claendar events
        self.ids.table_layout.clear_widgets()
        # reload
        self.init_ui()

    def get_date(self, boundary: str):
        """
        Dispatches date and time pickers to update either the start or
        the end date of the time range filter.

        Positional arguments:
            boundary: str,
                either "start" or "end"
        """

        if boundary in ("start", "end"):
            # cancel asynchronous loader if running
            if self.asyncloader is not None:
                self.asyncloader.cancel()

            def get_time():
                """
                Helper function to request datetime input from user.
                It dispatches a time picker dialog.
                """

                nonlocal self
                time_dialog = MDTimePicker()
                time_dialog.title = f"Filter by {boundary} time"
                time_dialog.set_time(getattr(self, boundary))

                def on_save_time(instance: MDTimePicker, time: datetime.time):
                    """
                    Action to be performed on selection.

                    Positional arguments:
                        instance: kivymd.uix.pickers.MDTimePicker,
                            time picker dialog.

                        time: datetime.time,
                            time object from user interaction.
                    """

                    nonlocal self
                    setattr(
                        self,
                        boundary,
                        getattr(self, boundary).replace(
                            hour=time.hour, minute=time.minute
                        ),
                    )
                    # if no search are present, add default one
                    if len(self.ids.stack.children) == 0:
                        chip = SearchTag(text="*")
                        chip.bind(on_press=self.remove_search_tag)
                        self.ids.stack.add_widget(chip)
                    # reload
                    self.ids.table_layout.clear_widgets()
                    self.init_ui()
                    instance.dismiss()

                time_dialog.bind(on_save=on_save_time)
                time_dialog.open()

            if self.start.date() != self.end.date():
                # if the dates in the range differ, dispatch dialog to retrieve datewha
                date_dialog = MDDatePicker(
                    year=getattr(self, boundary).year,
                    month=getattr(self, boundary).month,
                    day=getattr(self, boundary).day,
                )
                date_dialog.title = "Filter by start date"

                def on_save_date(
                    instance: MDDatePicker, value: datetime.date, date_range: list
                ):
                    """
                    Action to be performed on selection.

                    Positional arguments:
                        instance: kivymd.uix.pickers.MDDatePicker,
                            date picker dialog.

                        value: datetime.date,
                            date object from user interaction.

                        date_range:list,
                            not used.
                    """

                    nonlocal self
                    setattr(
                        self,
                        boundary,
                        getattr(self, boundary).replace(
                            year=value.year, month=value.month, day=value.day
                        ),
                    )
                    instance.dismiss()
                    get_time()

                date_dialog.bind(on_save=on_save_date)
                date_dialog.open()
            else:
                get_time()


class CalendarEvent(MDDialog):
    """
    Dialog widget displaying filtered calendar widgets.
    """

    # list of calendar events
    events = ListProperty([])

    # container for tags (chip widgets) to be set on startup
    initial_tags = ListProperty([])

    def __init__(
        self,
        *,
        events: tuple[dict[str, Any]],
        initial_tags: tuple[str],
        **kwargs: dict[str, Any],
    ):
        """
        Initializes calendar popup.

        Keyword arguments:
            events: tuple[dict[str,Any]],
                list of calendar events, given as:
                [{
                    "summary": bytes,
                    "description": bytes,
                    "dtstart": datetime.datetime,
                    "dtend": datetime.datetime,
                    "location": bytes
                }, ...]

            initial_tags: tuple[str],
                list of wildcard patterns used to match calendar events by summary.

        """

        self.events = events
        self.initial_tags = initial_tags
        self.content_cls = CalendarEventContent(dialog=self)
        super().__init__(**kwargs)
