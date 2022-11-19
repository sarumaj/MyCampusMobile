# -*- coding: utf-8 -*-

import traceback
from io import BytesIO
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import networkx as nx
from kivy.core.image import Image as CoreImage
from kivy.properties import ObjectProperty
from kivymd.uix.banner import MDBanner
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen

from .popup_save_dialog import SaveDialog

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
