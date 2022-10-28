# -*- coding: utf-8 -*-

from tkinter import Button
from kivy.properties import (ObjectProperty, NumericProperty, StringProperty, BooleanProperty, ListProperty, DictProperty)
from kivy.uix.image import AsyncImage
from kivymd.uix.bottomnavigation import MDBottomNavigation
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.expansionpanel import (MDExpansionPanel, MDExpansionPanelTwoLine)
from kivymd.uix.card import MDCard
from kivymd.uix.fitimage import FitImage
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import (
    OneLineIconListItem, 
    IconLeftWidget,
    IconLeftWidgetWithoutTouch,
    ThreeLineIconListItem,
    IRightBodyTouch,
    ThreeLineAvatarIconListItem
)
from kivy.clock import Clock
from kivymd.uix.bottomsheet import MDCustomBottomSheet
from kivymd.uix.selectioncontrol import MDCheckbox
from io import BytesIO
from pathlib import Path
import asynckivy
from typing import Any
from kivymd.uix.dialog.dialog import MDDialog

####################################
#                                  #
# preamble to provide package name #
#                                  #
####################################

import sys
from pathlib import Path

if __name__ == '__main__' and __package__ is None:
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[1]
    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError:
        pass
    __package__ = '.'.join(parent.parts[len(top.parts):])

from .popup_progress import ProgressPopup
from .popup_save_dialog import SaveDialog

