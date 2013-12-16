#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Pinnacola        Copyright (c) 2013  by Robby Cerantola
=======================================

This is a basic pinnacola cards game, using the scatter widget.

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

__version__ = '0.5'
#v 0.0 deck, userinterface
#v 0.1 simple net messages (Twisted), server only
#v 0.2 implement screen manager
#v 0.3 registra le carte calate
#v 0.4 multiple screens
#v 0.5 cleaning  code

import kivy
kivy.require('1.1.2')

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
from kivy.properties import StringProperty, ObjectProperty, NumericProperty
from kivy.atlas import Atlas
from kivy.animation import Animation
# FIXME this shouldn't be necessary
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.anchorlayout import AnchorLayout
from kivy.lang import Builder
from kivy.core.audio import SoundLoader

import random
import re

# set to 1 to get extra debug info
DEBUG = 1

PLAYERS = 4
DISCARDY = 250
CONNECTION = {}
NAMES = []
DECKINSTANCE = None
PLAYERINSTANCE = None
SELCARDS = []





#:PEP8 -W293

# BUG?!? Cannot put this on external kv file:
# screen manager seems to work only with inline statements!!
Builder.load_string("""
#:kivy 1.0
#:import kivy kivy
#:import win kivy.core.window

<Picture>:
    # each time a picture is created, the image can delay the loading
    # as soon as the image is loaded, ensure that the center is changed
    # to the center of the screen.
    on_size: self.center = win.Window.center
    size: image.size
    size_hint: None, None

    Image:
        id: image
        source: root.source

        # create initial image to be 84x122 pixels
        size: 84, 122 #/ self.image_ratio

        # add shadow background
        canvas.before:
            Color:
                rgba: 1,root.c,root.c,.8
            BorderImage:
                
                source: 'shadow32b.png'
                border: (33,33,33,33)
                size:(self.width+66, self.height+66)
                pos: (-33,-33)


<IntroScreen>:
    canvas:
        Rectangle:
            source: 'pinnacolook.jpg'
            size: self.size
    
    BoxLayout:
        #padding: 10
        #spacing: 10
        #height: 44
        size_hint: 1, None
        Button:
            background_color: (1,1,1,.5)
            text: 'Goto settings'
            on_press: app.open_settings(self)
        Button:
            background_color: (1,1,1,.5)
            text: 'Play game'
            on_press: root.manager.current = 'pinnacolabackground'; app.sound.stop()
        Button:
            background_color: (1,1,1,.5)
            text: 'Rules of game'
            on_press: root.manager.current = 'rules'
    BoxLayout:
        Label:
            color: (0,0,0,1)
            text: 'Pinnacola v %s (c) 2013 by Robby Cerantola' % root.ver
        
<RulesScreen>:
    canvas:
        Rectangle:
            source: 'pinnacolook.jpg'
            size: self.size
    BoxLayout:
        orientation: "vertical"
        #size_hint: None, 1
        ScrollView:
            TextInput:
                color: (0,0,0,1)
                background_color: (1,1,1,.6)
                text: root.rulestxt
        Button:
            size_hint: 1, 0.1
            pos_hint: { 0.5: "center_x" }
            background_color: (1,1,1,.5)
            text: 'Play game'
            on_press: root.manager.current = 'pinnacolabackground'; app.sound.stop()

<SettingsScreen>:
    BoxLayout:
        Button:
            text: 'My settings button'
        Button:
            text: 'Back to menu'
            on_press: root.manager.current = 'intro'

<Player2Screen>
    canvas:
        Color:
            rgb: 1, 1, 1
        Rectangle:
            source: 'CardTable.png'
            size: self.size
    FloatLayout:
        Label:
            text: 'Player 2 name'
        
        Button:
            background_color: (1,1,1,.5)
            text: 'Back'
            pos: 1,20
            size_hint: .2,.2
            on_press:root.manager.current = 'pinnacolabackground'

        Button:
            background_color: (1,1,1,.5)
            text: 'Player 3'
            pos: 1,200
            size_hint: .2,.2
            on_press:root.manager.current = 'player3'
        Button:
            background_color: (1,1,1,.5)
            text: 'Player 4'
            pos: 200,20
            size_hint: .2,.2
            on_press:root.manager.current = 'player4'

<Player3Screen>
    canvas:
        Color:
            rgb: 1, 1, 1
        Rectangle:
            source: 'CardTable.png'
            size: self.size
    FloatLayout:
        Label:
            text: 'Player 3 name'
        
        Button:
            background_color: (1,1,1,.5)
            text: 'Back'
            pos: 1,20
            size_hint: .2,.2
            on_press:root.manager.current = 'pinnacolabackground'

        Button:
            background_color: (1,1,1,.5)
            text: 'Player 2'
            pos: 200,20
            size_hint: .2,.2
            on_press:root.manager.current = 'player2'
        Button:
            background_color: (1,1,1,.5)
            text: 'Player 4'
            pos: 100,100
            size_hint: .2,.2
            on_press:root.manager.current = 'player4'

<Player4Screen>
    canvas:
        Color:
            rgb: 1, 1, 1
        Rectangle:
            source: 'CardTable.png'
            size: self.size
    FloatLayout:
        Label:
            text: 'Player 4 name'
        
        Button:
            background_color: (1,1,1,.5)
            text: 'Back'
            pos: 1,20
            size_hint: .2,.2
            on_press:root.manager.current = 'pinnacolabackground'

        Button:
            background_color: (1,1,1,.5)
            text: 'Player 2'
            pos: 1,20
            size_hint: .2,.2
            on_press:root.manager.current = 'player2'
        Button:
            background_color: (1,1,1,.5)
            text: 'Player 3'
            pos: 50,20
            size_hint: .2,.2
            on_press:root.manager.current = 'player3'

<PinnacolaBackground>:
    canvas:
        Color:
            rgb: 1, 1, 1
        Rectangle:
            source: 'CardTable.png'
            size: self.size
        
        Color:
            rgb: 0, 1, 0
        Rectangle:
            source: 'discardzone.png'
            pos: 250,245
            size: 400,80
        
    Button:
        text: 'Pick me!'
        background_normal: 'atlas://decks/cards/br'
        #pos: 175, 250
        pos_hint: {'x': .2,'y':.5}
        size_hint: None, None
        height: dp(90)
        width: dp(60)
        on_press:app.showcard()
        
    BoxLayout:
        padding: 10
        spacing: 10
        size_hint: 1, None
        pos_hint: {'top': 1}
        height: 44
        Image:
            size_hint: None, None
            size: 24, 24
            source: 'data/logo/kivy-icon-24.png'
        Label:
            height: 24
            #text_size: self.size
            color: (.5, .5, .5, .8)
            text: 'Pinnacola %s ' % root.ver
            valign: 'bottom'

        
        Button:
            text: 'Put down'
            on_press:app.putontable(app.player[0])
        Button:
            text: 'Unselect'
            on_press:app.unselectall()
        Button:
            text: 'Attach'
            on_press:app.attach(app.player[0])
        Button:
            text: 'Status'
            on_press:app.status()
            
    FloatLayout:
        Button:
            #background_color: (1,1,1,1)
            background_normal: 'decks/backcards.png'
            text: '4'
            pos_hint: {'x': .8,'y': .5}
            #size_hint: .2,.2
            size_hint: None, None
            height: dp(80)
            width: dp(100)
            on_press:root.manager.current = 'player4'
        Button:
            #background_color: (1,1,1,.5)
            background_normal: 'decks/backcards.png'
            text: '2'
            pos_hint: {'x': .0,'y':.5}
            #pos_hint: {'center_y':1}
            #size_hint: .2,.2
            size_hint: None, None
            height: dp(80)
            width: dp(100)
            on_press:root.manager.current = 'player2'
        Button:
            #background_color: (1,1,1,.5)
            background_normal: 'decks/backcards.png'
            text: '3'
            pos_hint: {'x': .4,'y':.7}
            #size_hint: .2,.2
            size_hint: None, None
            height: dp(80)
            width: dp(100)
            on_press:root.manager.current = 'player3'

""")


