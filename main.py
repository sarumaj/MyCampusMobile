# -*- coding: utf-8 -*-


__version__ = "1.0.2b"


def main():
    import os
    from pathlib import Path

    import certifi
    from kivy.utils import platform

    os.environ["KIVY_IMAGE"] = "pil,sdl2"
    os.environ["SSL_CERT_FILE"] = certifi.where()

    if platform != "android":
        from kivy.core.window import Window

        Window.size = (720, 1440)
        Window.minimum_height = 1000
        Window.minimum_width = 600
    else:
        from android.permissions import Permission, request_permissions

        request_permissions(
            [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
        )
    from app_controller.client import Client
    from app_view.app import MobileApp
    from app_view.platform_specs import app_dir_path

    app = MobileApp(
        Client(
            "",
            "",
            max_len=100,
            max_age=60**2,
            filepath=__file__,
            verbose=True,
            destination=str(Path(app_dir_path) / ".cache.dat"),
        )
    )
    app.run()


if __name__ == "__main__":
    main()
