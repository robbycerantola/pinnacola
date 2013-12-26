git clone git://git.code.sf.net/p/pinnacola/code pinnacola-code

Pinnacola 0.7  2013(c) by Robby Cerantola 

Features:
  * Pinnacola cards game.
  * Multiuser.
  * Multiplatform: runs on Linux, Windows, Mac OS, Android 
    


Dependencies
------------

  
  * Python 2.7
  * Kivy 1.1.2
  * Twisted 
  

Optionally
----------
  
  * Kivy-Launcer for Android platform
  * Buildozer



Usage
-----

0) Install the dependencies listed above.

2) On Linux run python ./main.py
    It can be started from console in server mode by python ./main.py -- -S ( note space between -- and -S to 
    override kivy arguments handling) or in console mode by python ./main.py -- -C
    
3) On Windows (yet to be tested)

4) On Android you have to install Kivy-Launcer to run the application. 
    You have to copy all the sources into kivy directory.
    To start as client for now go into settings and change
    game mode from Server to Client and then restart.   (Working on this issue.......)
    From now on it will start in Client mode untill you change again in settings.
 

   Optionally you could compile the sources using buildozer.


It is a multi user game, minimum 2 players needed, maximum 4.
One terminal has to be started as Server and the other as clients .
In settings you have to set your user name and the server ip address to connect to.



How to play
-------------

Rules, see: http://it.wikipedia.org/wiki/Pinnacola
(translator wanted.....)

The Pinnacola is played with 2 decks of 52 cards, in opposite pairs. 
The dealer (Server) distributes 13 or 15 cards each, the rest of the deck is placed at 
the center of the table and the first card turned out.
Each player in turn must draw a card from the deck or from the well, insert it between
those in his hand, possibly dropping one or more combinations and then discard a card.
While moving the cards, they are selected (frames turn red) and then ca be dropped or deselected by 
pushing the appropriate button in the upper part of the screen.
By moving a card towards the discard zone, 
it will be discarded while moving it outside the well, it will be picked up.  




Known Issues
------------

Work in progress
Simple game functionality, multiuser (two players only for now).
No rules checking yet.
Graphic interface incomplete.
Lot of debug informations



Future development
------------------

Playin in pairs.
Turnament.
Playing against virtual players.



Thanks
------

to Intro loop music from PlayOnLoop.com

to my grandparents who teached me this game when I was a child.