class Deck():
    '''Create cards' deck in memory using the following convention:
        1 to 13 number of card, and f for flower p for  q for  and
         c for harts 0-1.. number of deck.
        Manage the metods to use the deck
    '''
    #assign to every card some points
    points_table = {'1': 15, '2': 5, '3': 5, '4': 5, '5': 5, '6': 5, '7': 10,
    '8': 10, '9': 10, '10': 10, '11': 10, '12': 10, '13': 10, 'j': 30}

    def __init__(self, n_mazzi=1):
        '''initialize the cards deck'''
        self.n_mazzi = n_mazzi
        self.deck = []
        self.ontable = []
        semi = ['q', 'c', 'p', 'f']
        
        for volte in range(self.n_mazzi):  # how many decks are used
            for a in semi:
                for i in range(1, 14):
                    tmp = '%s%s%s' % (i, a, volte)    
                    #print tmp
                    self.deck.append(tmp)
            self.deck.extend(['jr%s' % (volte), 'jn%s' % (volte)])  # add jokers     
            
        self.shufflecards()
        #if DEBUG: print self.deck

    def shufflecards(self):
        '''Shuffle the cards in the deck'''
        random.shuffle(self.deck)

    def pickacard(self):
        '''Get a card randomly from deck'''
        sel = random.choice(self.deck)
        self.deck.remove(sel)
        return sel

    def allcards(self):
        '''return all the cards in the deck'''
        return self.deck

    def cardsontable(self):
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
            print 'Some error, card you wish to remove is not on table'

    def value(self,card):
        return card[:-1]
    
    def number(self,card):
        return card[:-2]
        
    def seed(self,card):
        return card[:-1][-1]

