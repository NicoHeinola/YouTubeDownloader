from Download import Video
from Interface import Interface
from typing import List
import pytube
from threading import Thread


class Main:
    def __init__(self):
        self._interface: Interface = Interface()

        # Download related
        self._downloadedLatest: bool = False  # Used to determine if link was changed so it downloads two separate files

        # Download options
        self._videos: List[Video] = []
        self._videoItag: str = ""
        self._audioItag: str = ""

        # Interface setup
        self._interface.setLoadVideoInfoFunc(self._loadURL)
        self._interface.setDownloadFunc(self._download)
        self._interface.setOnVideoChange(self._onVideoResolutionChange)
        self._interface.setOnAudioChange(self._onAudioQualityChange)
        self._interface.setOnFolderChangeFunc(self._onFolderChange)

    def _getLatestVideo(self):
        """
        When user starts downloading video, the previous videos in this list should NEVER be modified afterwards, but they have to be saved
        This is a quick fix to that
        :return: The latest video
        """
        return self._videos[len(self._videos) - 1]

    def _onVideoCombined(self, index):
        self._interface.modifyDownloadText(index, "Yes")

    def _onFolderChange(self, folder: str):
        video = self._getLatestVideo()
        video.setOutputFolderPath(folder)

    def _onVideoResolutionChange(self, res: str):
        video = self._getLatestVideo()
        self._videoItag = video.getVideoOptions().filter(resolution=res)[0].itag

    def _onAudioQualityChange(self, quality: str):
        video = self._getLatestVideo()
        self._audioItag = video.getAudioOptions().filter(abr=quality)[0].itag

    def _download(self):

        if self._downloadedLatest:
            video = self._getLatestVideo()
        else:
            video = self._getLatestVideo().__deepcopy__()
            video.setInterfaceIndex(video.getInterfaceIndex() + 1)

        index = self._interface.addNewDownloadToList(video.getVideoTitle())
        video.setInterfaceIndex(index)
        Thread(target=lambda: video.downloadAndCombineVideo(self._videoItag, self._audioItag)).start()
        self._downloadedLatest = False

    def _loadURL(self, url: str):
        Thread(target=lambda: self._loadThread(url)).start()

    def _loadThread(self, url):
        video = Video(url)

        self._videos.append(video)
        self._downloadedLatest = True

        video.setOnVideoCombinedFunc(self._onVideoCombined)
        video.fetchOptions()
        videoOptions: pytube.StreamQuery[pytube.Stream] = video.getVideoOptions().order_by("resolution").desc().filter(progressive=False)
        audioOptions: pytube.StreamQuery[pytube.Stream] = video.getAudioOptions()

        resolutionList: List[str] = []
        audioList: List[str] = []
        for stream in videoOptions:
            res: str = stream.resolution
            if res not in resolutionList:
                resolutionList.append(stream.resolution)

        for stream in audioOptions:
            abr: str = stream.abr
            if abr not in audioList:
                audioList.append(stream.abr)

        self._interface.addQualityOptions(resolutionList, audioList)

    def start(self):
        self._interface.mainLoop()


if __name__ == '__main__':
    main = Main()
    main.start()
