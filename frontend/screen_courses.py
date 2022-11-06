# -*- coding: utf-8 -*-

import sys
from io import BytesIO
from itertools import cycle
from pathlib import Path
from typing import Any

import asynckivy
from kivy.clock import Clock
from kivy.input.motionevent import MotionEvent
from kivy.properties import (
    BooleanProperty,
    DictProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivymd.uix.banner import MDBanner
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.bottomsheet import MDCustomBottomSheet
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelTwoLine
from kivymd.uix.fitimage import FitImage
from kivymd.uix.list import (
    IconLeftWidgetWithoutTouch,
    IRightBodyTouch,
    OneLineIconListItem,
    ThreeLineAvatarIconListItem,
    ThreeLineIconListItem,
)
from kivymd.uix.screen import MDScreen
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.toolbar import MDTopAppBar

####################################
#                                  #
# preamble to provide package name #
#                                  #
####################################

if __name__ == "__main__" and __package__ is None:
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[2]
    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError:
        pass
    __package__ = ".".join(parent.parts[len(top.parts) :])

from ..backend import Client
from .popup_graph import GraphDialog
from .popup_progress import ProgressPopup
from .popup_save_dialog import SaveDialog

###############
#             #
# definitions #
#             #
###############


class CourseStartRecord(ThreeLineIconListItem):
    """
    Widget stored in a bottom sheet list used to display a startable course.
    """

    # keyword arguments required to start the course
    dispatch_ctx = DictProperty({})
    # reference to the "courses" screen
    screen = ObjectProperty(None)
    # reference to the containing widget
    parent_widget = ObjectProperty(None)

    def __init__(
        self,
        *args: tuple[Any],
        dispatch_context: dict[str, str],
        screen: MDScreen,
        parent_widget,
        **kwargs: dict[str, Any],
    ):
        """
        Creates class instance with necessary references.

        Positional arguments:
            *args: tuple[Any],
                positional arguments passed to the parent class.

        Keyword arguments:
            dispatch_context: dict[str,str],
                keyword arguments required to start given course:
                {
                    "enrolmentPeriodId": str,
                    "lectureSeriesId": str,
                    "curriculumEntryId": str,
                    "bookingId": str
                }

            screen: MDScreen,
                reference tot he implementing screen.

            **kwargs: dict[str,Any],
                keyword arguments of the parent class.
        """

        self.dispatch_ctx = dispatch_context
        self.screen = screen
        self.parent_widget = parent_widget
        super().__init__(**kwargs)

    @property
    def client(self):
        return self.screen.client

    @property
    def banner(self):
        return self.screen.ids.banner

    @property
    def bottom_sheet(self):
        return self.parent_widget.parent_widget.bottom_sheet

    def on_release(self):
        """
        Ought to be triggered on release of the class instance.
        """

        try:
            self.bottom_sheet.dismiss()
            self.client.dispatch(**self.dispatch_ctx)
            self.screen.refresh()
            self.banner.text = [
                "Successfully started new course!",
                "It might take some time till the change takes the effect though...",
            ]
            self.banner.show()
        except BaseException as ex:
            # send warning as the banner of the "courses" screen
            self.banner.text = [
                "Error occured processing the request to start the course!",
                ex.args[0][:1].upper() + ex.args[0][1:] + ".",
            ]
            self.banner.show()


class CourseRegisrationRecordContent(MDBoxLayout):
    """
    Content for the bottom sheet object of the CourseRegisrationRecord.
    """

    # reference to the parent widget
    parent_widget = ObjectProperty(None)


class CourseRegisrationRecord(ThreeLineAvatarIconListItem):
    """
    List item displayed as record representing a bookable course.
    """

    # keyword arguments passed to the client interface to enroll
    booking_ctx = DictProperty({})
    # status flag
    is_enrolled = BooleanProperty(False)
    # container for bottom sheet listing available course subjects/lectures
    bottom_sheet_content = ObjectProperty(None)
    # reference to the checkbox triggering enrollment
    enroll_checkbox = ObjectProperty(None)
    # reference to the "courses" screen instance
    screen = ObjectProperty(None)
    # reference to opened bottom sheet instance
    bottom_sheet = ObjectProperty(None)

    def __init__(
        self,
        *,
        booking: dict[str, str],
        is_enrolled: bool,
        bottom_sheet_content: MDCustomBottomSheet,
        screen: MDScreen,
        **kwargs: dict[str, Any],
    ):
        """
        Creates bookable course record.

        Keyword arguments:
            booking: dict[str,str],
                set of keyword arguments to pass to the client instance for enrollment.

            is_enrolled: bool,
                status flag denoting the enrollment of the course record.

            bottom_sheet_content: MDCustomBottomSheet,
                list of available course subjects/lectures.

            screen: MDScreen,
                reference to the "courses" screen instance.

            **
        """
        self.booking_ctx = booking
        self.is_enrolled = is_enrolled
        self.bottom_sheet_content = bottom_sheet_content
        self.screen = screen

        # create checkbox
        self.enroll_checkbox = CourseEnroll(parent_widget=self, active=self.is_enrolled)

        # create widget with left icon and checkbox on the right side
        super().__init__(
            IconLeftWidgetWithoutTouch(icon="book-plus-multiple-outline"),
            self.enroll_checkbox,
            **kwargs,
        )

    @property
    def client(self) -> Client:
        """
        Access point to the client interface.

        Returns:
            backend.Client
        """

        return self.screen.client

    def on_release(self):
        """
        Ought to be triggered on release of the class instance.
        """

        if not self.enroll_checkbox.active:
            # course is not enrolled yet, so perform enrollment
            self.enroll_checkbox.on_active(self, True)
            self.enroll_checkbox.active = True
        # open bottom sheet list
        if self.enroll_checkbox.is_enrolled:
            self.bottom_sheet = MDCustomBottomSheet(screen=self.bottom_sheet_content)
            self.bottom_sheet.open()
        return super().on_release()


class CourseEnroll(IRightBodyTouch, MDCheckbox):
    """
    Customized checkbox to be implemented as widget on the right side of a ThreeLineAvatarIconListItem.
    """

    # reference to the parent widget
    parent_widget = ObjectProperty(None)
    # reference to asynchronous content loader
    # to track the content loading routine
    asyncloader = ObjectProperty(None)

    def __init__(
        self, *, parent_widget: ThreeLineAvatarIconListItem, **kwargs: dict[str, Any]
    ):
        """
        Creates chekbox widget for the ThreeLineAvatarIconListItem.

        Keyword arguments:
            parent_widget: ThreeLineAvatarIconListItem,
                widget implementing instance of this class.

            **kwargs: dict[str,Any],
                keyword arguments passed to the kivymd.uix.selectioncontrol.MDCheckbox class.
        """

        self.parent_widget = parent_widget
        MDCheckbox.__init__(self, **kwargs)
        IRightBodyTouch.__init__(self)

    @property
    def client(self) -> Client:
        """
        Access point to the client interface.

        Returns:
            backend.Client
        """

        return self.parent_widget.client

    @property
    def is_enrolled(self) -> bool:
        """
        Access point to the "is_enrolled" property of the parent_widget.

        Returns:
            bool
        """

        return self.parent_widget.is_enrolled

    @is_enrolled.setter
    def is_enrolled(self, value: bool):
        """
        Access point (setter) for the "is_enrolled" property of the parent_widget.
        """
        self.parent_widget.is_enrolled = value

    @property
    def banner(self) -> MDBanner:
        """
        Access point to the "banner" of the "main" screen.

        Returns:
            kivymd.uix.banner.MDBanner
        """

        return self.parent_widget.screen.ids.banner

    def on_active(self, bound_instance: MDCheckbox, check: bool):
        """
        Triggered when checkbox is toggled.

        Positional arguments:
            bound_instance: MDCheckbox,
                checkbox instance to which the method is bound.

            check: bool,
                indicates the state of the checbox.
        """

        if self.asyncloader is not None and not self.asyncloader.done:
            return

        async def book():
            """
            Asynchronous worker performing the enrollment.
            """

            if check and not self.is_enrolled:
                try:
                    # enroll
                    self.client.enroll(**self.parent_widget.booking_ctx)
                    self.is_enrolled = True
                except BaseException as ex:
                    # send warning as the banner of the main screen
                    self.banner.text = [
                        "Error occured while enrolling!",
                        ex.args[0][:1].upper() + ex.args[0][1:] + ".",
                    ]
                    self.banner.show()
                    self.active = not check
            elif not check and self.is_enrolled:
                try:
                    # cancel enrollment
                    self.client.cancel(**self.parent_widget.booking_ctx)
                    self.is_enrolled = False
                except BaseException as ex:
                    # send warning as the banner of the main screen
                    self.banner.text = [
                        "Error occured while cancelling enrollment!",
                        ex.args[0][:1].upper() + ex.args[0][1:] + ".",
                    ]
                    self.banner.show()
                    self.active = check

        # dispatch
        self.asyncloader = asynckivy.start(book())
        return super().on_active(bound_instance, check)


class CourseImage(AsyncImage, FitImage):
    """
    Asynchronous loader for course images.
    """

    # numeric proeprty identifying a course
    course_id = NumericProperty(0)

    def __init__(self, *, course_id: int, **kwargs: dict[str, Any]):
        """
        Create instance of course image loader.

        Keyword arguments:
            course_id: int,
                internal course id.

            **kwargs: dict[str,Any],
                keyword arguments passed to the constructors of
                kivy.uix.image.AsyncImage and
                kivymd.uix.fitimage.FitImage.
        """

        self.course_id = course_id
        return super().__init__(**kwargs)


class CourseResources(MDBoxLayout):
    """
    Custom widget used to list all available course resources (downloadbale contents).
    """

    # internal course id
    course_id = NumericProperty(0)
    # screen utilizing widget
    screen = ObjectProperty(None)
    # list of resources
    resources = ListProperty([])
    # place holder for the content of the target file
    content = ObjectProperty(None)
    # data type of the content (MIME)
    content_disposition = StringProperty("")

    def __init__(
        self,
        *,
        course_id: int,
        screen: MDScreen,
        resources: dict[str, str],
        **kwargs: dict[str, Any],
    ):
        """
        Initializes widget.

        Keyword arguments:

            course_id: int,
                internal course id.

            screen: MDScreen,
                reference to the screen instance implementing the widget.

            resources:dict[str,str],
                list of resources: [
                    {
                        "link": str,
                        "title": str
                    }
                ]

            **kwargs: dict[str,Any],
                keyword arguments passed to the constructor of
                kivymd.uix.boxlayout.MDBoxLayout.

        """
        self.course_id = course_id
        self.screen = screen
        self.resources = list(filter(lambda x: isinstance(x, dict), resources))
        super().__init__(**kwargs)
        for resource in self.resources:
            # create button instance
            download_btn = OneLineIconListItem(
                IconLeftWidgetWithoutTouch(icon="download-outline"),
                text=resource.get("title"),
            )
            download_btn.bind(
                on_release=lambda bound_instance: self.download(
                    bound_instance, resource.get("link")
                )
            )
            self.add_widget(download_btn)

    @property
    def client(self) -> Client:
        return self.screen.client

    @property
    def use_cache(self) -> bool:
        return self.screen.main_screen.use_cache

    @property
    def banner(self) -> MDBanner:
        return self.screen.ids.banner

    def download(self, bound_instance: Button, link: str):
        """
        Performs download of given course resource and sipatches a dialog
        to determine the target location for the downloaded content.

        Positional arguments:
            bound_instance: kivy.uix.button.Button,
                button instance bound to this widget.

            link: str,
                URI of the file to download.
        """

        bound_instance.disabled = True
        # dispatch progress popup
        popup = ProgressPopup(title="Downloading...")
        popup.open()

        def perform_download(self, popup: MDDialog):
            """
            Worker downloading the content and updating the progress dialog.

            Positional arguments:
                popup: kivymd.uix.dialog.MDDialog,
                    instance of a progress dialog.
            """
            try:
                # set status message
                popup.status_msg = "Downloading..."
                #  download in chunks
                buff = BytesIO()
                chunk_size = 1024
                (
                    content_disposition,
                    content_iterator,
                    content_length,
                ) = self.client.download(link, cached=self.use_cache, chunk=chunk_size)
                self.content_disposition = content_disposition
                popup.total = content_length
                for i, chunk in enumerate(content_iterator):
                    buff.write(chunk)
                    # update progress bar
                    popup.prog_val = i * chunk_size

                # finished
                popup.status_msg = "Download completed"
                self.content = buff

            except BaseException as ex:
                # propagate exception
                popup.exception = ex

            finally:
                popup.dismiss()

        # dispatch worker as child thread (coroutine)
        popup.run_worker(perform_download, self, popup)

        def perfom_switch(dt):
            """
            Watch-dog waiting for the completing of the child thread.

            Positional arguments:
                dt: int
                    interval in seconds denoting the lookup frequency.
            """

            if popup.has_started and popup.exception is None:
                # child thread still running...
                Clock.schedule_once(perfom_switch, dt)
            else:
                # worker has finished
                if isinstance(popup.exception, Exception):
                    self.banner.text = [
                        "Download in failed!",
                        popup.exception.args[0][:1].upper()
                        + popup.exception.args[0][1:]
                        + ".",
                    ]
                    self.banner.show()
                else:
                    # dispatch save dialog to get location to save the target file
                    spopup = SaveDialog(
                        content_disposition=self.content_disposition,
                        save_method=lambda file, path: self.client.save(
                            file, self.content.getvalue(), Path(path)
                        ),
                        banner=self.banner,
                    )
                    spopup.open()
                    bound_instance.disabled = False

        # dispatch watch-dog
        perfom_switch(1)


class CoursesExpansionPanel(MDExpansionPanel):
    """
    Custom expansion panel used to list courses and available course resources
    as drop down panel list.
    """


class CourseCard(MDCard):
    """
    Container for the custom expansion panel.
    """


class CoursesBottomNavigation(MDBottomNavigation):
    """
    Tab manager for the course overview used to cluster the courses into categories.
    """

    def on_switch_tabs(
        self, bottom_navigation_item: MDBottomNavigationItem, name_tab: str
    ):
        """
        Called when switching between tabs.

        Positional arguments:
            bottom_navigation_item: MDBottomNavigationItem,
                instance of navigation item.

            name_tab: str,
                name of the tab to switch over.
        """
        tabs = {"active": 0, "inactive": 1, "bookable": 2}
        # determine direction of the transition
        if tabs.get(self.current, 0) > tabs.get(name_tab, 0):
            self.ids.tab_manager.transition.direction = "right"
        else:
            self.ids.tab_manager.transition.direction = "left"
        # perform switch
        self.current = name_tab
        return super().on_switch_tabs(bottom_navigation_item, name_tab)

    def on_touch_move(self, touch: MotionEvent):
        """
        Switch months pages by touch move.

        Positional arguments:
            touch: MotionEvent,
                touch event.
        """

        nav_items = (
            (self.ids.bookable_nav_item, "bookable"),
            (self.ids.inactive_nav_item, "inactive"),
            (self.ids.active_nav_item, "active"),
        )
        to_left = cycle(nav_items)
        to_right = cycle(reversed(nav_items))
        # left - previous
        if touch.dpos[0] < -30:
            for _, name in to_left:
                if self.current == name:
                    self.on_switch_tabs(*next(to_left))
                    break
        # right - next
        elif touch.dpos[0] > 30:
            for _, name in to_right:
                if self.current == name:
                    self.on_switch_tabs(*next(to_right))
                    break


class CourseBrowser(MDScreen):
    """
    Screen view listing all available courses.
    """

    # reference to the "main" screen
    main_screen = ObjectProperty(None)
    # list of courses (for internal usage only)
    resources = ListProperty([])
    # list of bookable courses (for internal usage only)
    bookable = DictProperty({})
    # dependency graph
    dependencies = ObjectProperty(None)
    # reference to asynchronous content loader
    # to track the content loading routine
    asyncloader = ObjectProperty(None)

    def __init__(self, *, main_screen: MDScreen, **kwargs: dict[str, Any]):
        """
        Initialize the screen view.

        Keyword arguments:
            main_screen: kivymd.uix.screen.MDScreen,
                reference to the "main" screen instance.

            **kwargs: dict[str,Any],
                keyword arguments passed to the MDScreen class.
        """

        self.main_screen = main_screen
        super().__init__(**kwargs)

        def experimental_warning(*args):
            print(args)
            self.ids.banner.text = [
                "Warning!",
                "This functionality is experimental and provided without warranty!",
            ]
            self.ids.banner.show()

        self.ids.bookable_nav_item.bind(on_tab_press=experimental_warning)
        # retrieve courses
        self.get_courses()

    @property
    def client(self) -> Client:
        return self.main_screen.client

    @property
    def top_bar(self) -> MDTopAppBar:
        return self.main_screen.ids.top_bar

    @property
    def use_cache(self) -> bool:
        return self.main_screen.use_cache

    @use_cache.setter
    def use_cache(self, value: bool):
        self.main_screen.use_cache = value

    def init_ui(self):
        """
        Method used to create necessary widgets.
        """

        async def set_courses():
            """
            Asynchronous worker to load widgets in a non-blocking way.
            """

            # course is a dict describing a course records
            # resources is a lit of downloadable course resources
            for course, resources in self.resources:
                await asynckivy.sleep(0)
                # create text label for expansion panel
                lines = MDExpansionPanelTwoLine(
                    text=course.get("fullname"),
                    secondary_text=course.get("shortname"),
                )
                # create course image
                img = CourseImage(
                    course_id=course.get("id"),
                    source=course.get("img"),
                    height=lines.height,
                )
                # container for the image and expansion panel
                layout = MDBoxLayout(
                    orientation="horizontal",
                    spacing="10dp",
                    adaptive_height=True,
                    size_hint=(1, None),
                )
                layout.add_widget(img)
                # create expansion panel
                panel = CoursesExpansionPanel(
                    content=CourseResources(
                        course_id=course.get("id"), screen=self, resources=resources
                    ),
                    panel_cls=lines,
                )
                layout.add_widget(panel)
                # wrap contents inside a card widget
                card = CourseCard()
                card.add_widget(layout)
                # sort out active and inactive courses
                if course.get("state") == "active":
                    self.ids.active_table_layout.add_widget(card)
                else:
                    self.ids.inactive_table_layout.add_widget(card)
                # update badge icons
                self.ids.active_nav_item.badge_icon = (
                    f"numeric-{len(self.ids.active_table_layout.children)}"
                )
                self.ids.inactive_nav_item.badge_icon = (
                    f"numeric-{len(self.ids.inactive_table_layout.children)}"
                )
                # update the navigation item in the navigation drawer of the "main" screen
                self.main_screen.courses_btn.right_text = f"({len(self.resources)})"

        async def set_bookable_courses():
            """
            Second asynchrounous worker updating the bookable courses.
            """

            if self.bookable:
                for semester in self.bookable["semesters"]:
                    for subject in sorted(
                        filter(
                            # retrieve not courses where at least one
                            # subject/lecture is not started yet
                            lambda x: any(
                                [not lecture["isStarted"] for lecture in x["lectures"]]
                            )
                            and x["booking"],
                            semester["subjects"],
                        ),
                        key=lambda x: x["name"],
                    ):
                        await asynckivy.sleep(0)
                        # container for list items
                        content = CourseRegisrationRecordContent()
                        # fill container with not started subjects/lectures
                        for lecture in filter(
                            lambda x: not x["isStarted"], subject["lectures"]
                        ):
                            if lecture.get("dispatching"):
                                content.ids.container.add_widget(
                                    CourseStartRecord(
                                        IconLeftWidgetWithoutTouch(
                                            icon="book-plus-outline"
                                        ),
                                        screen=self,
                                        dispatch_context=lecture["dispatching"],
                                        parent_widget=content,
                                        text=lecture["name"],
                                        secondary_text="(%s)" % lecture["shortname"],
                                        tertiary_text="%d credits" % lecture["credits"],
                                    )
                                )
                        # add bookable course list record
                        reg_record = CourseRegisrationRecord(
                            text=subject["name"],
                            secondary_text="(%s)" % subject["shortname"],
                            tertiary_text=semester["cluster"],
                            is_enrolled=subject["isEnrolled"],
                            booking=subject["booking"],
                            bottom_sheet_content=content,
                            screen=self,
                        )
                        content.parent_widget = reg_record
                        self.ids.bookable_table_layout.add_widget(reg_record)
                # update badge icon
                self.ids.bookable_nav_item.badge_icon = (
                    f"numeric-{len(self.ids.bookable_table_layout.children)}"
                )

        async def all_together():
            """
            Dispatch both workers one after another.
            """

            await set_courses()
            await set_bookable_courses()

        self.asyncloader = asynckivy.start(all_together())

    def refresh(self):
        """
        Method enforces refreshment of the data and displayed widgets.
        """

        def refresh_callback(interval):
            # do nothing if already dispatched
            if self.asyncloader is not None and not self.asyncloader.done:
                return

            # clear widgets from tabs
            self.ids.active_table_layout.clear_widgets()
            self.ids.inactive_table_layout.clear_widgets()
            self.ids.bookable_table_layout.clear_widgets()
            # clear data
            self.use_cache = False
            self.resources = []
            self.bookable = {}
            # fetch data and setup ui
            self.get_courses()
            self.use_cache = True
            # signalize completion
            self.ids.active_refresh_layout.refresh_done()
            self.ids.inactive_refresh_layout.refresh_done()
            self.ids.bookable_refresh_layout.refresh_done()

        Clock.schedule_once(refresh_callback, 1)

    def on_enter(self, *args):
        """
        Called when entering the screen.

        Positional arguments:
            *args: tuple[Any],
                arguments forwarded to kivymd.uix.screen.MDScreen.on_enter method.
        """

        # list of temporary top panel entries
        self.to_remove = [
            [
                "information-variant",
                self.show_stats,
                "Show available credits",
                "Show available credits",
            ],
            [
                "graph-outline",
                self.show_dependencies,
                "Draw dependency graph",
                "Draw dependency graph",
            ],
        ]
        # extend top bar of "main" screen
        for item in self.to_remove:
            if item not in self.top_bar.right_action_items:
                self.top_bar.right_action_items.insert(0, item)
        self.top_bar.title = "Course access"
        super().on_enter(*args)

    def on_leave(self, *args):
        """
        Called when leaving the screen.

        Positional arguments:
            *args: tuple[Any],
                arguments forwarded to MDScreen.on_leave method.
        """

        # remove temporary top panel entries
        for item in self.to_remove:
            try:
                self.top_bar.right_action_items.remove(item)
            except ValueError:
                pass
        return super().on_leave(*args)

    def show_dependencies(self, bound_instance: Button):
        """
        Dispatches a popup dialog displaying the dependency graph.

        Positional arguments:
            bound_instance: kivy.iux.button.Button,
                button bound to the method.
        """

        dialog = GraphDialog(
            title="Course dependency graph", graph=self.dependencies, screen=self
        )
        dialog.open()

    def show_stats(self, bound_instance: Button):
        """
        Dispatches a banner popup displaying current credits.

        Positional arguments:
            bound_instance: kivy.iux.button.Button,
                button bound to the method.
        """

        self.ids.banner.text = [
            f"{self.bookable['counts']['booked']:>3} credit points are already booked,",
            f"{self.bookable['counts']['remaining']:>3} credit points still remaining.",
        ]
        self.ids.banner.show()

    def get_courses(self):
        """
        Method fetches relevant course data and initualizes the UI.
        """

        # dispatch progress dialog
        popup = ProgressPopup(title="Loading...")
        popup.open()

        def perform_load(self, popup: MDDialog):
            """
            Worker loading the data and updating the sprogress bar.

            Positional arguments:
                popup: kivymd.uix.dialog.MDDialog,
                    dialog holding progress bar.
            """

            try:
                # prepare data containers
                resources = list()
                courses = list(
                    sorted(
                        self.client.list_courses(cached=self.use_cache),
                        key=lambda x: x.get("fullname"),
                    )
                )

                # collect course resources
                for idx, course in enumerate(courses):
                    resources.append(
                        [
                            course,
                            self.client.list_course_resources(
                                course.get("id"), cached=self.use_cache
                            ),
                        ]
                    )
                    popup.status_msg = (
                        f"Loading resources for the course {course.get('fullname')}..."
                    )
                    popup.prog_val = int(100 * (idx + 1) / len(courses))

                # reset progress bar
                popup.status_msg = "Obtaining booking information..."
                popup.prog_val = 0
                popup.schedule_auto_update(15, 0.3)

                # fetch bookable courses
                self.bookable = self.client.get_courses_to_register(
                    cached=self.use_cache
                )
                self.resources = resources
                popup.status_msg = "Preparing dependency graph..."
                self.dependencies = self.client.get_dependency_graph(
                    cached=self.use_cache
                )

                popup.pro_val = 100

            except BaseException as ex:
                # forward exception
                popup.exception = ex

            finally:
                popup.dismiss()

        # dispatch coroutine as child thread
        popup.run_worker(perform_load, self, popup)

        def wait_on_load(dt):
            """
            Watch-dog monitoring the status of the running worker.

            Positional arguments:
                dt: int,
                    interval in seconds at which the watch-dog performs
                    lookups.
            """

            if popup.has_started and popup.exception is None:
                # worker still running
                Clock.schedule_once(wait_on_load, dt)
            else:
                # worker has completed
                if isinstance(popup.exception, Exception):
                    # dispatch banner with warning
                    self.ids.banner.text = [
                        "Failed to load course resources!",
                        popup.exception.args[0][:1].upper()
                        + popup.exception.args[0][1:]
                        + ".",
                    ]
                    self.ids.banner.show()
                else:
                    # trigger update of the UI
                    Clock.schedule_once(lambda dt: self.init_ui(), 1)
                    popup.dismiss()

        # dispatch watch-dog
        wait_on_load(1)