###############
#             #
# definitions #
#             #
###############

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
    # reference to the "main" screen instance
    main_screen = ObjectProperty(None)


    def __init__(
        self, *, 
        booking:dict[str,str], 
        is_enrolled:bool, 
        bottom_sheet_content:MDCustomBottomSheet, 
        main_screen:MDScreen, **kwargs:dict[str,Any]
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
                reference to the "main" screen instance.

            **
        """
        self.booking_ctx = booking
        self.is_enrolled = is_enrolled
        self.bottom_sheet_content = bottom_sheet_content
        self.main_screen = main_screen

        # create checkbox
        self.enroll_checkbox = CourseEnroll(parent_widget=self, active=self.is_enrolled)

        # create widget with left icon and checkbox on the right side
        super().__init__(
            IconLeftWidgetWithoutTouch(icon="book-plus-multiple-outline"),
            self.enroll_checkbox,
            **kwargs
        )

    @property
    def client(self) -> main_screen.client:
        """
        Access point to the client interface.

        Returns:
            backend.Client
        """

        return self.main_screen.client

    def on_release(self):
        """
        Ought to be triggered on release of the class instance.
        """

        if self.enroll_checkbox.active:
            # open bottom sheet list if course enrolled
            MDCustomBottomSheet(screen=self.bottom_sheet_content).open()
        else:
            # course is not enrolled yet, so dipatch a notification banner
            self.main_screen.ids.banner.text = [
                f'You did not enroll yet for the course "{self.text}"!',
                "Toogle the checkbox on the right side to enroll, please."
            ]
            self.main_screen.ids.banner.show()
        return super().on_release()

class CourseEnroll(IRightBodyTouch, MDCheckbox):
    """
    Customized checkbox to be implemented as widget on the right side of a ThreeLineAvatarIconListItem.
    """

    # reference to the parent widget
    parent_widget = ObjectProperty(None)

    def __init__(
        self, *, 
        parent_widget:ThreeLineAvatarIconListItem, 
        **kwargs:dict[str,Any]
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
        super().__init__(self, **kwargs)

    
    @property
    def client(self) -> parent_widget.client:
        """
        Access point to the client interface.

        Returns:
            backend.Client
        """

        return self.parent_widget.client

    @property
    def is_enrolled(self) -> parent_widget.is_enrolled:
        """
        Access point to the "is_enrolled" property of the parent_widget.

        Returns:
            bool
        """

        return self.parent_widget.is_enrolled

    @is_enrolled
    def is_enrolled(self, value:bool):
        """
        Access point (setter) for the "is_enrolled" property of the parent_widget.
        """
        self.parent_widget.is_enrolled = value

    @property
    def banner(self) -> parent_widget.main_screen.ids.banner:
        """
        Access point to the "banner" of the "main" screen.

        Returns:
            kivymd.uix.banner.MDBanner
        """

        return self.parent_widget.main_screen.ids.banner

    def on_active(self, bound_instance:MDCheckbox, check:bool):
        """
        Triggered when checkbox is toggled.

        Positional arguments:
            bound_instance: MDCheckbox,
                checkbox instance to which the method is bound.

            check: bool,
                indicates the state of the checbox.
        """

        async def book():
            """
            Asynchronous worker performing the enrollment.
            """

            if check and not self.is_enrolled: 
                try:
                    # enroll
                    self.client.enroll(**self.master.booking_ctx)
                    self.is_enrolled = True
                except BaseException as ex:
                    # send warning as the banner of the main screen
                    self.banner.text = [
                        f'Error occured while enrolling"!',
                        ex.args[0][:1].upper()+ex.args[0][1:]+"."
                    ]
                    self.banner.show()
                    self.active = not check
            elif not check and self.master.is_enrolled:
                try:
                    # cancel enrollment
                    self.client.cancel(**self.master.booking_ctx)
                    self.is_enrolled = False
                except BaseException as ex:
                    # send warning as the banner of the main screen
                    self.banner.text = [
                        f'Error occured while cancelling enrollment"!',
                        ex.args[0][:1].upper()+ex.args[0][1:]+"."
                    ]
                    self.banner.show()
                    self.active = check

        # dispatch
        asynckivy.start(book())
        return super().on_active(bound_instance, check)

class CourseImage(AsyncImage, FitImage):
    """
    Asynchronous loader for course images.
    """

    # numeric proeprty identifying a course
    course_id = NumericProperty(0)

    def __init__(self, *, course_id:int, **kwargs:dict[str,Any]):
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
    content_disposition = StringProperty('')

    def __init__(
        self, *, 
        course_id:int, 
        screen:MDScreen,
        resources:dict[str,str],
        **kwargs:dict[str,Any]
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
        self.resources = resources
        super().__init__(**kwargs)
        for i in self.resources:
            # create button instance
            download_btn = OneLineIconListItem(
                IconLeftWidgetWithoutTouch(icon="download-outline"), 
                text=i.get("title")
            )
            download_btn.bind(on_release=lambda bound_instance: self.download(bound_instance, i.get('link')))
            self.add_widget(download_btn)

    @property
    def client(self) -> screen.client:
        """
        Access point to the client interface.

        Returns:
            backend.Client
        """

        return self.screen.client

    @property
    def use_cache(self) -> screen.main_screen.use_cache:
        """
        Access point to the "use_cache" property of the main screen.

        Returns:
            bool
        """

        return self.screen.main_screen.use_cache

    @property
    def banner(self) -> screen.main_screen.ids.banner:
        """
        Access point to the banner instance of the main screen.

        Returns:
            kivymd.uix.banner.MDBanner
        """

        return self.screen.main_screen.ids.banner
            
    def download(self, bound_instance:Button, link:str):
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

        def perform_download(self, popup:MDDialog):
            """
            Worker downloading the content and updating the progress dialog.

            Positional arguments:
                popup: kivymd.uix.dialog.dialog.MDDialog,
                    instance of a progress dialog.
            """
            try:
                # set status message
                popup.status_msg = "Downloading..."
                #  download in chunks
                buff = BytesIO()
                chunk_size = 1024
                content_disposition, content_iterator, content_length = self.client.download(
                    link, cached=self.use_cache, chunk=chunk_size
                )
                self.content_disposition = content_disposition
                popup.total = content_length
                for i, chunk in enumerate(content_iterator):
                    buff.write(chunk)
                    # update progress bar
                    popup.prog_val = i*chunk_size

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

            if popup.has_started and popup.exception == None:
                # child thread still running...
                Clock.schedule_once(perfom_switch, dt)
            else:
                # worker has finished
                if isinstance(popup.exception, Exception):
                    self.banner.text = [
                        "Download in failed!",
                        popup.exception.args[0][:1].upper()+popup.exception.args[0][1:]+"."
                    ]
                    self.banner.show()
                else:
                    # dispatch save dialog to get location to save the target file
                    spopup = SaveDialog(
                        content_disposition=self.content_disposition, 
                        save_method=lambda file, path: self.client.save(file, self.content.getvalue(), Path(path)),
                        banner=self.banner
                    )
                    spopup.open()
                    bound_instance.disabled = False

        # dispatch watch-dog
        perfom_switch(1)

class CoursesExpansionPanel(MDExpansionPanel):
    pass

class CourseCard(MDCard):
    pass

class CoursesBottomNavigation(MDBottomNavigation):
    def on_switch_tabs(self, bottom_navigation_item, name_tab: str):
        tabs = {"active": 0, "inactive": 1, "bookable": 2}
        if tabs.get(self.current, 0) > tabs.get(name_tab, 0):
            self.ids.tab_manager.transition.direction = "right"
        else:
            self.ids.tab_manager.transition.direction = "left"
        self.current = name_tab
        return super().on_switch_tabs(bottom_navigation_item, name_tab)

class CourseBrowser(MDScreen):      
    master = ObjectProperty(None)
    resources = ListProperty([])
    bookable = DictProperty({})

    def __init__(self, **kwargs):
        self.master = kwargs.pop('master')
        super().__init__(**kwargs)
        self.get_courses()

    def set_items(self):
        async def set_items():                 
            for course, resources in self.resources:
                await asynckivy.sleep(0)
                lines = MDExpansionPanelTwoLine(
                    text=course.get("fullname"),
                    secondary_text=course.get("shortname"),
                )
                img = CourseImage(
                    course_id=course.get('id'), 
                    source=course.get('img'), 
                    height=lines.height
                )
                layout = MDBoxLayout(
                    orientation='horizontal', 
                    spacing='10dp', 
                    adaptive_height=True,
                    size_hint=(1, None)
                )
                layout.add_widget(img)
                panel = CoursesExpansionPanel(
                    content=CourseResources(
                        course_id=course.get('id'), 
                        master=self, 
                        resources=resources
                    ),
                    panel_cls=lines
                )
                layout.add_widget(panel)
                card = CourseCard()
                card.add_widget(layout)
                if course.get("state") == "active":
                    self.ids.active_table_layout.add_widget(card)
                else:
                    self.ids.inactive_table_layout.add_widget(card)
                self.ids.active_nav_item.badge_icon = f"numeric-{len(self.ids.active_table_layout.children)}"
                self.ids.inactive_nav_item.badge_icon = f"numeric-{len(self.ids.inactive_table_layout.children)}"
                self.master.courses_btn.right_text = f"({len(self.resources)})"
        async def set_bookable_items():
            if self.bookable:
                for semester in self.bookable["semesters"]:
                    for subject in sorted(
                        filter(
                            lambda x: any([not l["isStarted"] for l in x["lectures"]]) and x["booking"], 
                            semester["subjects"]
                        ),
                        key=lambda x: x["name"]
                    ):
                        await asynckivy.sleep(0)
                        layout = MDBoxLayout(id="container", orientation="vertical", adaptive_height=True)
                        for lecture in filter(lambda x: not x["isStarted"], subject["lectures"]):
                            layout.add_widget(
                                ThreeLineIconListItem(
                                    IconLeftWidgetWithoutTouch(
                                        icon="book-plus-outline"
                                    ),
                                    text=lecture["name"],
                                    secondary_text="(%s)" % lecture["shortname"],
                                    tertiary_text="%d credits" % lecture["credits"]
                                )
                            )
                        self.ids.bookable_table_layout.add_widget(CourseRegisrationRecord(
                            text=subject["name"],
                            secondary_text="(%s)" % subject["shortname"],
                            tertiary_text = semester["cluster"],
                            is_enrolled=subject["isEnrolled"],
                            booking=subject["booking"],
                            bottom_sheet_content=layout,
                            master=self
                        ))
                self.ids.bookable_nav_item.badge_icon = f"numeric-{len(self.ids.bookable_table_layout.children)}"
            
        asynckivy.start(asynckivy.and_(set_items(), set_bookable_items()))

    def refresh(self, *args):

        def refresh(interval):
            self.ids.active_table_layout.clear_widgets()
            self.ids.inactive_table_layout.clear_widgets()
            self.ids.bookable_table_layout.clear_widgets()
            self.master.use_cache = False
            self.resources = []
            self.get_courses()
            self.master.use_cache = True
            self.ids.active_refresh_layout.refresh_done()
            self.ids.inactive_refresh_layout.refresh_done()
            self.ids.bookable_refresh_layout.refresh_done()

        Clock.schedule_once(refresh, 1)

    def on_enter(self, *args):
        self.to_remove = [
            ['information-variant', self.show_stats, 'Show available credits', 'Show available credits']
        ]
        for item in self.to_remove:
            if item not in self.master.ids.top_bar.right_action_items:
                self.master.ids.top_bar.right_action_items.insert(0, item)
        self.master.ids.top_bar.title = "Course access"
        super().on_enter(*args)
        
    def on_leave(self, *args):
        for item in self.to_remove:
            self.master.ids.top_bar.right_action_items.remove(item)
        return super().on_leave(*args)

    def show_stats(self, bound_instance):
        self.ids.banner.text = [
            f"{self.bookable['counts']['booked']:>3} credit points are already booked,",
            f"{self.bookable['counts']['remaining']:>3} credit points still remaining."
        ]
        self.ids.banner.show()
        
    def get_courses(self):
        popup = ProgressPopup(title="Loading...")
        popup.open()

        def perform_load(self, popup):
            try:
                resources = list()
                courses = list(
                    sorted(
                        self.master.manager.client.list_courses(cached=self.master.use_cache), 
                        key=lambda x: x.get('fullname')
                    )
                )
                
                for idx, course in enumerate(courses):
                    resources.append([course, self.master.manager.client.list_course_resources(
                        course.get('id'), cached=self.master.use_cache
                    )])
                    popup.status_msg = f"Loading resources for the course {course.get('fullname')}..."
                    popup.prog_val = int(100*(idx+1)/len(courses))

                popup.status_msg = "Obtaining booking information..."
                popup.prog_val = 0
                popup.schedule_auto_update(15, .3)

                self.bookable = self.master.manager.client.get_courses_to_register(cached=self.master.use_cache)
                self.resources = resources

                popup.pro_val = 100
                
            except BaseException as ex:
                popup.exception = ex

            finally:
                popup.dismiss()
    
        popup.run_worker(perform_load, self, popup)

        def wait_on_load(dt):
            if popup.has_started and popup.exception == None:
                Clock.schedule_once(wait_on_load, dt)
            else:
                if isinstance(popup.exception, Exception):
                    self.ids.banner.text = [
                        "Failed to load course resources!",
                        popup.exception.args[0][:1].upper()+popup.exception.args[0][1:]+"."
                    ]
                    self.ids.banner.show()
                else:
                    self.set_items()
                    popup.dismiss()

        wait_on_load(1)

