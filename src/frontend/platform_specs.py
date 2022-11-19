# -*- coding: utf-8 -*-

import webbrowser

from kivy.utils import platform
from plyer import email, notification, storagepath

if platform == "android":
    from android.permissions import Permission, request_permissions

    request_permissions(
        [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
    )

# application directory
app_dir_path = str(storagepath.get_application_dir())

# download directory
download_dir_path = str(storagepath.get_downloads_dir())


def notify(
    title: str, message: str, ticker: str, toast: bool = False, **kwargs: dict[str, str]
):
    """
    Function to be used on Android to dispatch a notification into notification banner.

    Keyword arguments:
        title: str,
            title of the notification.

        message: str,
            content of the notification.

        ticker: str,
            content of a ticker notification.

        toast: bool, optional, default is False,
            dispatch notification as toast.

        **kwargs: dict[str,str]
            optional arguments including 'app_icon' and 'app_name'.
    """

    nwargs = {"title": title, "message": message, "ticker": ticker, "toast": toast}
    if not kwargs.get("app_icon") is None:
        nwargs["app_icon"] = kwargs["app_icon"]
    if not kwargs.get("app_name") is None:
        nwargs["app_icon"] = kwargs["app_name"]
    notification.notify(**nwargs)


def send_email(recipient: str):
    """
    Creates e-mail object in the default e-mail client.

    Positional arguments:
        recipient: str,
            e-mail address of the recipient.
    """
    email.send(recipient=recipient, subject="", text="", create_chooser=True)


def open(filename: str, datatype: str = "application/pdf"):
    """
    Dispatches default action associated with given datatype.

    Positional arguments:
        filename: str,
            name of the file to perfomrm default action with.

        datatype: str,
            MIME description of the file content.
    """
    try:
        from jnius import autoclass, cast

        PythonActivity = autoclass(
            "org.renpy.android.PythonActivity"
        )  # request the Kivy activity instance
        Intent = autoclass("android.content.Intent")
        String = autoclass("java.lang.String")
        Uri = autoclass("android.net.Uri")
        # fileNameJava = cast('java.lang.CharSequence', String(filename))
        File = autoclass("java.io.File")
        target = Intent()
        target.setAction(Intent.ACTION_VIEW)
        urifromfile = Uri.fromFile(File(filename))
        target.setDataAndType(urifromfile, datatype)  # setData(urifromfile)#
        target.setFlags(Intent.FLAG_ACTIVITY_NO_HISTORY)
        target = Intent.createChooser(
            target, cast("java.lang.CharSequence", String("Open file with:"))
        )
        currentActivity = cast("android.app.Activity", PythonActivity.mActivity)
        currentActivity.startActivity(target)
    except BaseException:
        webbrowser.open_new(filename)
