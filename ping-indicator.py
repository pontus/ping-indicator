#!/usr/bin/env python
#
# Simple indicator to show network connectivity by pinging a host.
#
# Built upon example code at <http://conjurecode.com/create-indicator-applet-for-ubuntu-unity-with-python/>
#


import sys
import gtk
import appindicator
import string
import subprocess
import os.path
import gobject
import ConfigParser

class PingChecker:
    def __init__(self):

        self.find_icons()

        self.ind = appindicator.Indicator("ping-indicator",
                                           self.path+"/ping-indicator-connected.svg",
                                           appindicator.CATEGORY_COMMUNICATIONS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_attention_icon(self.path+"/ping-indicator-no-connection.svg")


        self.read_config()


        self.menu_setup()
        self.ind.set_menu(self.menu)

    def read_config(self):
        # Set up some reasonable defaults


        cfg = ConfigParser.SafeConfigParser()


        self.freq = 10
        self.host = "www.google.com"
        self.maxtime = 3
        self.ipv6 = False
        

        cfg.read( ('.ping-indicator.cfg', os.environ.setdefault('HOME','/tmp/nosuch')+'/.ping-indicator.cfg'))

        if 'Ping indicator' in cfg.sections():
            for (k,v) in cfg.items('Ping indicator'):
                if k == 'delay':
                    self.freq = int(v)
                if k == 'host':
                    self.host = v
                if k == 'timeout':
                    self.maxtime = int(v)
                if k == 'ipv6':
                    self.ipv6 = False
                    if v.lower() == 'true':
                        self.ipv6 = True

        
    def write_config(self):
        cfg = ConfigParser.SafeConfigParser()

        cfg.add_section('Ping indicator')
        cfg.set('Ping indicator','delay', str(self.freq))
        cfg.set('Ping indicator','timeout', str(self.maxtime))
        cfg.set('Ping indicator','host', self.host)
        cfg.set('Ping indicator','ipv6', str(self.ipv6))

        f = open( os.environ.setdefault('HOME','/tmp/nosuch')+'/.ping-indicator.cfg','w')
        cfg.write(f)
        f.close()

    def menu_setup(self):
        self.menu = gtk.Menu()

        self.conf_item = gtk.MenuItem("Configure")
        self.conf_item.connect("activate", self.conf)
        self.conf_item.show()
        self.menu.append(self.conf_item)

        self.quit_item = gtk.MenuItem("Quit")
        self.quit_item.connect("activate", self.quit)
        self.quit_item.show()
        self.menu.append(self.quit_item)



    def main(self):
        # Main loop function, defer to gtk
        self.do_ping()

        self.current_to = gtk.timeout_add(self.freq * 1000, self.do_ping)
        gtk.main()

    def quit(self, widget):
        sys.exit(0)

    def conf(self,widget):
        # Configuration dialog

        c = gtk.Dialog('Configure ping-indicator')

        l = gtk.Label("Ping indicator configuration")
        c.vbox.pack_start(l)
        l.show()
   
        ipv6 = gtk.CheckButton("IPv6")
        ipv6.set_active(self.ipv6)

        c.vbox.pack_end(ipv6)
        ipv6.show()


        hostline = gtk.HBox()
        hostlabel = gtk.Label("Host: ")
        hostline.pack_start(hostlabel)
        hostlabel.show()

        host = gtk.Entry(max=900)
        host.set_text(self.host)
        hostline.pack_start(host)
        host.show()

        c.vbox.pack_start(hostline)
        hostline.show()

        class NEntry(gtk.Entry):
            # Numeric entry class, see <http://stackoverflow.com/questions/5159219/how-can-i-filter-or-limit-the-text-being-entered-in-a-pygtk-text-entry-field>
            def __init__(self):
                gtk.Entry.__init__(self,4)
                self.connect('insert_text', self.do_insert_text)

            def do_insert_text(self,ent,text,length,pos):
                s = [x for x in text if x in string.digits]

                if (s):
                    ent.handler_block_by_func(self.do_insert_text)
                    ent.insert_text(string.join(s,''), ent.get_position())
                    ent.handler_unblock_by_func(self.do_insert_text)                  
                    
                    gobject.idle_add(ent.set_position, ent.get_position()+len(s) )

                ent.stop_emission("insert_text")

        freqline = gtk.HBox()
        freqlabel = gtk.Label("Ping every ")
        freqline.pack_start(freqlabel)
        freqlabel.show()

        freq = NEntry()
        freq.set_text(str(self.freq))
        freqline.pack_start(freq)
        freq.show()

        c.vbox.pack_start(freqline)
        frseclabel = gtk.Label("seconds")
        freqline.pack_start(frseclabel)
        frseclabel.show()

        freqline.show()


        waitline = gtk.HBox()
        waitlabel = gtk.Label("Timeout after ")
        waitline.pack_start(waitlabel)
        waitlabel.show()

        wait = NEntry()
        wait.set_text(str(self.maxtime))
        waitline.pack_start(wait)
        wait.show()

        waseclabel = gtk.Label("seconds")
        waitline.pack_start(waseclabel)
        waseclabel.show()

        c.vbox.pack_start(waitline)
        waitline.show()




        c.action_area
        host.show()

        c.add_button(gtk.STOCK_OK, 1)
        c.add_button(gtk.STOCK_CANCEL, 2)
        c.set_default_response(1)

        c.show()

        dorun = True
        
        while dorun:
            
            c.set_focus(None)
            dorun = False
            r = c.run()

            if r == 1 and int(freq.get_text()) < int(wait.get_text())+1:
                print "Dum!"

                a = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,buttons=gtk.BUTTONS_OK)
                a.set_markup("The delay between pings needs to be greater than the timeout and an additional seconds!")
                a.show()
                a.run()
                a.destroy()
                dorun = True
            

        if r == 1:
            self.host = host.get_text()
            self.freq = int(freq.get_text())
            self.maxtime = int(wait.get_text())
            self.ipv6 = ipv6.get_active()

        c.destroy()

        gtk.timeout_remove(self.current_to)
        self.current_to = gtk.timeout_add(self.freq * 1000, self.do_ping)
        self.write_config()
        self.do_ping()
        return

    def do_ping(self):
        
        f=open('/dev/null','w')

        cmd = 'ping'
        
        if self.ipv6:
            cmd = 'ping6'

        connected = subprocess.call([cmd, '-n', '-w', str(self.maxtime), '-c', '1', self.host], stdout=f.fileno(), stderr=f.fileno())
        f.close()

        if connected > 0:
            self.ind.set_status(appindicator.STATUS_ATTENTION)
        else:
            self.ind.set_status(appindicator.STATUS_ACTIVE)
        return True

    def find_icons(self):
        if os.path.exists("ping-indicator-no-connection.svg"):
            self.path = os.path.realpath(".")
            return
        if os.path.exists(os.path.dirname(sys.argv[0])+"/ping-indicator-no-connection.svg"):
            self.path = os.path.realpath(os.path.dirname(sys.argv[0]))
            return

        raise SystemExit("Found no icons.")

if __name__ == "__main__":
    indicator = PingChecker()
    indicator.main()