class Player():
    def __init__(self):
        self.hand = []
        self.down = []
        self.points = 0

    def countcards(self):
        return len(self.hand)

    def addcard(self, card):
        self.hand.append(card)

    def deletecard(self, card):
        try:
            self.hand.remove(card)
        except:
            print 'Some error, card you wish to remove is not in player\
                    hand, not removing again.'

    def playcard(self, card):
        self.hand.remove(card)

    def hand(self):
        return self.hand
        
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
        #Info.showpoints()



class Picture(Scatter):
    '''Picture is the class that will show the cards with a white border and a
    shadow. There are nothing here because almost everything is inside the
    pinnacola. kv. Check the rule named <Picture> inside the file, and you'll
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

    def __init__(self, **kwargs):
        super(PinnacolaBackground, self).__init__(**kwargs)


class IntroScreen(Screen):
    ver = __version__


class RulesScreen(Screen):
    '''Introduzione al gioco'''
    import codecs
        #load rules text
    try:
        with codecs.open("rules.txt", "r", encoding="utf8") as myfile:
            rulestxt = "".join(line for line in myfile)
    except EnvironmentError:
        rulestxt = "Rules file not found !"


#class MainScreen(Screen):
#    pass


class SettingsScreen(Screen):
    pass


class Player2Screen(Screen):
    pass


class Player3Screen(Screen):
    pass


class Player4Screen(Screen):
    pass


# Create the screen manager
sm = ScreenManager()
sm.add_widget(IntroScreen(name='intro'))
sm.add_widget(RulesScreen(name='rules'))
sm.add_widget(SettingsScreen(name='settings'))
sm.add_widget(PinnacolaBackground(name='pinnacolabackground'))
sm.add_widget(Player2Screen(name='player2'))
sm.add_widget(Player3Screen(name='player3'))
sm.add_widget(Player4Screen(name='player4'))


class PinnacolaApp(App):
    #icon='pinnaicon.png'  #define icon
    #title='Titolo' #define title
    player = {}
    connection = None
    picture = None
    # cards currently selected
    selcards = []
    sound = SoundLoader.load('./music/intro.wav')
    if sound:
        sound.loop = True
        sound.play()

    def build(self):
        global max_cards
        #load configurations from ini file
        config = self.config
        max_cards = int(config.get('section1', 'max_cards'))
        gamemode = config.get('section1', 'gamemode')
        self.gamemode = gamemode
        # card y position and discarded flag
        self.numDiscarded = self.oldvalue = self.flag = 0
        self.oldinstance = None

        if gamemode == "Server":
            # start server
            reactor.listenTCP(8123, ChatFactory(self))
            if DEBUG: print "server started\n"

        root = sm.get_screen('pinnacolabackground')
        self.startplay(sm.get_screen('pinnacolabackground'))
        return sm

    def startplay(self, root):
        '''Prepare game'''
        global DECKINSTANCE, PLAYERINSTANCE
        #create instance for current deck
        DECKINSTANCE = self.currentDeck = Deck(2)  # use 2 decks of 52 cards

        #create instance for local player and display cards on hand
        PLAYERINSTANCE = self.player[0] = Player()

        #disposition of cards
        cy = [50, 53, 55, 60, 70, 75, 80, 85, 80, 75, 70, 60, 55, 53, 50]
        cx = 0
        rot = 0

        for i in range(max_cards):
            entry = self.currentDeck.pickacard()
            cx = cx + 25
            
            self.player[0].addcard(entry)
            try:
                # load the image
                picture = Picture(source='atlas://decks/cards/%s' % entry[:-1], rotation=int(rot), x=200+cx , y=cy[i]-120, card=entry)
                
            except Exception, e:
                Logger.exception('Pictures: Unable to load card %s from atlas' % entry[:-1] )
            
            picture.bind(pos=self.callback_pos)
            picture.bind(on_touch_down=self.callback_touch)
            # add to the main field
            root.add_widget(picture)
        
        self.info = Info(root)  # initialize info and connect to root widget
        if DEBUG:
            print 'Player 0 hand', self.player[0].hand
            print "gamemode:", self.gamemode
        #Put first card in the pit
        if self.gamemode == "Server":
            entry = self.currentDeck.pickacard()
            self.currentDeck.put_ontable(entry)
            try:
                # load the image
                picture = Picture(source='atlas://decks/cards/%s' % entry[:-1], rotation=int(rot), x=230 , y=DISCARDY,scale=.7, card=entry, condition='pit')
                
            except Exception, e:
                Logger.exception('Pictures: Unable to load card %s from atlas' % entry[:-1] )
            
            picture.bind(pos=self.callback_pos)
            picture.bind(on_touch_down=self.callback_touch)
            root.add_widget(picture)

    def on_pause(self):
        return True

    def on_start(self):
        pass
        #App.open_settings(self)
        #sm.current = 'startscreen'

    def buttontest(self):
        print 'Button test', self.picture

    def changecolor(self):
        self.picture.c = 1

    def showcard(self, stat=0):
        """pick a card from deck and show on table"""
        entry = self.currentDeck.pickacard()
        if DEBUG: print entry, stat
        ##self.i += 1
        try:
            # load the image
            picture = Picture(source='atlas://decks/cards/%s' % entry[:-1], scale=0.7,do_rotation=False, x=200 , y=200, card=entry)
            anim = Animation(x=300, y=50, scale=1)
            anim.start(picture)
            picture.bind(pos=self.callback_pos)
            # add to the main field
            sm.get_screen('pinnacolabackground').add_widget(picture)
            #self.root.add_widget(picture)
            self.player[0].addcard(entry)
            if DEBUG: print 'Player 0 hand:',self.player[0].hand
        except Exception, e:
            Logger.exception('Pictures: Unable to load card %s from atlas' % entry )
        self.selcards = []
        return picture

    def msg_sendontable(self,stat):
        '''inform clients which card is DISCARDED'''
        for n in NAMES:
            CONNECTION[n].sendLine("DISCARDED %s" % stat)

    def msg_pickedfromtable(self,stat):
        #inform clients PICKED UP
        for n in NAMES:
            CONNECTION[n].sendLine("PICKED UP %s" % stat)            

    def on_connection(self, connection):
        self.print_message("connected succesfully!")
        self.connection = connection

    def build_config(self, config):
        """create configuration file """
        config.add_section('section1')
        config.set('section1', 'max_cards', '13')
        config.set('section1','gamemode','Server')
        config.set('section1','name','')

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
                "options": ["Server","Client"]}
                   ]"""
        settings.add_json_panel('Pinnacola',self.config, data=jsondata)

    def on_config_change(self, config, section, key, value):
        if config is not self.config:
            return
        token = (section, key)
        if token == ('section1', 'max_cards'):
            self.max_cards = int(value)
        if token == ('section1', 'gamemode'):
            self.gamemode = value     

    def callback_pos(self,instance,value):
        #se la carta viene trascinata nella discard zone allora viene scartata
        #se viene trascinata fuori dalla discard zone allora viene pescata
        card=instance.card
        instance.selected='yes'
        self.info.showinfo('') #clear info
        if card not in self.selcards:
            self.selcards.append(card)
            print"Selected ",self.selcards
            instance.c=.2  #change property c ->color

        #scarta una carta nel pozzo    
        if value[1] > DISCARDY-30 and value[0] >200 and self.flag==0 and instance.condition <>'pit':
            if DEBUG:print 'Discarded', card
            self.currentDeck.put_ontable(card) #aggiunge al pozzo
            self.player[0].deletecard(card)  #toglie al giocatore
            instance.selected='no'
            instance.condition='pit'
            self.numDiscarded += 1
            self.flag=1
            #animazione
            anim = Animation(x=230+10*self.numDiscarded,y=DISCARDY, rotation=0,scale=0.7,t='out_back')
            anim.start(instance)
            self.msg_sendontable(card) #informa i client 

            if DEBUG:print "Pit:" ,self.currentDeck.ontable 
            if DEBUG:print "On Hand:",self.player[0].hand

        #pesca una carta fuori dal pozzo
        if instance.condition=='pit' and value[1] <200 and self.flag==0:
            if DEBUG:print'Picked up from pit',card
            self.player[0].addcard(card) #aggiunge al giocatore
            self.currentDeck.pick_fromtable(card) #toglie dal pozzo
            self.numDiscarded -=1 
            self.flag = 1
            instance.condition = ''
            #animazione
            anim = Animation(x=300 ,y=50 ,rotation=0,scale=1,t='out_back')
            anim.start(instance)
            #TODO informa i clients
            #self.msg_pickedfromtable(card)

        if instance <> self.oldinstance:
            self.flag = 0

        # self.oldvalue=value[1]
        self.oldinstance = instance

    def putontable(self,player):
        '''cancella dalla mano le carte calate in tavola'''
        if DEBUG: print 'Put on table',self.selcards
        if len(self.selcards) >= 3:
            a=self.check_if_valid(self.selcards)
            if a:
                player.putdown(self.selcards)  # aggiorna carte scoperte
                for i in self.selcards:
                    player.deletecard(i)
                    self.animation(i)
            else:
                self.info.showinfo('Invalid!!')
            self.unselectall();print "unselect all by putontable()"
            self.info.showpoints()
        else:
            self.info.showinfo('Select minimum 3 cards !!')


    def check_if_valid(self, cards):
        '''controlla se la calata di carte e valida'''
        valid = 0
        rightorder = "123456789101112131"
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
            print "last is joker, working around...."

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

        m=re.search(tcards, rightorder)
        if m:
            if m.group(0):
                valid=1
                if DEBUG: print "RE says it's valid!", m.group(0)

        return valid

    def unselectall(self):
        for child in sm.get_screen('pinnacolabackground').children:
            try:
                if child.card in self.selcards:
                    child.c = 1  # make border white
            except:
                pass
        self.selcards = []
        if DEBUG: print 'Unselected'

    def callback_touch(self, instance, touch):
        ''' se la carta e toccata '''
        if touch.is_double_tap:
            if DEBUG: print 'Double tap'
            self.unselectall()

        #print instance,touch,instance.card,instance.condition

    def on_selected(self, *args):
        print 'selected', args

    def animation(self,i):
        '''create animation for every card going on table'''
        for child in sm.get_screen('pinnacolabackground').children:
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

    def attach(self, player):
        '''Add a card to on table cards to get more points'''
        # get selected card
        if len(self.selcards) == 1:
            cardtoattach = self.selcards[0]
            # find where to add
            for group in player.down:
                newgroup = group
                newgroup.append(cardtoattach)
                if self.check_if_valid(newgroup):
                    print "Found", newgroup
                    group = newgroup
                    player.deletecard(cardtoattach)
                    player.addpoints(cardtoattach)
                    self.animation(cardtoattach)
                    break
                else:
                    newgroup = [cardtoattach]
                    newgroup.append(group)
                    if self.check_if_valid(newgroup):
                        print "Found", newgroup
                        group = newgroup
                        player.deletecard(cardtoattach)
                        player.addpoints(cardtoattach)
                        self.animation(cardtoattach)
                        break

        else:
            print "Only attach a card at a time, please...."
        # TODO        
        # check if it works as expected in all situations

    def handle_message(self, msg):
        if DEBUG: print 'received message', msg
        if msg == "getcards-player1": msg = str(self.player[1].hand)
        if msg == "pickcard-player1": msg = str(self.currentDeck.pickacard())
        if msg == "ping": msg = "pong"
        if msg == "plop": msg = "kivy rocks"
        return msg

    def send_message(self, msg):
        if msg and self.connection:
            self.connection.write(str("paperino"))

    def status(self):
        '''Print on console data'''
        print "STATUS: selected", self.selcards
        print "      : on hand ", self.player[0].hand
        print "      : down    ", self.player[0].down
        print "      : points  ", self.player[0].points
        print "      : pit     ", self.currentDeck.ontable

class Info(Label):
    '''put some info on screen'''
    def __init__(self, root):
        self.layout = AnchorLayout(anchor_x='center', anchor_y='center')
        self.infotext = Label(text='Your turn, pick a card from Deck or Pit.')
        self.layout.add_widget(self.infotext)
        root.add_widget(self.layout)
        self.layout2 = FloatLayout()
        self.pointstext = Label(text='Points:0', pos=(200,10))
        self.layout2.add_widget(self.pointstext)
        root.add_widget(self.layout2)

    def showinfo(self, txt):
        self.layout.remove_widget(self.infotext)
        self.infotext = Label(text=txt)
        self.layout.add_widget(self.infotext)
        
    def showpoints(self):
        txt = 'Points:' + (str(PLAYERINSTANCE.points))
        self.layout2.remove_widget(self.pointstext)
        self.pointstext = Label(text=txt)
        self.layout2.add_widget(self.pointstext)

###SERVER for picking  a card####
class EchoProtocol(protocol.Protocol):
    def dataReceived(self, data):
        response = self.factory.app.handle_message(data)
        if response:
            self.transport.write(response)


class EchoFactory(protocol.Factory):
    protocol = EchoProtocol

    def __init__(self, app):
        self.app = app


#####chat server implementation
class Chat(LineReceiver):
    global CONNECTION

    def __init__(self, users):
        self.users = users
        self.name = None
        self.state = "GETNAME"

    def connectionMade(self):
        self.sendLine("Pinnacola client id?")

    def connectionLost(self, reason):
        if self.users.has_key(self.name):
            del self.users[self.name]

    def pushMessage(self, msg):
        self.sendLine(str(msg))

    def lineReceived(self, line):
        if self.state == "GETNAME":
            self.handle_GETNAME(line)
        else:
            self.handle_CHAT(line)
            #response = self.factory.app.handle_message(data)
            #if response:
            #    self.sendLine(response)

    def handle_GETNAME(self, name):
        global CONNECTION, NAMES, DECKINSTANCE, max_cards
        if self.users.has_key(name):
            self.sendLine("ID taken, please choose another.")
            return
        if len(NAMES) == 3:
            self.sendLine("Maximum clients number exceeded!")
            self.transport.loseConnection()
            return

        self.sendLine("Client %s accepted" % (name,))
        self.name = name
        self.users[name] = self
        self.state = "CHAT"
        CONNECTION[name] = self  # link chat instances to global variable to be used outside
        NAMES.append(name)
        message = []
        print max_cards
        for i in range(max_cards):
            message.append(Deck.pickacard(DECKINSTANCE))

        self.sendLine(str(message))

    def handle_CHAT(self, message):
        global DECKINSTANCE

        if message == "PICKDECK":

            self.sendLine(str(Deck.pickacard(DECKINSTANCE)))
        message = "<%s> %s" % (self.name, message)
        print message
        for name, protocol in self.users.iteritems():
            if protocol != self:
                self.sendLine(message)


class ChatFactory(Factory):
    def __init__(self, app):
        self.users = {}  # maps user names to Chat instances
        self.app = app

    def buildProtocol(self, addr):
        return Chat(self.users)
############


if __name__ == '__main__':
    PinnacolaApp().run()
