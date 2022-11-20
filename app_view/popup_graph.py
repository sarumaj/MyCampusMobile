# -*- coding: utf-8 -*-

import traceback
from io import BytesIO
from pathlib import Path
from typing import Any

import networkx as nx
from kivy.core.image import Image as CoreImage
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivymd.uix.banner import MDBanner
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen

from .popup_save_dialog import SaveDialog

Builder.load_string(
    r"""
#:kivy 2.1.0

<GraphContent>:
    orientation: "vertical"
    padding: "20dp"
    size_hint: (1, None)
    height: Window.height * .8
    spacing: dp(10)
    
    MDScrollView:
        size_hint: (1, 1)
        do_scroll_x: True
        do_scroll_y: True
        do_scale: True

        BoxLayout:
            orientation: 'vertical'
            size_hint: (None,None)
            size: (image.size[0] * scatter.scale, image.size[1] * scatter.scale)

            Scatter:
                id: scatter
                scale_min: .01
                scale_max: 3.
                do_rotation: False
                do_translation_x: False
                do_translation_y: False

                Image:
                    id: image
                    texture: root.core_image.texture
                    allow_stretch: True
                    keep_ratio: True
                    size_hint: (None, None)
                    width: root.width - dp(30)
                    height: self.width / self.texture_size[0] * self.texture_size[1]

    MDFloatLayout:
        size_hint: (1, None)
        height: 0

        MDIconButton:
            icon: "download-outline"
            theme_text_color: "Custom"
            text_color: app.theme_cls.primary_color
            pos_hint: {'right': 1, 'top': 0}
            on_release:
                root.dialog.download()

    MDRectangleFlatButton:
        text: "Close"
        theme_text_color: "Custom"
        text_color: app.theme_cls.primary_color
        pos_hint: {"center_x": .5}
        on_release:
            root.dialog.dismiss()

<GraphDialog>:
    size_hint: (.8, None)
    auto_dismiss: False
    type: "custom"
    radius: (20, 7, 20, 7)
"""
)

###############
#             #
# definitions #
#             #
###############


class GraphContent(MDBoxLayout):
    """
    Content of the graph view dialog.
    """

    # reference to the dialog
    dialog = ObjectProperty(None)
    # place holder for kivy.core.Image
    core_image = ObjectProperty(None)

    def __init__(
        self, *, dialog: MDDialog, core_image: CoreImage, **kwargs: dict[str, Any]
    ):
        """
        Constructor.

        Key word arguments:
            dialog: kivymd.uix.dialog.MDDialog,
                reference to the implementing dialog instance.

            core_image: kivy.core.Image,
                image instance created from bytes in memory.

            **kwargs: dict[str,Any],
                keyword arguments passed to the kivymd.uix.boxlayout.MDBoxLayout class.
        """

        self.dialog = dialog
        self.core_image = core_image
        super().__init__(**kwargs)


class GraphDialog(MDDialog):
    """
    Dialog widget displaying dependencies between curriculum entries.
    """

    # reference to the screen instance
    screen = ObjectProperty(None)

    def __init__(self, *, graph: nx.Graph, screen: MDScreen, **kwargs: dict[str, Any]):
        """
        Initializes graph dialog.

        Keyword arguments:
            graph: networkx.Graph,
                Graph instance.

            screen: MDScreen,
                reference to the screen instance.

            **kwargs: dict[str,Any],
                keyword arguments of the parent class.

        """

        self.screen = screen
        try:
            import matplotlib.pyplot as plt

            plt.figure(figsize=tuple([int(len(graph.edges) / 2)] * 2))
            plt.axis("off")
            # use triangular layout
            pos = nx.planar_layout(graph, scale=len(graph.edges), dim=2)
            nx.draw_networkx_labels(graph, pos, clip_on=False, font_size=9)
            nx.draw_networkx_nodes(
                graph,
                pos,
                node_size=[200 * d.get("weight", 1) for _, d in graph.nodes(data=True)],
                alpha=0.5,
                node_color="green",
            )
            nx.draw_networkx_edges(
                graph,
                pos,
                width=[d.get("weight", 1) for _, _, d in graph.edges(data=True)],
                alpha=0.4,
                edge_color="green",
                arrowstyle="-|>",
            )

            buffer = BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format="png", dpi=200)
            try:
                core = CoreImage(buffer, ext="png", filename="dependency.png")
                self.content_cls = GraphContent(
                    dialog=self,
                    core_image=core,
                )
            except BaseException:
                self.screen.client.debug(buffer.getvalue())
                self.screen.client.warning(traceback.format_exc())
                raise
        except BaseException:
            pass
        super().__init__(**kwargs)

    @property
    def banner(self) -> MDBanner:
        return self.screen.ids.banner

    def download(self):
        """
        Dumps graph image into a local file.
        """
        spopup = SaveDialog(
            content_disposition="dependency_graph.png",
            save_method=lambda file, path: (
                self.content_cls.core_image.save(str(Path(path) / file)),
                str(Path(path) / file),
            )[1],
            banner=self.banner,
        )
        self.dismiss()
        spopup.open()
