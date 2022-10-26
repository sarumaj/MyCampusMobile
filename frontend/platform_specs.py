# -*- coding: utf-8 -*-

import webbrowser
from plyer import (
    storagepath, 
    notification, 
    email
)

app_dir_path = str(storagepath.get_application_dir())

download_dir_path = str(storagepath.get_downloads_dir())

def notify(title:str, message:str, ticker:str, toast:bool=False, **kwargs):
    nwargs = {'title': title, 'message': message, 'ticker': ticker, 'toast': toast}
    if kwargs.get('app_icon') != None:
        nwargs['app_icon'] = kwargs['app_icon']
    if kwargs.get('app_name') != None:
        nwargs['app_icon'] = kwargs['app_name']
    notification.notify(**nwargs)

def send_email(recipient:str):
    email.send(
        recipient=recipient, 
        subject="", 
        text="",
        create_chooser=True
    )

def open(filename:str, datatype:str="application/pdf"):
    try:
        from jnius import autoclass, cast
        PythonActivity = autoclass('org.renpy.android.PythonActivity')  #request the Kivy activity instance
        Intent = autoclass('android.content.Intent')
        String = autoclass('java.lang.String') 
        Uri = autoclass('android.net.Uri')
        #fileNameJava = cast('java.lang.CharSequence', String(filename))
        File = autoclass('java.io.File')
        target = Intent()
        target.setAction(Intent.ACTION_VIEW)
        urifromfile = Uri.fromFile(File(filename))
        target.setDataAndType(urifromfile, datatype) #setData(urifromfile)#
        target.setFlags(Intent.FLAG_ACTIVITY_NO_HISTORY)
        target = Intent.createChooser(target, cast(
            'java.lang.CharSequence',
            String('Open file with:')
        ))
        currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
        currentActivity.startActivity(target)
    except:
        webbrowser.open_new(filename)