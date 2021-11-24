import os
import time
import signal
import random
import warnings
import subprocess
from time import sleep
from threading import Thread
from utils.system import paths, command
from utils.thread_helpers import thread
from playerFramework.exceptions import *


class player:
    """
    This will be the API to interact with the player, the player class can not be initialised without
    a valid path to the player if the player file does not exist an exception will be raised
    """

    def __init__(self, executable: str = '/usr/bin/afplay', info=None, warning=True):
        """
        :param warning:
        boolean to spit out warnings
        default set to True

        :param executable:
        path to the executable file
        if left blank default player will be afplay

        :param info:
        a dictionary containing the IO file path and commands to pause or play the player
        i.e.
        {
            'io file': '/Users/*/.ioFile',
            'play' : ['player', '**path**'],
            'pause': 'pause',
            'resume': 'resume',
            'exit': 'stop',
            'exit_codes': [4, 5, 6],
            'Volume': 'volume:{}'
        }

        if the player does not conform to the standard arg[0] == executable_path and arg[1] == track_path
        the 'play' value must be a list which defines how the player will ba called via subprocesses/utils
        with the keyword '**path**' which defines where the framework will replace it with the path to the track
        otherwise leave 'play' to the value of None

        exit_codes value is optional although if the player exits with the codes [15, 9, 2, 4] an exception will be
        raised playerFramework.exceptions.ProcessTerminatedExternally


        if the player doesnt support pausing and resuming using IO files than use the .pause()
        and .resume() functionality
        """
        if info is None:
            info = dict(play=None, exit_codes=[])

        self.internalKill = False
        self.warning = warning
        self.exec = paths.Path(executable)
        self.info = info
        self.thread = None

        self.pid = None

        self.cs_playing = None
        self.file_resume_bytes = None

        self.exitCodes = []

        if info.__contains__('exit_codes'):
            for code in info['exit_codes']:
                self.exitCodes.append(abs(int(code)))

        if not self.exec.isPath():
            raise PlayerPathNotValid('Player not found')


        self._handle_args()

    @staticmethod
    def __info_object():
        """return a blank object of type playerStorageObject"""
        class playerStorageObject:
            def __init__(self, running_thread):

                if not isinstance(running_thread, Thread):
                    raise songObjectNotInitialized('Expected type Thread got type: {}'.format(type(running_thread)))

                self.thread = running_thread

        return playerStorageObject



    def _handle_args(self):
        if self.info is None or self.info == {}:
            self.info = {'play': None}

    # noinspection PyTypeChecker
    def changeValue(self, key_name, Format=False):
        """
        :param key_name:
        Will be used to find the value against info dictionary
        :param Format:
        Value to format the string via {}
        :return:
        """
        try:
            if not paths.file_exists(self.info['io file']):
                raise UnableToWriteToIOFile('IO File does not exist')
        except KeyError:
            raise UnableToWriteToIOFile('No IO file specified')

        try:
            if Format is False:
                with open(self.info['io file'], 'w+') as file:
                    file.write(self.info[key_name])
            else:
                writeINFO = self.info[key_name].format(Format)
                with open(self.info['io file'], 'w+') as file:
                    file.write(writeINFO)

        except FileNotFoundError or PermissionError as exception:
            raise UnableToWriteToIOFile(exception)

        except KeyError as exception:
            raise UndefinedKey(exception)

    def _reset(self):
        self.pid = None
        self.cs_playing = None
        self.file_resume_bytes = None

    def play_track(self, track_path, main_thread=False):
        """
        The player will not be run on the main thread
        to wait till the player is completed on the main thread use .wait_for_player()

        :param main_thread:
        by default set to false, if true the player will be on the main thread
        :param track_path:
        path to the file that will be played
        :return:
        Keep a reference to the object returned as it is the frameworks
        prediction on where the player should be at in seconds passed or total duration
        if the player is paused via and internal methods such as writing to IO file
        then the time from the song object won't be accurate. It will however reflect
        .pause() or .resume()
        """

        class current_song:
            def __init__(self, song):
                self.path = song
                self.audio_segment = None
                self.audio = 0
                self.seconds_passed = 0
                self.percentage_completed = 0
                self.err = None




        track_path = abs(paths.Path(track_path))

        def internal_player(playerClass, track):
            arguments = [playerClass.exec.path]
            playINFO = playerClass.info['play']
            if playINFO is None:
                arguments.append(track_path)
            else:
                for a in playINFO:
                    if a == '**path**':
                        a = track

                    arguments.append(a)

            try:
                process = subprocess.Popen(args=arguments, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                           stderr=subprocess.STDOUT)


                self.pid = process.pid

                process.communicate()[0].decode('utf8')
                process.wait()
                process.poll()
                return_code = int(abs(process.returncode))

                if self.internalKill is not True:
                    if not self.exitCodes.__contains__(return_code):
                        if return_code != 0:
                            self._reset()
                            err_msg = 'Expected return code 0, got return code: {}'.format(return_code)
                            raise ProcessTerminatedExternally(err_msg)


                # print('Return Code: ' + return_code.__str__())
                # print('exit code', return_code)

                # any code executed after this point means the player is not alive
                self.thread = None

            except KeyboardInterrupt:
                warning = 'Player was stopped by KeyBoardInterrupt'
                if playerClass.warning:
                    # Not raising an exception just letting the user know
                    warnings.warn(warning)
                    self._reset()

            self.thread = None

        if self.warning:
            if not paths.file_exists(track_path):
                raise InvalidTrackPath('The file "{}" does not exist'.format(track_path))

        if self.is_playing():
            try:
                self._kill_player()
            except ProcessLookupError:
                pass

        if main_thread:
            internal_player(playerClass=self, track=track_path)
        else:
            self.thread = thread(func=internal_player, args=[self, track_path])
            self.cs_playing = current_song(track_path)
            self._calculations(self.cs_playing)
            return self.cs_playing

    def _calculations(self, clss, re=True):
        def internal(self_, cls, re_write=True):
            try:
                now = time.time()
                from pydub.audio_segment import AudioSegment
                cls.audio_segment = AudioSegment.from_file(cls.path)
                cls.audio = round(cls.audio_segment.duration_seconds)
                post = time.time()


                if re_write:
                    cls.seconds_passed = 0
                    cls.percentage_completed = 0

                # the time it took for ffmpeg to load and stuff
                cls.seconds_passed += int(post - now)

                while self_.is_playing():
                    if cls.seconds_passed >= cls.audio:
                        break

                    cls.seconds_passed += 1
                    cls.percentage_completed = round((cls.seconds_passed / cls.audio) * 100)
                    time.sleep(1)
            except Exception as processErr:
                cls.err = processErr.__str__()

        thread(func=internal, args=[self, clss, re])


    def fake_pause(self):
        """if the audio has paused due to because of IO file, or external reasons call
        fake_pause() to reflect it in the current_song obejct"""

        # So we have to make self.is_alive = False
        # which should break the _calculations loop
        # then we can fake_resume

        # we need to store a refrence to this object
        thread_with_player = self.thread
        self.thread = False

        infoObj = self.__info_object()(thread_with_player)
        self.file_resume_bytes = infoObj


    def fake_resume(self):
        """if the audio is resumed externally (or via IO file) reflect on cs via this method"""
        try:
            self.thread = self.file_resume_bytes.thread
            self._calculations(clss=self.cs_playing, re=False)
        except TypeError:
            raise invalidInternalType('Expected type playerStorageObject got type: {}'
                                      .format(type(self.file_resume_bytes)))



    def pause(self):
        try:
            self._kill_player()
        except TypeError:
            try:
                time.sleep(1)  # some times it takes a second for all the variables to load into their place
                self._kill_player()
            except TypeError:
                raise songObjectNotInitialized('No song is currently playing')

        # lets cut the audio file and save it in buffer memory (less overhead i think)
        # write the file into temp file and remove after resuming player

        # --current_song-- Obj
        # self.path = song
        # self.audio_segment = None
        # self.audio = 0
        # self.seconds_passed = 0
        # self.percentage_completed = 0
        # self.err = None

        # lets create a new AudioSegment instead of referencing the one in current song
        cs = self.cs_playing
        song = self.cs_playing.audio_segment
        time_lapsed = cs.seconds_passed

        time_left = int(cs.audio - time_lapsed) * 1000  # milliseconds

        try:
            rest_of_song = song[-time_left:]
        except TypeError:
            errmsg = 'Song is not initialised yet, make sure the player is still playing'
            raise songObjectNotInitialized(errmsg)
        temporary_file = random.random().__str__()


        rest_of_song.export(temporary_file, format='wav')

        file = open(temporary_file, 'rb+')
        self.file_resume_bytes = file.read()
        file.close()

        os.remove(temporary_file)


    def resume(self):
        if self.file_resume_bytes is not None:
            file_name = random.random().__str__()
            with open(file_name, 'wb+') as file:
                file.write(self.file_resume_bytes)

            path = paths.join(os.getcwd(), file_name)
            # print(path)

            # self.play_track(self.cs_playing.path, main_thread=True)
            self.thread = thread(self.play_track, [path, True])
            self._calculations(clss=self.cs_playing, re=False)

            def remove(file_path):
                time.sleep(2)
                os.remove(file_path)

            thread(remove, [path])
        elif self.file_resume_bytes is None:
            msg = 'Please make sure to call .pause() before .resume()'
            raise unableToReadBytes(msg)



    def wait_for_player(self):
        if self.thread is not None:
            if self.thread.is_alive():
                self.thread.join()
            else:
                warnings.warn('Thread is not alive: {}'.format(self.thread))

    def is_playing(self):
        if isinstance(self.thread, Thread):
            if self.thread.is_alive():
                return True
            else:
                return False
        return False

    def _kill_player(self):
        if isinstance(self.pid, int):
            self.internalKill = True
            os.kill(self.pid, signal.SIGTERM)
            sleep(0.1)
            self.internalKill = False

    def exit(self):
        # Old documentation
        # The exit function is not 100% accurate, it works of the 'killall' command meaning
        # if there are multiple instances of the executable will be closed. If a player is terminated without calling
        # .exit() will raise ProcessTerminatedExternally
        try:
            self._kill_player()
        except ProcessLookupError:
            pass

        self._reset()

    def kill_all(self):
        """
        kills all instances of the player
        this isn't 100% reliable as we use the file name as the process name
        """
        exec_name = self.exec.last_component()
        command(['killall', exec_name], quite=True)
