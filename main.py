#!/usr/bin/python
# -*- coding: utf-8 -*-
#:PEP8 -W293

'''
Pinnacola        Copyright (c) 2014 2015 2016 by Robby Cerantola
=======================================

This is a basic pinnacola cards game, using kivy ,the scatter widget
the screenmanager widget and Twisted.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''

__version__ = '0.8.5'
#v 0.0 deck, userinterface
#v 0.1 simple net messages (Twisted), server only
#v 0.2 implement screen manager
#v 0.3 registra le carte calate
#v 0.4 multiple screens
#v 0.5 cleaning and debugging
#v 0.6 started client implementation
#v 0.7 beta playable in two players, no rules check yet (bugged!!)
#v 0.7b server ip selectable in settings
#v 0.8 multiplayer, no rules check yet BUGGED!!
#v 0.8.1 cleanup
#v 0.8.2 refactoring, 3 players
#V 0.8.3 android compatible, 4 players
#v 0.8.4 raspberry compatible , internationalization
#v 0.8.5 external kv file

import kivy
kivy.require('1.9.0')

from kivy.config import Config
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '480')


# install_twisted_reactor must be called before
#importing  and using the reactor
from kivy.support import install_twisted_reactor
install_twisted_reactor()

from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory

from kivy.app import App
from kivy.logger import Logger
from kivy.uix.scatter import Scatter
from kivy.properties import StringProperty, NumericProperty
from kivy.animation import Animation
# FIXME this shouldn't be necessary
#from kivy.core.window import Window    #create Opengl context

#from kivy.uix.floatlayout import FloatLayout
#from kivy.uix.boxlayout import BoxLayout
#from kivy.uix.button import Button

from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.anchorlayout import AnchorLayout
from kivy.lang import Builder,Observable, EventDispatcher
from kivy.core.audio import SoundLoader
from kivy.clock import Clock

import sys
import random
import re
from os.path import join, dirname

import gettext

language='it' # default language on first start up

DEBUG = 1                 # set to 1 to get extra debug info

PLAYERS = 4
DISCARDY = 250
GAMEMODE = None           # can be 'Server' or 'Client'
SERVER = ''
PORT = 8123               #Twisted connection port
CONNECTION = {}           #Twisted connections instances
NAMES = []                # NAMES stores only the other players names no server name included!! 
DECKINSTANCE = None
PLAYERINSTANCE = {}       #Players instances including local one
SELCARDS = []



class Lang(Observable):
    observers = []
    lang = None

    def __init__(self, defaultlang):
        super(Lang, self).__init__()
        self.ugettext = None
        self.lang = defaultlang
        self.switch_lang(self.lang)

    def _(self, text):
        return self.ugettext(text)

    def fbind(self, name, func, args, **kwargs):
        if name == "_":
            self.observers.append((func, args, kwargs))
        else:
            return super(Lang, self).fbind(name, func, *largs, **kwargs)

    def funbind(self, name, func, args, **kwargs):
        if name == "_":
            key = (func, args, kwargs)
            if key in self.observers:
                self.observers.remove(key)
        else:
            return super(Lang, self).funbind(name, func, *args, **kwargs)

    def switch_lang(self, lang):
        # get the right locales directory, and instanciate a gettext
        locale_dir = join(dirname(__file__), 'data', 'locales')
        locales = gettext.translation('pinnacola', locale_dir, languages=[lang])
        self.ugettext = locales.ugettext

        # update all the kv rules attached to this text
        for func, largs, kwargs in self.observers:
            func(largs, None, None)



tr = Lang(language) #instantiate curent language

# BUG?!? Can use  external kv file only by declaring it explicitely:
# screen manager seems to work only with inline statements!

Builder.load_file('pinnacola1.kv')


class Deck():
    '''Create cards' deck in memory using the following convention:
        1 to 13 number of card, and f for flower p for  q for  and
         c for hearts 0-1.. number of deck.
        Manage the metods to use the deck
    '''
    #assign to every card some points
    points_table = {'1': 15, '2': 5, '3': 5, '4': 5, '5': 5, '6': 5, '7': 10,
    '8': 10, '9': 10, '10': 10, '11': 10, '12': 10, '13': 10, 'j': 30}

    def __init__(self, app, n_mazzi=1):
        '''initialize the cards deck'''
        self.n_mazzi = n_mazzi
        self.deck = []
        self.ontable = []
        semi = ['q', 'c', 'p', 'f']
        self.app = app

        for volte in range(self.n_mazzi):  # how many decks are used
            for a in semi:
                for i in range(1, 14):
                    tmp = '%s%s%s' % (i, a, volte)
                    #print tmp
                    self.deck.append(tmp)
            # add jokers
            self.deck.extend(['jr%s' % (volte), 'jn%s' % (volte)])
            
        self.shufflecards()
        #if DEBUG: print self.deck

    def shufflecards(self):
        '''Shuffle the cards in the deck'''
        random.shuffle(self.deck)

    def pickacard(self):
        '''Get a card randomly from deck'''
        if len(self.deck) >0 :
            sel = random.choice(self.deck)
            self.deck.remove(sel)
        else:
            sel= ""
        return sel

    def allcards(self):
        '''return all the cards in the deck'''
        return self.deck

    def pit(self):
        '''return all the cards that where discarded'''
        return self.ontable

    def put_ontable(self, card):
        '''Discard in the pit'''
        self.ontable.append(card)

    def pick_fromtable(self, card):
        '''Draw a card from pit'''
        try:
            self.ontable.remove(card)
        except:
            print 'Some error, the card you wish to remove is not on table!'

    def value(self,card):
        return card[:-1]
    
    def number(self,card):
        return card[:-2]
        
    def seed(self,card):
        return card[:-1][-1]

class Player():
    counter = 0
    def __init__(self,name,place=0):
        global NAMES
        if DEBUG:print NAMES, len(NAMES),Player.counter
                          # refresh also name in main screen  ###very ugly!!!
        screennames = ['pinnacolabackground','player2','player3','player4']
        if GAMEMODE == "Server":
            if len(NAMES) == 1:
                sm.get_screen('pinnacolabackground').gamer2 = name
            if len(NAMES) == 2:
                sm.get_screen('pinnacolabackground').gamer3 = name
            if len(NAMES) == 3:
                sm.get_screen('pinnacolabackground').gamer4 = name
        
        if GAMEMODE == "Client" and len(NAMES) == 0:
            screennames = ['pinnacolabackground','player4','player2','player3']
            if Player.counter == 1:
                sm.get_screen('pinnacolabackground').gamer4 = name #ok
            if Player.counter == 2:
                sm.get_screen('pinnacolabackground').gamer2 = name #ok
            if Player.counter == 3:
                sm.get_screen('pinnacolabackground').gamer3 = name #ok
        if GAMEMODE == "Client" and len(NAMES) == 1:
            screennames = ['pinnacolabackground','player3','player4','player2']
            if Player.counter == 1:
                screennames = ['pinnacolabackground','player3','player4','player2']
                sm.get_screen('pinnacolabackground').gamer3 = name
            if Player.counter == 2:
                sm.get_screen('pinnacolabackground').gamer4 = name
            if Player.counter == 3:
                sm.get_screen('pinnacolabackground').gamer2 = name
        if GAMEMODE == "Client" and len (NAMES) == 2:
            screennames = ['pinnacolabackground','player4','player2','player3']
            if Player.counter == 1:
                sm.get_screen('pinnacolabackground').gamer4 = name
            if Player.counter == 2:
                sm.get_screen('pinnacolabackground').gamer2 = name
            if Player.counter == 3:
                sm.get_screen('pinnacolabackground').gamer3 = name
            
        self.positions=[10,60,110,160,210,260,310] #posizioni automatiche delle carte calate
        self.hand = []
        self.down = []
        self.points = 0
        self.name = name
        self._nr = None
        #assign a screen to each player
        if place == 0:
            self.screen = screennames[Player.counter]
        else:
            self.screen = screennames[place]
            
        Player.counter += 1
            
        self.pos=1  #successiva posizione libera per calare le carte
        
        #assign a name to each player
        sm.get_screen(self.screen).gamer = name
        if DEBUG: print tr._("Created player instance "),name

    def gamername(self,n):
        return 'none' if len(NAMES) <2 else NAMES[n-1] 
    
    def addcard(self, card):
        self.hand.append(card)

    def deletecard(self, card):
        try:
            self.hand.remove(card)
        except:
            print 'Some error, the card you wish to remove is not in player\
                    hand, not removing again.'

    def playcard(self, card):
        self.hand.remove(card)

    def hand(self):
        return self.hand
        
    @property
    def left(self):
        return len(self.hand) if self._nr is None else self._nr 

    def putdown(self, cards):
        self.down.append(cards)
        #calculate player's points
        for card in cards:
            #self.points += int(Deck.points_table[card[:-2]])
            self.addpoints(card)
            

    def down(self):
        return self.down

    def addpoints(self,card):
        self.points += int(Deck.points_table[card[:-2]])
        print "CardPoint",card


class Picture(Scatter):
    '''Picture is the class that will show the cards with a white border and a
    shadow. There are nothing here because almost everything is inside the
    inline kv statements. Check the rule named <Picture> , and you'll
    see how the Picture() is really constructed and used.
    The source property will be the filename to show.
    '''
    source = StringProperty(None)
    card = StringProperty(None)
    selected = StringProperty(None)  # to store information about selection
    condition = StringProperty(None)  # information about beeing in the pit
    c = NumericProperty(1)  # to store information about border colour
   # def __init__(self, **kwargs):
   #     self.size= [50,50]
   #     self.pos = [100,50]
   #     self.c = 1
   #     super(Picture, self).__init__(**kwargs)


#declare screens
class PinnacolaBackground(Screen):
    
    ver = __version__
    points = NumericProperty(0)
    info = StringProperty(tr._("Welcome!"))
    gamer2 = StringProperty('2')
    gamer3 = StringProperty('3')
    gamer4 = StringProperty('4')

    def __init__(self, **kwargs):
        super(PinnacolaBackground, self).__init__(**kwargs)
        
                

class IntroScreen(Screen):
    
    ver = __version__
    string = "Pinnacola %s" % ver
    info = StringProperty(string)

    def on_info(self, instance, value):
        pass

class RulesScreen(Screen):
    '''Introduzione al gioco'''
    import codecs
    #load rules text in proper language
    rulesfile = "rules"+str(language)+".txt"
    try:
        with codecs.open(rulesfile, "r", encoding="utf8") as myfile:
            rulestxt = "".join(line for line in myfile)
    except EnvironmentError:
        rulestxt = tr._("Rules file not found !")


class SettingsScreen(Screen):
    pass


class Player2Screen(Screen):
    ver = __version__
    points = NumericProperty(0)
    gamer = StringProperty("not connected")

class Player3Screen(Player2Screen):
    pass

class Player4Screen(Player2Screen):
    pass


#######sc


class PinnacolaApp(App):
    icon='pinnaicon.png'  #define icon
    #title='Titolo' #define title
    player = {}  #needed to bound screen buttons to app functions
    
    #client side connection
    connection = None  
    picture = None
    cards_server = []
    # cards currently selected
    selcards = []

    lang = StringProperty(language) #set default language

    def on_lang(self, instance, lang):
        tr.switch_lang(lang)

    def on_pause(self):
        return True

    def on_start(self):
        pass

    def build(self):
        global max_cards, GAMEMODE, SERVER, PLAYERINSTANCE, language
        #load configurations from ini file
        config = self.config
        max_cards = int(config.get('section1', 'max_cards'))
        if GAMEMODE is None: 
            GAMEMODE = config.get('section1', 'gamemode')
            sm.get_screen('intro').info = "%s mode," %(GAMEMODE) + tr._(" waiting for connections..")
        self.playername = config.get('section1', 'name')
        SERVER = config.get('section1', 'serverip')
        # card y position and discarded flag
        self.numDiscarded = self.oldvalue = self.flag = 0
        self.oldinstance = None
        
        intromusic = int( config.get('section1', 'intromusic'))
        
        language = config.get('section1','language')  #set language from ini file
        tr.switch_lang(language)
        
        self.sound = SoundLoader.load('./music/intro.wav')
        if self.sound and intromusic:
            self.sound.loop = True
            self.sound.play()
        
        #create global instance for local player to be called from everywhere
        PLAYERINSTANCE['Local'] = Player(self.playername) #####
        
        if GAMEMODE == "Server":
            # start server
            reactor.listenTCP(PORT, ChatFactory(self))
            if DEBUG: print "Twisted server listening on port %s \n" % PORT
            self.startplay(sm.get_screen('pinnacolabackground'))
        
        if GAMEMODE == "Client":
            # start client
            self.connect_to_server()
        
        return sm

    def startplay(self, root):
        '''Prepare game'''
        global DECKINSTANCE, PLAYERINSTANCE
        #create instance for current deck 
        DECKINSTANCE = self.currentDeck = Deck(self, 2)  # use 2 decks of 52 cards
                
        # and display cards on hand
        #####PLAYERINSTANCE['Local'] = self.player[0] = Player(self.playername)

        self.player[0] = PLAYERINSTANCE['Local'] #workaround to bind screen buttons to PLAYERINSTANCE
        
        
        #disposition of cards on start screen
        cy = [50, 53, 55, 60, 70, 75, 80, 85, 80, 75, 70, 60, 55, 53, 50]
        cx = 0
        rot = 0

        for i in range(max_cards):
            if GAMEMODE == "Server":
                entry = self.currentDeck.pickacard()
            else:
                # display cards received from Server
                entry = self.cards_server[i]

            cx += 25
            
            PLAYERINSTANCE['Local'].addcard(entry)
            try:
                # load the image
                picture = Picture(source='atlas://decks/cards/%s' % entry[:-1], rotation=int(rot), x=200+cx , y=cy[i]-120, card=entry)
                
            except Exception, e:
                Logger.exception('Pictures: Unable to load card %s from atlas' % entry[:-1] )
            
            picture.bind(pos=self.callback_pos)
            picture.bind(on_touch_down=self.callback_touch)
            # add to the main field
            root.add_widget(picture)
        

        # Put first card in the pit
        if GAMEMODE == "Server":
            entry = self.currentDeck.pickacard()
            self.currentDeck.put_ontable(entry)
            self.show_pit(entry, root)

    def show_pit(self, entry, root):
        '''show cards on pit, suitable for Server and Client'''
        try:
            # load the image
            picture = Picture(source='atlas://decks/cards/%s' % entry[:-1], rotation=int(0), x=230+10*self.numDiscarded , y=DISCARDY,scale=.7, card=entry, condition='pit')
            
        except Exception, e:
            Logger.exception('Pictures: Unable to load card %s from atlas' % entry[:-1] )
        
        picture.bind(pos=self.callback_pos)
        picture.bind(on_touch_down=self.callback_touch)
        root.add_widget(picture)

    def showcard(self, stat=0):
        """pick a card from local or remote deck and show on table"""
        sm.get_screen('pinnacolabackground').info=""
        if GAMEMODE == "Server":
            entry = self.currentDeck.pickacard()
            if entry <>"":
                PLAYERINSTANCE['Local'].addcard(entry)
            else:
                sm.get_screen('pinnacolabackground').info = "No more cards on Deck"
            if DEBUG: print 'Player 0 hand:',PLAYERINSTANCE['Local'].hand
            return self.putonscreen(entry)
        if GAMEMODE == "Client":
            self.climsg_pickacard()
        
    def putonscreen(self, entry, screen='pinnacolabackground', xi=200, yi=200, xf=300, yf=50):
        '''Show the picked card on proper screen and coordinates'''
        try:
            # load the image
            picture = Picture(source='atlas://decks/cards/%s' % entry[:-1], scale=0.7,do_rotation=False, x=xi , y=yi, card=entry)
            def picbind(dt,picture=picture):
                # helper function to bind on pos after an animation takes place
                picture.bind(pos=self.callback_pos)
            anim = Animation(x=xf, y=yf, scale=1)
            anim.start(picture)
            # binding to callback_pos after animation is completed
            Clock.schedule_once(picbind,2)
            # add to the main field
            sm.get_screen(screen).add_widget(picture)

        except Exception, e:
            Logger.exception('Pictures: Unable to load card %s from atlas' % entry )
        self.selcards = []
        return picture

    def attach(self, player):
        '''Add a card to on table cards to get more points'''
        def common(card):
            # helper function
            player.deletecard(card)
            player.addpoints(card)
            self.animation(card)
        # get selected card
        if len(self.selcards) == 1:
            cardtoattach = self.selcards[0]
            # find where to add
            for group in player.down:
                newgroup = group
                newgroup.append(cardtoattach)
                if self.check_if_valid(newgroup):
                    group = newgroup
                    common(cardtoattach)
                    break
                else:
                    newgroup = [cardtoattach]
                    newgroup.append(group)
                    if self.check_if_valid(newgroup):
                        print "Found", newgroup
                        group = newgroup
                        common(cardtoattach)
                        break
        else:
            #self.info.showinfo("Only attach a card at a time, please....")
            #refresh info
            sm.get_screen('pinnacolabackground').info = "Only attach a card at a time, please...."
        # TODO        
        # check if it works as expected in all situations

    def putontable(self,player):
        '''cancella dalla mano le carte calate in tavola'''
        screen = sm.get_screen('pinnacolabackground')
        screen.info = ""
        if DEBUG: print 'Put on table',self.selcards
        if len(self.selcards) >= 3:
            a=self.check_if_valid(self.selcards)
            if a:
                player.putdown(self.selcards)  # aggiorna carte scoperte
                for i in self.selcards:
                    player.deletecard(i)
                    self.animation(i)
                if GAMEMODE == "Client": self.climsg_dropped(self.selcards)
                if GAMEMODE == "Server": self.srvmsg_dropped(self.selcards)
            else:
                if DEBUG:print "Invalid"
                screen.info = "Invalid"
            self.unselectall()
            #refresh player's screen 
            screen.points = player.points
        else:
            screen.info = 'Select minimum 3 cards !!'
    
    def build_config(self, config):
        """create configuration file """
        config.add_section('section1')
        config.set('section1', 'max_cards', '13')
        config.set('section1','gamemode','Server')
        config.set('section1','name','')
        config.set('section1','serverip','')
        config.set('section1','intromusic','1')
        config.set('section1','language','en')

    def build_settings(self, settings):
        """create configuration pannel"""

        jsondata="""[
                {"type": "title",
                "title":"Config Pinnacola"},
                
                {"type": "string",
                "title": "Player Id",
                "desc": "Player name",
                "section":"section1",
                "key": "name"},
                
                {"type": "options",
                "title": "Start cards",
                "desc": "Number of cards in hand that we start with",
                "section":"section1",
                "key": "max_cards",
                "options": ["13","15"]},
                
                {"type": "options",
                "title": "Play mode",
                "desc": "Act as Server or client ",
                "section":"section1",
                "key": "gamemode",
                "options": ["Server","Client"]},
                
                {"type": "string",
                "title": "Server ip",
                "desc": "When playing as a client, this is the server ip address to connect to.",
                "section": "section1",
                "key": "serverip"},
                
                {"type": "bool",
                "title": "Intro music",
                "desc": "Play music in intro screen.",
                "section": "section1",
                "key": "intromusic"},
                
                {"type": "options",
                "title": "Language",
                "desc": "Choose your favourite language",
                "section":"section1",
                "key": "language",
                "options": ["en","it"]}
                   ]"""
                   
        settings.add_json_panel('Pinnacola',self.config, data=jsondata)

    def on_config_change(self, config, section, key, value):
        global SERVER, GAMEMODE, language
        if config is not self.config:
            return
        token = (section, key)
        if token == ('section1', 'max_cards'):
            self.max_cards = int(value)
        if token == ('section1', 'gamemode'):
            GAMEMODE = value
        if token == ('section1', 'serverip'):
            SERVER = value
            self.connect_to_server()
            #re-connect
        if token == ('section1','intromusic'):
            if value == "0":
                self.sound.stop()
            if value == "1":
                self.sound.loop = True
                self.sound.play()
            
        if token == ('section1','language'):
            language = value
            print language
            tr.switch_lang(language)    

    def callback_pos(self,instance,value):
        #se la carta viene trascinata nella discard zone allora viene scartata
        #se viene trascinata fuori dalla discard zone allora viene pescata
        def rebind(dt,inst=instance):
            #helper function to rebind to changes on pos after an animation
            inst.bind(pos=self.callback_pos)
        
        card=instance.card
        instance.selected='yes'

        if card not in self.selcards:
            self.selcards.append(card)
            print"Selected ",self.selcards
            instance.c=.2  #change property c ->color

        #scarta una carta nel pozzo    
        if value[1] > DISCARDY-30 and value[0] >200 and self.flag == 0 and instance.condition <> 'pit':
            if DEBUG:print 'Discarded', card
            self.currentDeck.put_ontable(card) #aggiunge al pozzo
            PLAYERINSTANCE['Local'].deletecard(card)  #toglie al giocatore
            instance.selected = 'no'
            instance.condition = 'pit'
            self.numDiscarded += 1
            self.flag = 1
            self.unselectall()
            #animazione
            anim = Animation(x=230+10*self.numDiscarded,y=DISCARDY, rotation=0,scale=0.7,t='out_back')
            # unbind to avoid triggering callback_pos
            instance.unbind(pos=self.callback_pos)
            anim.start(instance)
            # binding again to callback_pos after animation is completed
            Clock.schedule_once(rebind,2)
            if GAMEMODE == "Server":
                self.msg_sendontable(card) #inform clients 
            else:
                self.climsg_send("DISCARDED "+card) #inform server

            if DEBUG:
                print "Pit:" ,self.currentDeck.ontable 
                print "On Hand:",PLAYERINSTANCE['Local'].hand

        #pesca una carta fuori dal pozzo
        if instance.condition=='pit' and value[1] <200 and self.flag==0:
            if DEBUG: print'Picked up from pit',card
            PLAYERINSTANCE['Local'].addcard(card) #aggiunge al giocatore
            self.currentDeck.pick_fromtable(card) #toglie dal pozzo
            self.numDiscarded -=1 
            self.flag = 1
            instance.condition = ''
            #animazione
            anim = Animation(x=300 ,y=50 ,rotation=0,scale=1,t='out_back')
            anim.start(instance)
            if GAMEMODE == "Client":
                #inform server
                self.climsg_send("PICKPIT "+card)
            if GAMEMODE == "Server":
                #inform clients
                self.srvmsg_send("PICKPIT", card)

        if instance <> self.oldinstance:
            self.flag = 0

        # self.oldvalue=value[1]
        self.oldinstance = instance

    def callback_touch(self, instance, touch):
        ''' se la carta e toccata '''
        if touch.is_double_tap:
            if DEBUG: print 'Double tap'
            self.unselectall()
            return False



    def check_if_valid(self, cards):
        '''controlla se la calata di carte e valida'''
        valid = 0
        rightorder = "123456789101112131"
        leftorder ="113121110987654321"
        #cards=sorted(cards)
        tcards = ""
        pcards = []
        deleted = None
        if DEBUG: print "Checking",cards
        number = (cards[0][:-2])
        seed = (cards[0][:-1][-1])
        #print number,seed
        #work around for joker last in the list
        if cards[-1][:2][-2] == 'j' :  #last element is joker , delete from list to avoid problems
            deleted = cards[-1]
            del cards[-1]
            if DEBUG: print "last is joker, working around...."

         #check for same number   
        for card in cards:
            pcards.append(card[:-1])

            if card[:2][-2] != 'j' and card[:-2] != number :
                valid = 0
                break 
            else:
                valid = 1
                if deleted:
                    cards.append(deleted) # put back joker
                    deleted = None

        if len(pcards) != len(set(pcards)): #duplicate same number and same seed
            if DEBUG: print'Duplicate found'
            valid = 0

        if valid == 1:
            if DEBUG: print 'Same number'
            return valid

        #check for same seed
        oldcard = "100"
        for card in cards:

            replacement = ""
            for k in range(len(str(oldcard[:-2]))):
                replacement = replacement + "." 
            if oldcard[:-2] == '9':    # caso del jolly tra 9 e 11
                replacement = replacement+"."

            if (card[:-1][-1] == seed) or (card[:2][-2] == 'j'):
                tcards=tcards+str(card[:-2])
                tcards=tcards.replace('j', replacement)

            else:
                valid = 0
                return valid
            oldcard = card
        if DEBUG:
            print'Same seed'
            print tcards

        m = re.search(tcards, rightorder)
        if m:
            if m.group(0):
                valid=1
                if DEBUG: print "RE says it's valid!", m.group(0)

        m = re.search(tcards, leftorder) 
        if m:
            if m.group(0):
                valid=1
                if DEBUG: print "RE says it's valid!", m.group(0)

        return valid

    def unselectall(self):
        sm.get_screen('pinnacolabackground').info=""
        for child in sm.get_screen('pinnacolabackground').children:
            try:
                if child.card in self.selcards:
                    child.c = 1  # make border white
            except:
                pass
        self.selcards = []
        if DEBUG: print 'Unselected'

    def on_selected(self, *args):
        print 'selected', args

    def animation(self,i,screen='pinnacolabackground'):
        '''create animation for every card going on table'''
        for child in sm.get_screen(screen).children:
                        try:
                            if child.card == i:
                                # unbind callback_pos to avoid selection
                                # when moving because of the animation
                                child.unbind(pos=self.callback_pos)
                                anim = Animation(scale=0.6,t='out_back')
                                anim.start(child)
                                child.do_translation = False

                        except:
                            pass

    def destroy(self,card):
        root = sm.get_screen('pinnacolabackground')
        def destro(dt, item):
           sm.get_screen('pinnacolabackground').remove_widget(item)
        
        for child in sm.get_screen('pinnacolabackground').children:
            if child.card == card:
                #child.unbind(pos=self.callback_pos)
                anim = Animation(scale=1,t='out_back')
                anim.start(child)
                root.remove_widget(child)
                #shedule deletion after animation
                #Clock.schedule_once(partial(destro, child), 2)
                break

###############Server side routines#####################################
    def msg_sendontable(self,stat):
        '''inform clients which card is DISCARDED'''
        self.srvmsg_send("DISCARDED", stat)

    def msg_pickedfromtable(self,stat):
        #inform clients PICKED UP
        self.srvmsg_send("PICKED UP", stat)

    def srvmsg_dropped(self,cards):
        line = ""
        for card in cards:
            line += str(card)+"-"
        line = line +str(PLAYERINSTANCE['Local'].left)+"-"+self.playername
        self.srvmsg_send("DROPPED", line)  #spazio

    def srvmsg_send(self, header, msg):
        '''Server send message msg to all clients. 
            header is kind of message '''
        for n in NAMES:
            CONNECTION[n].sendLine(str(header)+" "+str(msg))

    def handle_CHAT(self, cla, message):

        if DEBUG: print "<%s> %s" % (cla.name, message)
        
        self.relay_message(cla.name, message) #relay messages to other players
        
        if message == "PICKDECK":
            CONNECTION[cla.name].sendLine('<DECK>'+str(self.currentDeck.pickacard()))

        if "PICKPIT" in message:
            print "Doing pickpit things..."
            card = message[8:]
            self.currentDeck.pick_fromtable(card) #toglie dal pozzo
            self.numDiscarded -=1
            self.destroy(card)
            #self.relay_message(cla.name, message) 
        
        if "DISCARDED" in message:
            self.numDiscarded += 1
            card = message[10:]
            self.currentDeck.put_ontable(card)
            self.show_pit(card, sm.get_screen('pinnacolabackground'))
            
        if "DROPPED" in message:
            #receive cards dropped and nr cards left in hand
            cards = message[8:].split('-')     #8
            if DEBUG: print"KKKK %s", cards
            self.syncplayer(cla.name,cards[:-1],int(cards[-1]))


    def relay_message(self, sender, msg):
        '''broadcast mesages to all clients but the original sender'''
        other = NAMES[:]
        other.remove(sender)
        for n in other:
            CONNECTION[n].sendLine(msg+"-"+sender)

############### Client side routines###################################
    def connect_to_server(self):
        reactor.connectTCP(SERVER, PORT, EchoFactory(self))

    def on_connection(self, connection):
        '''runs only once when connection with server is succesfull'''
        if DEBUG: print"connected succesfully with server!"
        sm.get_screen('intro').info = "Connected with server!"
        self.connection = connection
        # after connection wait message <INIT> then continue to play
        
    def climsg_dropped(self,cards):
        line = ""
        for card in cards:
            line += str(card)+"-"
        line = line +str(PLAYERINSTANCE['Local'].left) # nr cards remained
        self.climsg_send("DROPPED "+line)
    
    def climsg_sendontable(self, card):
        self.climsg_send("DISCARDED "+card)
        
    def climsg_pickpit(self, card):
        self.climsg_send("PICKPIT "+card)

    def climsg_pickacard(self):
        '''send a message to server asking a card from deck'''
        self.climsg_send("PICKDECK")

    def climsg_send(self, msg):
        '''In client mode send message to connected Server'''
        if msg and self.connection:
            self.connection.write(str(msg)+"\r\n")
        else:
            print'Server not found'

    def handle_message(self,msg):
        '''Handle (decode) messages/requests from clients
            <xxx> are answers to client questions
            xxx are spontaneous messages from server'''
        global PLAYERINSTANCE, NAMES
        if DEBUG: print "Message from server: %s" % msg

        
        if "Welcome" in msg:
            self.climsg_send(self.playername)
        elif "exceeded" in msg:
            if DEBUG: print "not accepted, too many clients"
            sm.get_screen('intro').info = "Too many clients!!" 
        elif "taken" in msg:
            if DEBUG: print "not accepted, id exists"
            sm.get_screen('intro').info = "Id taken already, change and try again."
        elif "<INIT>" in msg:
            cards = msg[6:].split('-')
            self.cards_server = cards[:-1]
            gamersname= cards[-1].split('#')
            self.servername= str(gamersname[0].rstrip())
            NAMES=gamersname[1:-2] #exclude the last name because it is the local player,
                                   # NAMES stores only the other players names without the server's name !! 
                                   
            
            if DEBUG: 
                print "Getting cards from server %s" % self.servername
                print "Players: %s %s" % (self.servername,NAMES)

            #create a new instance for server player 
            if not(PLAYERINSTANCE.has_key(self.servername)):
                PLAYERINSTANCE[self.servername]=Player(self.servername)
                
            # and a new instance for all previously connected players
            for na in NAMES:
                PLAYERINSTANCE[na]=Player(na) #da indicare la posizione!!
            
        
            
            ##now can continue to play after <INIT> is catched
            self.startplay(sm.get_screen('pinnacolabackground'))
        
        elif "DISCARDED" in msg:
            self.numDiscarded += 1
            if "-" in msg:
                tmp=msg.split('-')
                msg=tmp[0]
            card = msg[10:].rstrip()
            self.currentDeck.put_ontable(card)
            self.show_pit(card, sm.get_screen('pinnacolabackground'))
        elif "<DECK>" in msg:
            card = msg[6:-2]
            if card <>"":
                PLAYERINSTANCE['Local'].addcard(card)
                self.putonscreen(card)
            else:
                sm.get_screen('pinnacolabackground').info = "No more cards."
        elif "PICKPIT" in msg:
            # if the message is relayed from server get the original sender from the 
            # relayed message and stripp it off
            if "-" in msg:
                tmp=msg.split('-')
                msg=tmp[0]
                sender=tmp[1]
            self.numDiscarded -=1
            card = msg[8:].rstrip()
            self.currentDeck.pick_fromtable(card)
            self.destroy(card)
        elif "DROPPED" in msg:
            campi= msg[8:].split('-')  #9
            inhand = campi[-2]
            cards = campi[:-2]
            name = campi[-1].rstrip()
            i=0
            print "<"+name+">","DROPPED",cards,"left in hand",inhand
            self.syncplayer(name,cards,inhand)
        elif "NEWGAMER" in msg:
            #self.afterme = self.afterme + 1
            name = msg[9:].rstrip()
            # create new player instance
            if not(PLAYERINSTANCE.has_key(name)):
                PLAYERINSTANCE[name]=Player(name) ## da indicare in quale posizione
                NAMES.append(name)

    def syncplayer(self,name,cards='',inhand=''):
        '''syncronize datas on players screens'''
        global PLAYERINSTANCE
        if DEBUG:print "Screen %s assigned to %s player" %(PLAYERINSTANCE[name].screen, name)
        
        PLAYERINSTANCE[name].putdown(cards)
        PLAYERINSTANCE[name]._nr = int(inhand)
        i=0
        x= PLAYERINSTANCE[name].positions[PLAYERINSTANCE[name].pos]
        PLAYERINSTANCE[name].pos +=1
        if DEBUG:print "X:",x
        for card in cards:
            i +=1
            self.putonscreen(card,PLAYERINSTANCE[name].screen,100,100,x,180-(20*i))
            self.animation(card,PLAYERINSTANCE[name].screen)
        scr = sm.get_screen(PLAYERINSTANCE[name].screen)
        scr.points=PLAYERINSTANCE[name].points

    def status(self):
        '''Print on console local players' data'''
        print "Local player"
        print " : selected", self.selcards
        print " : on hand ", PLAYERINSTANCE['Local'].hand
        print " : down    ", PLAYERINSTANCE['Local'].down
        print " : points  ", PLAYERINSTANCE['Local'].points
        print " : nr cards", PLAYERINSTANCE['Local'].left
        print " : pit     ", self.currentDeck.ontable
        for n in NAMES:
            print " Player <%s>" % n
            print " : on hand ", PLAYERINSTANCE[n].hand
            print " : down    ", PLAYERINSTANCE[n].down
            print " : points  ", PLAYERINSTANCE[n].points
            print " : nr cards", PLAYERINSTANCE[n].left



