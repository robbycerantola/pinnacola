git clone git://git.code.sf.net/p/pinnacola/code pinnacola-code

Pinnacola 0.8.1  2014(c) by Robby Cerantola                   12/11/2014

Features
--------
  * Pinnacola cards game.
  * Multiplayer.
  * Multiplatform: runs on Linux, Windows, Mac OS, Android 
    


In brief
--------

Pinnacola is a multi user game, minimum 2 players needed, maximum 4.
First one terminal has to be started as Server by changing the mode in 'settings'.
Then the other terminals have to start as Clients in succession .
In 'settings' every client has to set a unique user name and the Server ip address to connect to.


Dependencies
------------

  
  * Python 2.7
  * Kivy 1.1.2 or later
  * Twisted 
  

Optionally
----------
  
  * Kivy-Launcer for Android platform
  * Buildozer



Usage
-----

1) Install the dependencies listed above:
    
    Python:
        
        
    Kivy:
    

    Twisted:
        pip install twisted

2) On Linux run python ./main.py
    It can be started from console in server mode by 
    
        python ./main.py -- -S 
        
    ( note space between -- and -S to override kivy arguments handling)
    or in console mode by 
    
        python ./main.py -- -C
        
    Open port 8123 for multiplayer !
    
3) On Windows 7 or later:
    draw the main.py file to kivy.bat file in kivy directory.

4) On Android you have to install Kivy-Launcer to run the application. 
    You have to copy all the sources into kivy directory.
    To start as client for now go into settings and change
    game mode from Server to Client and then restart.   (Working on this issue.......)
    From now on it will start in Client mode untill you change again in settings.
 

   Optionally you could compile the sources using buildozer.

5) On Mac OS:
    (Someone has tried?)



How to play
-------------

Rules, see: http://it.wikipedia.org/wiki/Pinnacola
(translator wanted.....)

The Pinnacola is played with 2 decks of 52 cards, in opposite pairs. 
The dealer (Server) distributes 13 or 15 cards each, the rest of the deck 
is placed at the center of the table and the first card turned out.
Each player in turn must draw a card from the deck or from the well, insert 
it between those in his hand, possibly dropping one or more combinations
and then discard a card.
While moving the cards, they are selected (frames turn red) and then can 
be dropped or deselected by pushing the appropriate button in the upper 
part of the screen.
By moving a card towards the discard zone, it will be discarded while
moving it outside the well, it will be picked up.  




Known Issues
------------

Work in progress
Simple game functionality, multiuser .
No rules checking yet.
Graphic interface incomplete.
Lot of debug informations



Future development
------------------

Playing in pairs.
Turnament.
Playing against virtual players.



Thanks
------

to PlayOnLoop.com for the Intro loop music; 

to my grandparents Mario and Anna, who teached me this game when 
I was a child.



