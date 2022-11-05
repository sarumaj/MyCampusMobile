# -*- coding: utf-8 -*-

from kivy.properties import (ObjectProperty, ListProperty, NumericProperty, BooleanProperty)
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.datatables import MDDataTable
import asynckivy
from typing import (Any, Callable)
import re
from kivymd.uix.bottomsheet import MDCustomBottomSheet
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.button import Button
from kivymd.uix.toolbar import MDTopAppBar
import csv
from io import StringIO

####################################
#                                  #
# preamble to provide package name #
#                                  #
####################################

import sys
from pathlib import Path

if __name__ == '__main__' and __package__ is None:
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[2]
    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError:
        pass
    __package__ = '.'.join(parent.parts[len(top.parts):])

from .popup_save_dialog import SaveDialog
from ..backend import Client

###############
#             #
# definitions #
#             #
###############

class ExamResultModifyRequestContent(MDBoxLayout):
    """
    """
    grade_value = NumericProperty(0)
    credits_value = NumericProperty(0)
    data_table = ObjectProperty(0)

    def __init__(
        self, *,
        grade_value:int,
        credits_value:int,
        data_table:MDDataTable,
        **kwargs:tuple[str,Any]
    ):
        self.grade_value = grade_value
        self.credits_value = credits_value
        self.data_table = data_table
        super().__init__(**kwargs)

class ExamResults(MDDataTable):
    sreen = ObjectProperty(None)
    row_index = NumericProperty(0)
    # reference to opened bottom sheet instance
    bottom_sheet = ObjectProperty(None)
    # reference to asynchronous content loader
    # to cancel running coroutine if necessary
    asyncloader = ObjectProperty(None)

    def __init__(self, *, screen:MDScreen, **kwargs):
        self.screen = screen
        super().__init__(**kwargs)

    @property
    def get_grade_for_rating(self) -> Callable:
        return self.screen.get_grade_for_rating

    def on_row_press(self, instance_row:object):
        self.row_index = int(instance_row.index / self.table_data.total_col_headings)
        if self.row_index < len(self.table_data.row_data) - 1:
            grade_rating, credit = self.table_data.row_data[self.row_index][-3:-1]
            grade_rating_matches = re.match("(\d+\.\d+)\s?\((\d+\.\d+)%\)", grade_rating)
            self.bottom_sheet = MDCustomBottomSheet(
                screen=ExamResultModifyRequestContent(
                    grade_value=grade_rating_matches and int(float(grade_rating_matches.group(2))) or 0,
                    credits_value=int(re.sub('[^\d]', '', credit)),
                    data_table=self
                )
            )
            self.bottom_sheet.open()
    
    def apply_row(self, rating:float):
        old_data = self.table_data.row_data[self.row_index]
        new_data = tuple(old_data[:-4]) + (
            self.screen.get_status(
                "other" if rating == 0.0 else
                "failed" if rating < .5 else
                "passed"
            ),
            "{0:.1f} ({1:.2%})".format(self.screen.get_grade_for_rating(rating), rating),
        ) + tuple(old_data[-2:])
        async def update():
            await asynckivy.sleep(0)
            self.update_row(old_data, new_data)
            self.screen.remove_last_row()
            self.screen.calculate_last_row()
        if self.asyncloader != None and not self.asyncloader.done:
            self.asyncloader.cancel()
        self.asyncloader = asynckivy.start(update())

