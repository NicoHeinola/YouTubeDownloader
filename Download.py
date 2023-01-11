import os
import time
from typing import List

import pytube
import requests
from pytube import YouTube

import subprocess

from pytube.exceptions import RegexMatchError


def cleanFilename(s: str):
    """
    Makes a name compatible with filenames
    :param s: the name
    :return: compatible name
    """
    # Checks that s is valid
    if not s:
        return ''
    badChars = '\\/:*?\"<>|'  # These characters will be removed from the name
    # Loops through each bad character and removes that specific character from name
    for c in badChars:
        s = s.replace(c, '')
    return s


class Video:
    videos: List = []  # Unused for now

    def __init__(self, link: str):
        Video.videos.append(self)

        self._link: str = link  # Link to a YouTube video

        # Contains information about downloadable files such as resolution and fps
        # This program downloads one of those options by Itag
        self._videoOptions: pytube.query.StreamQuery = None
        self._audioOptions: pytube.query.StreamQuery = None

        # The streams from which the video is downloaded from
        self._videoStream: pytube.query.Stream = None
        self._audioStream: pytube.query.Stream = None

        # How the program views and saves ongoing downloads
        # It saves temporary video with given name and a number so it can combine a video with correct sound
        self._videoNameFormat: str = "tempvideo."
        self._audioNameFormat: str = "tempaudio."

        self._tempVideoFolder: str = "tempvideos"
        self._outputFolder: str = "downloads"

        # Used for combining video and audio
        self._ffmpegPath = os.getcwd() + "\\" + r"ffmpeg\bin\ffmpeg.exe"

        # Interface related
        self._onVideoCombinedFunc = lambda index: print(index)  # Called when downloaded video is combined (aka. ready)
        self._interfaceIndex: int = None  # Used to update its "done" portion on the interface when download is ready

    def __deepcopy__(self):
        newVideo = Video(self._link)
        newVideo.setOnVideoCombinedFunc(self._onVideoCombinedFunc)
        newVideo.setInterfaceIndex(self._interfaceIndex)
        newVideo.setOutputFolderPath(self._outputFolder)
        newVideo._videoOptions = self._videoOptions
        newVideo._audioOptions = self._audioOptions

        return newVideo

    def setInterfaceIndex(self, index: int):
        self._interfaceIndex = index

    def getInterfaceIndex(self) -> int:
        return self._interfaceIndex

    def setOnVideoCombinedFunc(self, func):
        self._onVideoCombinedFunc = func

    def setOutputFolderPath(self, folder: str):
        self._outputFolder = folder

    def setLink(self, link: str):
        """
        Sets link to a YouTube video
        :param link: the link to a video
        """
        self._link = link

    def getLink(self) -> str:
        """
        Returns the link to a YouTube video
        :return: link
        """
        return self._link

    def getVideoOptions(self) -> pytube.StreamQuery:
        """
        Returns a list of video options which can be downloaded
        :return: list of video options
        """
        return self._videoOptions

    def getAudioOptions(self) -> pytube.StreamQuery:
        """
        Returns a list of audio options which can be downloaded
        :return: a list of audio options
        """
        return self._audioOptions

    def _getNextVideoNums(self) -> List[int]:
        """
        Returns the next valid number which the program can name temporary audio and video.
        This is used to not overwrite ongoing downloads
        :return: a valid audio and video number
        """

        nums: List[int] = [1, 1]  # Contains the valid video and audio number

        # Makes sure the folder in which the temporary videos are stored exists
        if not os.path.exists(self._tempVideoFolder):
            os.mkdir(self._tempVideoFolder)
            return nums

        files = os.listdir(self._tempVideoFolder)  # List of ongoing downloads
        for file in files:
            filename: str = os.path.splitext(file)[0]  # Gets the filename of a download
            if filename.count(".") > 0:  # Makes sure file is properly named
                try:
                    num: int = int(os.path.splitext(filename)[1][1:])  # Tries to get the integer from file
                except ValueError:
                    # Fails if file is not an ongoing video or if the file is incorrectly named
                    continue

                # Checks if file is a video or audio
                if filename.find(self._videoNameFormat, 0):
                    if nums[0] > num:
                        continue
                    nums[0] = num + 1
                elif filename.find(self._audioNameFormat, 0):
                    if nums[1] > num:
                        continue
                    nums[1] = num + 1

        return nums

    def _removeTempFile(self, fileName: str, wait: int = 1):
        """
        Removes a temporary file used in combining audio and video.
        Loops until the file is not used by the combiner anymore.
        :param fileName: Name of the video / audio file
        :param wait: how long until it tries again if there's a permission error
        """
        filePath: str = os.path.join(self._tempVideoFolder, fileName)  # Creates the path to file using temporary folder path and filename
        # Loops until it can properly delete the file
        while os.path.exists(filePath):
            try:
                os.remove(filePath)
            except PermissionError:
                pass
            time.sleep(wait)

    def getVideoTitle(self) -> str:
        """
        Returns the title of the video
        :return: title
        """
        return self._videoOptions.get_highest_resolution().title

    def _generateSafeFilename(self, outputName) -> str:
        listOfDownloads: List[str] = os.listdir(self._outputFolder)
        withoutExtensions: List[str] = []
        for file in listOfDownloads:
            withoutExtensions.append(os.path.splitext(file)[0])

        if outputName in withoutExtensions:
            num = sum(outputName in s for s in withoutExtensions)
            outputName = outputName + " (" + str(num) + ")"

        return outputName

    def downloadAndCombineVideo(self, videoItag: int, audioItag: int, outputName: str = None) -> bool:
        """
        Downloads a video and then combines the audio and video files into a single file
        :param videoItag: tag from video options. Determines which of those options will be downloaded
        :param audioItag: tag from audio options. Determines which if those options will be downloaded
        :param outputName: a custom name for the combined video. If empty, will just be the name of the downloaded video
        :return: whether download and combination was successful
        """

        # Streams from which the videos are downloaded from
        # Makes sure Itags are valid
        try:
            videoStream = self._videoOptions.get_by_itag(videoItag)
            audioStream = self._audioOptions.get_by_itag(audioItag)
        except ValueError:
            return False
        except AttributeError:
            return False

        if videoStream is None or audioStream is None:
            return False

        # Makes sure that output folder exists
        if not os.path.exists(self._outputFolder):
            os.mkdir(self._outputFolder)

        # Makes sure there is an output name for the final combined video
        if outputName is None:
            outputName = videoStream.title
        outputName = cleanFilename(outputName)  # Checks that the name is valid

        outputName = self._generateSafeFilename(outputName)  # Generates a non-existing file name
        # Creates a temporary file for the file so if user download's more videos with same name they won't overwrite
        with open(os.path.join(self._outputFolder, outputName + ".mp4"), "w+") as file:
            file.write("TEMP DOWNLOAD FILE")
            file.close()

        # Generate names for temporary videos
        videoNums: List[int] = self._getNextVideoNums()

        videoName: str = self._videoNameFormat + str(videoNums[0]) + ".mp4"
        audioName: str = self._audioNameFormat + str(videoNums[1]) + ".mp4"

        # Downloads audio and video
        audioStream.download(output_path=self._tempVideoFolder, filename=audioName)
        videoStream.download(output_path=self._tempVideoFolder, filename=videoName)

        # Combines audio and video
        self.combine(videoName, audioName, outputName, ".mp4")

        sleepTime: int = 1  # How often program checks if combination is done

        # Wait for combination to finish
        fullPath: str = os.path.join(self._outputFolder, outputName + ".mp4")
        while not os.path.exists(fullPath):
            time.sleep(sleepTime)

        # Remove the temp files
        self._removeTempFile(videoName)
        self._removeTempFile(audioName)

        self._onVideoCombinedFunc(self._interfaceIndex)

        return True

    def combine(self, videoFile: str, audioFile: str, outputFile: str, extension: str):
        """
        Combines a video and an audio file
        :param extension: extension of the video file
        :param videoFile: name of the video file
        :param audioFile: name of the audio file
        :param outputFile: name of the output file
        """
        codec: str = "copy"
        # Create paths
        videoPath: str = os.path.join(self._tempVideoFolder, videoFile)
        audioPath: str = os.path.join(self._tempVideoFolder, audioFile)
        outputPath: str = os.path.join(self._outputFolder, outputFile + extension)

        command: str = f"\"{self._ffmpegPath}\" -i \"{videoPath}\" -i \"{audioPath}\" -c {codec} \"{outputPath}\""

        process: subprocess.DETACHED_PROCESS = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)  # Run the command and return the process
        process.stdin.write(b"y\n")  # Tell the process to continue if an output file with same name already exists
        process.communicate()  # Run 'y\n' to overwrite if a video with same name already exists
        process.stdin.close()  # Close the process

    def fetchOptions(self) -> bool:
        """
        Gets the options from which the video can be downloaded from.
        These options contain information about the video such as resolution.
        :return: whether fetching was successful or not
        """

        # Tries to find the video and create a connection
        try:
            video: YouTube = YouTube(self._link)
        except RegexMatchError:
            return False

        # Gets video and audio options. Filters them to be video and audio
        self._videoOptions = video.streams.filter(mime_type="video/mp4")
        self._audioOptions = video.streams.filter(only_audio=True)

        # If program didn't find any downloadable options, tries to find again but with less filtering
        if len(self._videoOptions) == 0:
            self._videoOptions = video.streams.filter(file_extension="mp4")

        if len(self._audioOptions) == 0:
            self._audioOptions = video.streams.filter(only_audio=True)

        # Makes sure it could find some options
        if len(self._videoOptions) > 0 and len(self._audioOptions) > 0:
            return True
        else:
            return False