class Info(Label):
    '''put some info on screen'''
    def __init__(self, root):
        self.layout = AnchorLayout(anchor_x='center', anchor_y='center')
        self.infotext = Label(text='Your turn, pick a card from Deck or Pit.')
        self.layout.add_widget(self.infotext)
        root.add_widget(self.layout)

    def showinfo(self, txt):
        self.layout.remove_widget(self.infotext)
        self.infotext = Label(text=txt)
        self.layout.add_widget(self.infotext)


###################Twisted Server implementation######################
class Chat(LineReceiver):
    global CONNECTION, PLAYERINSTANCE

    def __init__(self, users,app):
        self.users = users
        self.name = None
        self.state = "GETNAME"
        self.app=app
        
    def connectionMade(self):
        self.sendLine("Welcome to Pinnacola server. Set your id:")

    def connectionLost(self, reason):
        print "Connection lost with %s" %(self.name,)
        if self.users.has_key(self.name):
            del self.users[self.name]   # delete handle
            idx=NAMES.index(self.name)  
            NAMES.remove(self.name)     # delete id name
            #TODO: if you lost connection you probably wont continue playing....

    def pushMessage(self, msg):
        self.sendLine(str(msg))

    def lineReceived(self, line):
        if self.state == "GETNAME":
            if DEBUG: print"New client request: ", line
            self.handle_GETNAME(line)
        else:
            self.app.handle_CHAT(self, line) # linked to outside function
            #response = self.factory.app.handle_message(data)
            #if response:
            #    self.sendLine(response)

    def handle_GETNAME(self, name): 
        global CONNECTION, NAMES, DECKINSTANCE, max_cards, PLAYERINSTANCE
        
        def relay_name(dt,instance=self):
            # send gamer names to every one else
            tmp=NAMES[:]
            tmp.remove(self.name)
            newgamer=NAMES[-1]
            if DEBUG:
                print "Gamers: %s" % NAMES
                print "Newgamer: %s" % (newgamer,)
            for n in tmp:
                CONNECTION[n].sendLine('NEWGAMER %s' %(newgamer,))
            
        
        def delayed(dt,instance=self):
            instance.sendLine("DISCARDED "+ str(DECKINSTANCE.pit()[0]))
        
        if DEBUG:print "Connected users:",self.users
        
        
        if name in NAMES:
            self.sendLine("ID taken, please choose another.")
            return
        if len(NAMES) == 3:
            self.sendLine("Maximum clients number exceeded!")
            self.transport.loseConnection()
            return

        if DEBUG: print"Client %s accepted" % (name,)
        sm.get_screen('intro').info = "Client %s accepted" % (name,)
        self.name = name
        self.users[name]= self
        self.state = "CHAT"
        CONNECTION[name] = self  # link chat instances to global variable to be used outside
        NAMES.append(name)
        PLAYERINSTANCE[name] = Player(name) # create new player instance (server side)
        
        #refresh player screen name
        ##sm.get_screen(PLAYERINSTANCE[name].screen).gamer=name 
                

        message = ""
        for i in range(max_cards):
            message = message + str(Deck.pickacard(DECKINSTANCE))+ "-"
        gamersname= "#"
        for n in NAMES:
            gamersname = gamersname + str(n) +"#"
        #send init message with cards in hand, name of the server and other players
        self.sendLine('<INIT>'+str(message)+str(PLAYERINSTANCE['Local'].name)+str(gamersname))
        # delay 1 sec
        Clock.schedule_once(relay_name,1)
        #delay 1 sec
        Clock.schedule_once(delayed,2)
        
        
        
        


