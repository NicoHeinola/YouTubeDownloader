import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from typing import List
from tkinter import filedialog
import os
import pytube


class Themes:
    class THEME_PATHS:
        THEME_FOLDER = "./themes"
        AZURE = "azure/azure.tcl"

    class THEME_NAMES:
        AZURE_DARK = "dark"
        AZURE_LIGHT = "light"

    @staticmethod
    def setTheme(_tk: tk.Tk, themePath: str, themeName: str):
        _tk.call("source", os.path.join(Themes.THEME_PATHS.THEME_FOLDER, themePath))
        _tk.call("set_theme", themeName)


class DownloadsWidget(ttk.Frame):
    def __init__(self, master, **kwargs):
        super(DownloadsWidget, self).__init__(master, **kwargs)

        # self._titles: List[str] = []  # Used to only change done row and not title

        self._downloadListScroll = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self._downloadList = ttk.Treeview(self, selectmode="browse", columns=0, height=10, yscrollcommand=self._downloadListScroll.set)
        self._downloadList.column("#0", anchor="w")
        self._downloadList.column(0, anchor="w", width=80)
        self._downloadList.heading("#0", text="Video title", anchor="center")
        self._downloadList.heading(0, text="Done", anchor="center")
        self._downloadList.pack(pady=0, padx=0, side=tk.LEFT, fill=tk.Y, expand=True)
        self._downloadListScroll.pack(side=tk.RIGHT, fill=tk.Y, expand=True)

    def addDownload(self, title: str, done: str) -> int:
        """
        Adds a column to the download list
        :param title: First row
        :param done: Second row
        :return:
        """
        self._downloadList.insert("", tk.END, None, text=title, values=done)
        return len(self._downloadList.get_children()) - 1

    def setDoneText(self, index: int, text: str):
        item = self._downloadList.get_children()[index]
        self._downloadList.item(item, values=text)


class LabelEntry(ttk.Frame):
    def __init__(self, master: ttk.Widget, text: str, **kwargs):
        super(LabelEntry, self).__init__(master)

        self._label = ttk.Label(self, text=text)
        self._entry = ttk.Entry(self, textvariable=kwargs.get("textvariable", None), state=kwargs.get("state", tk.NORMAL))

        self._label.pack(side=tk.TOP, padx=(0, 20), anchor=tk.W)
        self._entry.pack(side=tk.TOP)

    def getEntryValue(self) -> str:
        return self._entry.get()

    def setEntryText(self, text: str):
        self._entry.delete(0, tk.END)
        self._entry.insert(0, text)


class LabelSelect(ttk.Frame):
    def __init__(self, master: ttk.Widget, text: str, **kwargs):
        super(LabelSelect, self).__init__(master, **kwargs)

        self._label = ttk.Label(self, text=text)
        self._select = ttk.Combobox(self, state="readonly")

        self._label.pack(side=tk.TOP, padx=(0, 20), anchor=tk.W)
        self._select.pack(side=tk.TOP)

    def valueCount(self) -> int:
        return len(self._select["values"])

    def setSelectedValue(self, index: int):
        self._select.current(index)

    def getSelectedOptions(self) -> str:
        return self._select.get()

    def addOption(self, name: str):
        values = list(self._select["values"])
        values.append(name)
        self._select["values"] = values

    def removeOptionByIndex(self, index: int):
        values = list(self._select["values"])
        values.pop(index)
        self._select["values"] = values

    def removeOptionByName(self, name: str):
        values = list(self._select["values"])
        values.remove(name)
        self._select["values"] = values

    def removeAllOptions(self):
        self._select["values"] = ()

    def getCombobox(self) -> ttk.Combobox:
        return self._select