class GradeChecker(MDScreen):
    # reference to the "main" screen
    main_screen = ObjectProperty(None)
    # property storing the exam results as MDDataTable
    data_table = ObjectProperty(None)
    # list of exam results
    grades = ListProperty([])
    # reference to asynchronous content loader
    # to track the content loading routine
    asyncloader = ObjectProperty(None)

    def __init__(self, *, main_screen:MDScreen, **kwargs:dict[str,Any]):
        self.main_screen = main_screen
        self.prepare_data_table()
        super().__init__(**kwargs)
        self.ids.box_layout.add_widget(self.data_table)
        self.set_items()

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
    def use_cache(self, value:bool):
        self.main_screen.use_cache = value

    def prepare_data_table(self):
        self.grades = [
            (semester, record)
            for semester, records in self.client.get_grades(cached=self.use_cache).items()
            for record in sorted(
                records, 
                key=lambda x: (not x.get('Grade', 0) > 0, x.get('Module / Course', '')
                )
            )
        ]
        # get credits for open exam records
        self.client.get_booking_id()
        for subject in self.client.get_curricullum_entries(set(), set()).values():
            for module in subject["subjects"].values():
                for course in module['children'].values():
                    for _, record in self.grades:
                        if record['ID'] in course['label']:
                            record.update({"Credits": course['credits']})

        self.data_table = ExamResults(
            screen=self,
            rows_num = len(self.grades)+1,
            column_data=[
                ("Semester", dp(25)),
                ("Course", dp(45)),
                ( "Status", dp(25)),
                ("Grade", dp(30)),
                ("Credits", dp(15)),
                ("Attempt", dp(15))
            ]
        )

    def refresh(self, *args):

        def refresh_callback(interval):
            if self.asyncloader != None and not self.asyncloader.done:
                return
            
            self.data_table.clear_widgets()
            self.use_cache = False
            self.ids.box_layout.clear_widgets()
            self.prepare_data_table()
            self.ids.box_layout.add_widget(self.data_table)
            self.set_items()
            self.use_cache = True
            self.ids.refresh_layout.refresh_done() 
        
        Clock.schedule_once(refresh_callback, 1)

    def add_row(self, semester, record):
        status = record.get('Status', '').replace(', ', ',').split(',')
        self.data_table.add_row(
            (
                semester, 
                "{0} ({1})".format(
                    record.get('Module / Course', '').strip(),
                    record.get('ID').strip()
                ), 
                self.get_status("failed" if any((
                    'Failed' in status,
                    'Finally Not Passed' in status
                )) else "passed" if 'Passed' in status else "other"),
                f"{record.get('Grade'):.1f} ({record.get('Rating'):.2%})", 
                f"{record.get('Credits')} CP", 
                f"{record.get('Try')}/3"
            ) 
        )

    def get_status(self, status:str):
        return {
            "failed": ("alert-circle", [1, 0, 0, 1], "Failed"),
            "passed": (
                "checkbox-marked-circle",
                [40 / 256, 175 / 256, 100 / 256, 1],
                "Passed"
            )
        }.get(
            status,
            ("alert", [20 / 256, 20 / 256, 240/256, 1], 'Other')
        )

    def get_grade_for_rating(self, rating:float) -> float:
        if rating > 1: rating /= 100
        if rating >= .96: return 1.0
        elif rating >= .91: return 1.3
        elif rating >= .86: return 1.7
        elif rating >= .81: return 2.0
        elif rating >= .76: return 2.3
        elif rating >= .71: return 2.7
        elif rating >= .66: return 3.0
        elif rating >= .61: return 3.3
        elif rating >= .56: return 3.7
        elif rating >= .50: return 4.0
        else: return 5.0

    def remove_last_row(self):
        self.data_table.remove_row(self.data_table.table_data.row_data[-1])

    def calculate_last_row(self):
        credits, grades, ratings, trials = list(), list(), list(), list()
        for row in self.data_table.table_data.row_data:
            grade_rating, credit, trial = row[-3:]
            grade_rating_matches = re.match("(\d+\.\d+)\s?\((\d+\.\d+)%\)", grade_rating)
            if grade_rating_matches:
                grade, rating, trial, credit = (
                    *map(float, grade_rating_matches.groups()), 
                    int(re.sub('(?=[^\d]).*', '', trial)), 
                    int(re.sub('[^\d]', '', credit))
                )
                if grade * rating * credit > 0:
                    grades.append(grade * credit)
                    ratings.append(rating * credit)
                    credits.append(credit)
                if trial > 0:    
                    trials.append(trial)
        
        sum_credits = sum(credits)
        average_grade = sum_credits > 0 and sum(grades)/sum_credits or 0
        average_ratings = (sum_credits > 0 and sum(ratings)/sum_credits or 0)/100
        average_trials =len(trials) > 0 and sum(trials)/len(trials) or 0

        icon_type = "checkbox-marked-circle"
        if average_ratings >= .91:
            grade_text = "Very Good"
            color = (40 / 256, 175 / 256, 100 / 256, 1)
        elif average_ratings >= .76:
            grade_text = "Good"
            color = (80 / 256, 135 / 256, 80 / 256, 1)
        elif average_ratings >= .61:
            grade_text = "Satisfactory"
            color = (120 / 256, 95 / 256, 60 / 256, 1)
        elif average_ratings >= .5:
            grade_text = "Sufficient"
            color = (160 / 256, 55 / 256, 40 / 256, 1)
        else:
            grade_text = "Insufficient"
            icon_type = "alert"
            color = (200 / 256, 15 / 256, 20 / 256, 1)

        self.data_table.add_row(
            (
                "[color=#{0:02X}{1:02X}{2:02X}][b][u]Total[/u][/b][/color]".format(*map(lambda x: int(x*256), color[:-1])), 
                "", 
                (icon_type, color, grade_text),
                f"{average_grade:.2f} ({average_ratings:.2%})", 
                f"{sum_credits} CP", 
                f"{average_trials:.0f}/3"
            ) 
        )

    def set_items(self):
        async def set_items():
            credits, grades, ratings, trials = list(), list(), list(), list()
            for semester, record in self.grades:
                await asynckivy.sleep(0)
                self.add_row(semester, record)
    
            self.calculate_last_row()
            self.main_screen.grades_btn.right_text = f"({len(list(filter(lambda x: x[1].get('Grade'), self.grades)))})"

        self.asyncloader = asynckivy.start(set_items())

    def on_enter(self, *args):
        self.main_screen.ids.top_bar.title = "Exam results"
        # list of temporary top panel entries
        self.to_remove = [
            ['file-export-outline', self.export, 'Export data', 'Export data'],
        ]
        # extend top bar of "main" screen
        for item in self.to_remove:
            if item not in self.top_bar.right_action_items:
                self.top_bar.right_action_items.insert(0, item)
        return super().on_enter(*args)   

    def on_leave(self, *args):
        """
        Called when leaving the screen.

        Positional arguments:
            *args: tuple[Any],
                arguments forwarded to kivymd.uix.screen.MDScreen.on_leave method.
        """

        # remove temporary top panel entries
        for item in self.to_remove:
            self.top_bar.right_action_items.remove(item)
        return super().on_leave(*args)

    def export(self, bound_instance:Button):
        bound_instance.disabled = True
        content = StringIO()
        writer = csv.writer(content, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(["Semester", "Course", "Status", "Grade", "Credits", "Attempt"])
        writer.writerows(
            list(
                map(
                    lambda x: list(
                        map(
                            lambda y: re.sub(
                                '\[.*?\]', '', 
                                str(isinstance(y, (list, tuple)) and y[-1] or y)
                            ), 
                            x
                        )
                    ), 
                    self.data_table.table_data.row_data
                )
            )
        )
        # dispatch save dialog to get location to save the target file
        spopup = SaveDialog(
            content_disposition="exam_results.csv", 
            save_method=lambda file, path: self.client.save(file, content.getvalue(), Path(path)),
            banner=self.ids.banner
        )
        spopup.open()
        bound_instance.disabled = False

