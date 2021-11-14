# playerFramework
playerFramework allows you to play, pause audio files in python easily without having to miss around with
PyobjC and millions of dependencies.

##  Quickstart

Start playing a song from a file
```python
from playerFramework import player 
ply = player()

song = ply.play_track('/Users/*/song.mp3')
```

Get information on the song being player
```python
from playerFramework import player
song = player().play_track('/Users/*/song.mp3')

song_total_seconds = song.audio
song_seconds_passed = song.seconds_passed
song_percentage_passed = song.percentage_completed

```

Pause or resume the song
```python
from playerFramework import player
ply = player()

# ffmpeg is required for pausing the song
ply.pause()
ply.resume()

ply.exit() # completely stops playback, no way to restore the position the song was at 
```



Make a little animation
```python
import sys
import time
from playerFramework import player

ply = player()
song = ply.play_track('/Users/*/Maze.mp3')

while ply.is_playing():
    sys.stdout.write('\r{}/{} | {}%'.format(song.seconds_passed, song.audio, song.percentage_completed))
    sys.stdout.flush()
    time.sleep(1)
```

Note the time/passage of time given by playerFramework is an estimate on what the time should be, if the player
pauses (not from .pause()) it will not be reflected in the .seconds_passed attribute


Attributes and Functions of playerFramework.player()
```python
from playerFramework import player
player_exec = str("/usr/local/bin/ffplay") # Let's use ffplay as out player_exec this time instead of afplay by default
ply = player(executable=player_exec)

ply.changeValue('volume', Format='100') #  write to io file (Format is optional value)

ply.is_playing()  # Check if the player is currently alive

ply.resume() # resumes the track
ply.pause() # pauses the track

ply.play_track('song.mp3')  # plays a song returns current_song object

ply.kill_all() # kill all instances of the player (what ever was declared when initialising player())     

_ = ply.warning  # the warning bool set when initialised
_ = ply.cs_playing # the current_song initialised with the song being played from .play_track

_ = ply.file_resume_bytes # when .pause() is called the bytes of the remaining song duration
    
_ = ply.exec # a path object of the player (type: utils.system.paths.Path)
_ = ply.info # dictionary of how the player was set up  
    
_ = ply.thread # the thread the player is on
    
_ = ply.exit # kill the player subprocess

_ = ply.pid # the pid of the player                
_ = ply.wait_for_player # same as thread.join()
```