class ChooseFolder(ttk.Frame):
    def __init__(self, master, **kwargs):
        super(ChooseFolder, self).__init__(master, **kwargs)
        self._folderPath: str = ""
        self._folderPathVar = tk.StringVar(self, value="")

        self._onFolderChangeFunc = lambda folder: None

        self._folderFrame = ttk.Frame(self)
        self._folder = LabelEntry(self._folderFrame, "Folder Path", textvariable=self._folderPathVar, state='disabled')

        self._folderFrame.pack(side=tk.LEFT, padx=(0, 10))
        self._folder.pack(side=tk.LEFT)

        self._button = ttk.Button(self, text="Choose folder", style="", command=self._onFolderSelect)
        self._button.pack(side=tk.LEFT, anchor=tk.S)

    def _onFolderSelect(self):
        folder: str = filedialog.askdirectory()
        if folder is not "" and type(folder) == str:
            self._folderPath = folder
            self._folderPathVar.set(folder)
            self._onFolderChangeFunc(folder)

    def setFolderPath(self, path: str):
        self._folderPath = path
        self._folderPathVar.set(path)

    def getFolderPath(self) -> str:
        return self._folderPath

    def setOnFolderChangeFunc(self, func):
        self._onFolderChangeFunc = func

    def getButton(self) -> ttk.Button:
        return self._button


class VideoDownloadFrame(ttk.Labelframe):
    def __init__(self, master, **kwargs):
        super(VideoDownloadFrame, self).__init__(master, **kwargs)

        self._frame = ttk.Frame(self)
        self._frame.pack(padx=20, pady=20)

        # Url
        self._urlFrame = ttk.Frame(self._frame)
        self._url = LabelEntry(self._urlFrame, "Video URL*")
        self._fetchInfo = ttk.Button(self._urlFrame, text="Load", style="Accent.TButton", width=5)

        self._urlFrame.pack(anchor=tk.W)
        self._url.pack(side=tk.LEFT)
        self._fetchInfo.pack(side=tk.LEFT, padx=(10, 0), anchor=tk.S)

        # Folder
        self._folderFrame = ttk.Frame(self._frame)
        self._folderWidget = ChooseFolder(self._folderFrame)
        self._folderFrame.pack(pady=15, anchor=tk.W)
        self._folderWidget.pack(anchor=tk.W)

        # Download

        self._downloadButton = ttk.Button(self._frame, text="Download", style="Accent.TButton", width=40)
        self._downloadButton.pack(pady=15)

    def setOnFolderChange(self, func):
        self._folderWidget.setOnFolderChangeFunc(func)

    def setDownloadFunc(self, func):
        self._downloadButton["command"] = func

    def setLoadInfoFunc(self, func):
        self._fetchInfo["command"] = lambda: func(self._url.getEntryValue())


class VideoOptionsFrame(ttk.LabelFrame):
    def __init__(self, master, **kwargs):
        super(VideoOptionsFrame, self).__init__(master, **kwargs)

        self._frame = ttk.Frame(self)
        self._frame.pack(padx=20, pady=20)

        self._onVideoChangeFunc = lambda e: None
        self._onAudioChangeFunc = lambda e: None

        self._videoQualityWidget = LabelSelect(self._frame, text="Video Quality*")
        self._audioQualityWidget = LabelSelect(self._frame, text="Audio Quality*")

        self._videoQualityWidget.pack()
        self._audioQualityWidget.pack(pady=15)

    def onVideoChange(self, func):
        self._onVideoChangeFunc = func
        self._videoQualityWidget.getCombobox().bind("<<ComboboxSelected>>", lambda e: func(self._videoQualityWidget.getSelectedOptions()))

    def onAudioChange(self, func):
        self._onAudioChangeFunc = func
        self._audioQualityWidget.getCombobox().bind("<<ComboboxSelected>>", lambda e: func(self._audioQualityWidget.getSelectedOptions()))

    def addVideoQuality(self, quality: str):
        self._videoQualityWidget.addOption(quality)

    def addAudioQuality(self, quality: str):
        self._audioQualityWidget.addOption(quality)

    def resetQualities(self):
        self._videoQualityWidget.removeAllOptions()
        self._audioQualityWidget.removeAllOptions()

    def selectFirstQuality(self):
        self._videoQualityWidget.setSelectedValue(0)
        self._audioQualityWidget.setSelectedValue(0)
        self._onVideoChangeFunc(self._videoQualityWidget.getSelectedOptions())
        self._onAudioChangeFunc(self._audioQualityWidget.getSelectedOptions())