class ChatFactory(Factory):
    def __init__(self,app):
        self.users = {}  # maps user names to Chat instances
        self.app = app

    def buildProtocol(self, addr):
        return Chat(self.users, self.app)


#################### Twisted Client implementation########################
class EchoClient(protocol.Protocol):
    def connectionMade(self):
        #link to routines inside the main app
        self.factory.app.on_connection(self.transport)

    def dataReceived(self, data):
        #link to routines inside the main app
        self.factory.app.handle_message(data)


class EchoFactory(protocol.ClientFactory):
    protocol = EchoClient

    def __init__(self, app):
        self.app = app

    def clientConnectionLost(self, conn, reason):
        self.app.handle_message("connection lost")

    def clientConnectionFailed(self, conn, reason):
        self.app.handle_message("connection failed")
        sm.get_screen('intro').info = "Server not found!!" 


if __name__ == '__main__':
    #Parsing line flags
    # (to pass arguments to app use python main.py -- -C
    # inline flag overrides ini file)
    arguments = sys.argv
    if "-C" in arguments:
        GAMEMODE = "Client"
    elif "-S" in arguments:
        GAMEMODE = "Server"
    # Create the screen manager
    sm = ScreenManager()
    sm.add_widget(IntroScreen(name='intro'))
    sm.add_widget(RulesScreen(name='rules'))
    sm.add_widget(SettingsScreen(name='settings'))
    sm.add_widget(PinnacolaBackground(name='pinnacolabackground'))
    sm.add_widget(Player2Screen(name='player2'))
    sm.add_widget(Player3Screen(name='player3'))
    sm.add_widget(Player4Screen(name='player4'))
    # put some info about gamemode on intro screen
    sm.get_screen('intro').info = " %s mode: connecting" %GAMEMODE
    #run application
    PinnacolaApp().run()
