
import pygame
import time
import atexit

# Track currently loaded sound to avoid repeating initial load.
current_sound = None

def play_sound(filepath):
    """Plays the sound specified by the file path."""
    global current_sound  #Use the global current variable...

    if filepath != current_sound :
        # Load sound; this action may clear the existing queue (see clear) before loading...
        try:
           sound = pygame.mixer.Sound(filepath) # use a sound data
           pygame.mixer.stop()       # Remove sound channel before switching over;
        except Exception as e:
           print (f"Faild with Exception: {e}")
           return  # Handle audio failures gracefully
        current_sound = filepath

        pygame.mixer.Sound.play(sound) #Use Sound api instead....
    else:
        # Re-play directly without repeating initial loads, to maintain best continuity
        sound = pygame.mixer.Sound(filepath)  # Load Sound and keep as object to manage....
        pygame.mixer.stop()

        pygame.mixer.Sound.play(sound)   # restart and play... best contunites...


    duration = sound.get_length()  # get and print the total second need to played.  Avoid premature program terminates early
    print(f"Length of audio  = {duration:.2f} s")

    start_time = time.time()  # Capture start timestamp to assess accurately remaining periods


    while pygame.mixer.get_busy():   #Check to prevent mainthread quiting. if playing finished quiting early!!!

        remain = duration  - (time.time()- start_time);  # use to precisely determine remaining periods.. better check and monitor process
        # print("remaning duration is %.2f seconds"%remain )
        # Keep the script run to hold..

        pygame.time.Clock().tick(10);  #Ensure code loop only for tiny pauses!! Dont consume heavy processors load in this looping checking.

        if remain < 0: break

    print("done playing..!")

    # No Explicitly call needed sound.stop().  to auto handle freeing from sound.mixer resources

    return

@atexit.register #auto call exit.
def auto_uninit():  #Clear when exited ensure everyhing clean

  pygame.mixer.quit()

def playsnd(filepath):
    global current_sound
    # Initialize Pygame's mixer
    pygame.mixer.init()

    # Track currently loaded sound to avoid repeating initial load.
    current_sound = None
    try:
        play_sound(filepath) # Start
    except Exception as e:  # general issue while swappying the codec sounds, we will catches here prevent sudden drop and error display.

        print(f"Playing Error due to:{str(e)}")

    finally:

        pygame.mixer.quit()   #Uninit after tasks complete and free resources;

if __name__ == "__main__":
    # example code demonstrating. playing sound for 3s then swap others..
    audio1 = "./Temp/temp.mp3"   # ensure have available .wav file inside paths....or pygame unable create valid stream readers.. for codecs playing ...
    audio2 = "./Temp/temp.mp3"   # Replace  paths...

    # Start playback sequences
    try:
        play_sound(audio1) # Start
        print("Done First Play")
        time.sleep(1) #Add little Pause to Ensure properly swiched. to Prevent Crash

        play_sound(audio2)
        print("Done Second Play")
    except Exception as e:  # general issue while swappying the codec sounds, we will catches here prevent sudden drop and error display.

        print(f"Playing Error due to:{str(e)}");

    finally:

        pygame.mixer.quit()   #Uninit after tasks complete and free resources;
    print ("completed sample tasks!!! normal shutdown ")