class Interface:

    def __init__(self):
        self._tk = tk.Tk()
        self._tk.title("YouTube Video Downloader")
        self._tk.iconbitmap(os.path.join("images", "icon.ico"))
        self._tk.resizable(False, False)

        # Style & Theme
        Themes.setTheme(self._tk, Themes.THEME_PATHS.AZURE, Themes.THEME_NAMES.AZURE_DARK)
        # style = ttk.Style(self._tk)

        # Widgets
        self._mainFrame = ttk.Frame(self._tk)
        self._mainFrame.pack(anchor=tk.CENTER, pady=50, padx=50)

        self._rightFrame = ttk.Frame(self._mainFrame)
        self._leftFrame = ttk.Frame(self._mainFrame)
        self._leftFrame.pack(side=tk.LEFT, anchor=tk.N, padx=(0, 20), fill=tk.Y, expand=True)
        self._rightFrame.pack(side=tk.LEFT, anchor=tk.N, padx=(20, 0))

        self._downloadsWidget = DownloadsWidget(self._leftFrame)
        self._downloadsWidget.pack(fill=tk.Y, expand=True)

        # Video download frame
        self._videoDownloadFrame = VideoDownloadFrame(self._rightFrame, text="Basic Info")
        self._setFrameWidth(self._videoDownloadFrame, 400)
        self._videoDownloadFrame.pack()

        # Video options frame
        self._videoOptionsFrame = VideoOptionsFrame(self._rightFrame, text="Video Options")
        self._setFrameWidth(self._videoOptionsFrame, 400)
        self._videoOptionsFrame.pack(pady=(20, 0))

        # self._downloadList.insert(parent="", index="end", iid=None, text="text", values=("No"))

    @staticmethod
    def _setFrameWidth(frame: ttk.Frame, width: int):
        frame.update()
        height = frame.winfo_reqheight()
        frame.propagate(0)
        frame["height"] = height
        frame["width"] = width

    def addQualityOptions(self, video: List[str], audio: List[str]):
        self._videoOptionsFrame.resetQualities()

        for option in video:
            self._videoOptionsFrame.addVideoQuality(option)

        for option in audio:
            self._videoOptionsFrame.addAudioQuality(option)

        self._videoOptionsFrame.selectFirstQuality()

    def addNewDownloadToList(self, title: str, done: str = "No") -> int:
        """
        Adds a new column to the download list and returns it's index
        :param title: Title of the column
        :param done: Basically a text (usually saying no or yes)
        :return: index
        """
        return self._downloadsWidget.addDownload(title, done)

    def modifyDownloadText(self, index: int, done: str):
        self._downloadsWidget.setDoneText(index, done)

    def setOnFolderChangeFunc(self, func):
        self._videoDownloadFrame.setOnFolderChange(func)

    def setOnVideoChange(self, func):
        self._videoOptionsFrame.onVideoChange(func)

    def setOnAudioChange(self, func):
        self._videoOptionsFrame.onAudioChange(func)

    def setDownloadFunc(self, func):
        self._videoDownloadFrame.setDownloadFunc(func)

    def setLoadVideoInfoFunc(self, func):
        self._videoDownloadFrame.setLoadInfoFunc(func)

    @staticmethod
    def _fromRGB(r: int, g: int, b: int):
        return f'#{r:02x}{g:02x}{b:02x}'

    def mainLoop(self):
        self._tk.mainloop()


class ErrorHandling:
    @staticmethod
    def ShowError(title: str, error: str):
        messagebox.showerror(title, message=error)
