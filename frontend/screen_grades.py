# -*- coding: utf-8 -*-

from kivy.properties import (ObjectProperty, StringProperty, NumericProperty, BooleanProperty, ListProperty)
from kivy.metrics import (sp, dp)
from kivy.core.window import Window
from kivy.clock import Clock
from dateutil.parser import parse
from kivy.uix.label import Label
from kivymd.uix.screen import MDScreen
from kivymd.uix.datatables import MDDataTable
from datetime import date
import asynckivy
import re

class RowHead(Label):
    pass

class RowRecord(Label):
    pass

class ExamResults(MDDataTable):
    pass


class GradeChecker(MDScreen):
    main_screen = ObjectProperty(None)
    data_table = ObjectProperty(None)
    grades = ListProperty([])

    def __init__(self, *, main_screen:MDScreen, **kwargs:dict[str,Any]):
        self.main_screen = main_screen
        self.prepare_data_table()
        super().__init__(**kwargs)
        self.ids.box_layout.add_widget(self.data_table)
        self.set_items()

    def prepare_data_table(self):
        self.grades = [
            (semester, record)
            for semester, records in self.master.manager.client.get_grades(cached=self.master.use_cache).items()
            for record in sorted(
                records, 
                key=lambda x: (semester, parse(x.get('Date', '01.01.1970'), dayfirst=True, yearfirst=False))
            )
        ]
        self.data_table = ExamResults(
            rows_num = len(self.grades)+1,
            column_data=[
                ("Semester", dp(30)),
                ("Course / Module", dp(45)),
                ( "Status", dp(20)),
                ("Grade", dp(30)),
                ("Credits", dp(15)),
                ("Try", dp(10))
            ]
        )

    def refresh(self, *args):
        
        def refresh(interval):
            self.data_table.clear_widgets()
            self.master.use_cache = False
            self.ids.box_layout.clear_widgets()
            self.prepare_data_table()
            self.ids.box_layout.add_widget(self.data_table)
            self.set_items()
            self.master.use_cache = True
            self.ids.refresh_layout.refresh_done()

        Clock.schedule_once(refresh, 1)

    def set_items(self):
        async def set_items():
            credits, grades, ratings, trials = list(), list(), list(), list()
            for semester, record in self.grades:
                await asynckivy.sleep(0)
                credits.append(record.get('Credits'))
                grades.append(record.get('Grade'))
                ratings.append(record.get('Rating'))
                trials.append(record.get('Try'))
                status = record.get('Status', '').replace(', ', ',').split(',')
                self.data_table.add_row(
                    (
                        semester, 
                        "{0}\n({1})".format(
                            record.get('Module / Course', '').replace(': ', ':\n'),
                            record.get('ID')
                        ), 
                        (
                            ("alert-circle", [1, 0, 0, 1], "Failed") if 'Failed' in status else
                            (
                                "checkbox-marked-circle",
                                [40 / 256, 175 / 256, 100 / 256, 1],
                                "Passed"
                            ) if 'Passed' in status else
                            ("alert", [20 / 256, 20 / 256, 240/256, 1], "Unknown")
                        ),
                        f"{record.get('Grade'):.1f} ({record.get('Rating'):.2%})", 
                        f"{record.get('Credits')} CP", 
                        f"{record.get('Try')}/3"
                    ) 
                )
            average_grade = len(grades) > 0 and sum(grades)/len(grades) or 0
            average_ratings = (len(ratings) > 0 and sum(ratings)/len(ratings) or 0)/100
            sum_credits = sum(credits)
            average_trials =len(trials) > 0 and sum(trials)/len(trials) or 0

            icon_type = "checkbox-marked-circle"
            if average_grade <= 1.5:
                grade_text = "Very Good"
                color = (40 / 256, 175 / 256, 100 / 256, 1)
            elif average_grade <= 2.5:
                grade_text = "Good"
                color = (80 / 256, 135 / 256, 80 / 256, 1)
            elif average_grade <= 3.5:
                grade_text = "Satisfying"
                color = (120 / 256, 95 / 256, 60 / 256, 1)
            elif average_grade <= 4.0:
                grade_text = "Sufficient"
                color = (160 / 256, 55 / 256, 40 / 256, 1)
            elif average_grade <= 5.0:
                grade_text = "Deficient"
                icon_type = "alert"
                color = (200 / 256, 15 / 256, 20 / 256, 1)
            else:
                grade_text = "Insufficient"
                icon_type = "alert"
                color = (240 / 256, 0, 0, 1)

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

            self.master.grades_btn.right_text = f"({len(self.grades)})"
        asynckivy.start(set_items())

    def on_enter(self, *args):
        self.master.ids.top_bar.title = "Exam results"
        return super().on_enter(*args)   