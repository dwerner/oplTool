#!/usr/bin/env python

import wx, struct, os, re, subprocess
from wx import xrc

class MainWindow(wx.App):
    
    def OnInit(self, redirect=False, filename=None):
        self.read_ini()
        self.res = xrc.XmlResource("xrc/noname.xrc")
        self.InitFrame()
        return True
        
    def InitFrame(self):
        self.frame = self.res.LoadFrame(None, 'frame')
        self.game_info_group = {}
        
        game_info_group_list = [ 'game_name_static',  'game_name_textctrl',
                                 'max_char_static',   'size_static',
                                 'size_amount_static','part_static',
                                 'part_amount_static','rename_button', 'delete_button',
                                 'media_static', 'media_type_static']
                                
        for item in game_info_group_list:
            self.game_info_group[item] = xrc.XRCCTRL(self.frame, item)
        
        self.load_cfg_button = xrc.XRCCTRL(self.frame, 'load_cfg_button')
        self.quit_button = xrc.XRCCTRL(self.frame, 'quit_button')

        self.current_config_static = xrc.XRCCTRL(self.frame, 'current_config_static')
	
        #Installed Games section
        self.InstalledGamesSizer = xrc.XRCCTRL(self.frame, 'InstalledGamesSizer') # parent
        self.game_list_control = xrc.XRCCTRL(self.frame, 'game_list_control')
        self.game_list_control.Clear()
        #self.progress_bar = xrc.XRCCTRL(self.frame, 'progress_bar')
        
        # -- callbacks
        # Menus
        self.frame.Bind(wx.EVT_MENU, self.quit_app, id=xrc.XRCID('mitem_file_quit'))
        self.frame.Bind(wx.EVT_MENU, self.load_cfg_dialog, id=xrc.XRCID('mitem_file_open') )
        self.frame.Bind(wx.EVT_MENU, self.pref_dialog, id=xrc.XRCID('mitem_edit_prefs'))
        #get the last cfg file opened, and reopen it, if there is one
        
        self.game_list_control.Bind(wx.EVT_LISTBOX, self.load_game_info, self.game_list_control)

        # Button callbacks
        self.frame.Bind(wx.EVT_BUTTON, self.quit_app, self.quit_button )
        self.frame.Bind(wx.EVT_BUTTON, self.load_cfg_dialog, self.load_cfg_button)
        self.frame.Bind(wx.EVT_BUTTON, self.rename_game_button, self.game_info_group['rename_button'])
        self.frame.Bind(wx.EVT_BUTTON, self.delete_game_button, self.game_info_group['delete_button'])
        self.frame.Bind(wx.EVT_BUTTON, self.install_export_game_dialog, id=xrc.XRCID('install_button'))
        
        # load last config file if there was one
        if 'last_cfg' in self.ini.keys() and self.ini['last_cfg'].strip() != "":
            self.current_config = self.ini['last_cfg']
            self.refresh_game_list()
        else:
            self.current_config = ""
            
        self.frame.Show()
        return
        
    def load_cfg_dialog(self, evt):
        #dialog controls
        self.load_dialog = self.res.LoadDialog(None, 'file_open_dialog')
        self.load_dialog.cancel_load_button = xrc.XRCCTRL(self.load_dialog, 'cancel_load_button')
        self.load_dialog.confirm_load_button = xrc.XRCCTRL(self.load_dialog, 'confirm_load_button')
        self.load_dialog.load_cfg_dirctrl = xrc.XRCCTRL(self.load_dialog, 'load_cfg_dirctrl')
        
        #pick up directory where user last left off
        if self.current_config.strip() == "":
            self.load_dialog.load_cfg_dirctrl.SetPath(os.getcwd())
        else:
            self.load_dialog.load_cfg_dirctrl.SetPath(os.path.split(self.current_config)[0])
            
        self.load_dialog.dirtree = self.load_dialog.load_cfg_dirctrl.GetTreeCtrl()
        
        #dialog callbacks
        self.load_dialog.Bind(wx.EVT_TREE_SEL_CHANGED, self.file_open_handle_tree_click, self.load_dialog.dirtree)
        self.load_dialog.Bind(wx.EVT_BUTTON, self.dialog_close, self.load_dialog.cancel_load_button)
        self.load_dialog.Bind(wx.EVT_BUTTON, self.load_cfg_file, self.load_dialog.confirm_load_button)
        self.load_dialog.ShowModal()        
        return
        
    def generic_file_chooser(self):
        #dialog controls
        self.load_dialog = self.res.LoadDialog(None, 'file_open_dialog')
        self.load_dialog.cancel_load_button = xrc.XRCCTRL(self.load_dialog, 'cancel_load_button')
        self.load_dialog.confirm_load_button = xrc.XRCCTRL(self.load_dialog, 'confirm_load_button')
        self.load_dialog.confirm_load_button.Enable()
        self.load_dialog.load_cfg_dirctrl = xrc.XRCCTRL(self.load_dialog, 'load_cfg_dirctrl')
        self.load_dialog.dirtree = self.load_dialog.load_cfg_dirctrl.GetTreeCtrl()
        self.load_dialog.Bind(wx.EVT_BUTTON, self.dialog_close, self.load_dialog.cancel_load_button)
        self.load_dialog.Bind(wx.EVT_BUTTON, self.generic_confirm_load, self.load_dialog.confirm_load_button)
        self.load_dialog.ShowModal()        
        return
        
    def iso_file_chooser(self):

        #dialog controls
        self.load_dialog = self.res.LoadDialog(None, 'file_open_dialog')
        self.load_dialog.cancel_load_button = xrc.XRCCTRL(self.load_dialog, 'cancel_load_button')
        self.load_dialog.confirm_load_button = xrc.XRCCTRL(self.load_dialog, 'confirm_load_button')
        self.load_dialog.confirm_load_button.Enable()
        self.load_dialog.load_cfg_dirctrl = xrc.XRCCTRL(self.load_dialog, 'load_cfg_dirctrl')
        self.load_dialog.dirtree = self.load_dialog.load_cfg_dirctrl.GetTreeCtrl()
        
        if 'last_install_dir' in self.ini.keys():
            self.load_dialog.load_cfg_dirctrl.SetPath(self.ini['last_install_dir'])
            print "DEBUG found last install iso dir"
        else:
            self.load_dialog.load_cfg_dirctrl.SetPath(os.getcwd())

        self.load_dialog.Bind(wx.EVT_BUTTON, self.dialog_close, self.load_dialog.cancel_load_button)
        self.load_dialog.Bind(wx.EVT_BUTTON, self.generic_confirm_load, self.load_dialog.confirm_load_button)
        self.load_dialog.ShowModal()        
        return
        
    def generic_confirm_load(self,evt):
        self.scratch_path = self.load_dialog.load_cfg_dirctrl.GetPath()
        self.write_ini()
        self.load_dialog.Close()
        return
            
    def install_export_game_dialog(self, evt):
        #dialog controls
        self.install_dialog = self.res.LoadDialog(None, 'install_dialog')
        install_dialog_control_list = [
										'game_instructions_static',
                                        'install_game_button',
										'choose_install_button',
										'progress_static',
										'progress_bar', 
										'cancel_install_button',
                                        'console_output',
                                        'game_name',
                                        'media_choice' ]
                                        
        self.install_dialog_controls = {}
        for item in install_dialog_control_list:
            self.install_dialog_controls[item] = xrc.XRCCTRL(self.install_dialog, item)
            
        #dialog callbacks
        self.install_dialog.Bind(wx.EVT_BUTTON, self.install_close, self.install_dialog_controls['cancel_install_button'])
        self.install_dialog.Bind(wx.EVT_BUTTON, self.install_this_game, self.install_dialog_controls['install_game_button'])
        self.install_dialog.Bind(wx.EVT_BUTTON, self.choose_game_for_install, self.install_dialog_controls['choose_install_button'])
        
        self.install_dialog.console_line_limit = 300
        
        self.install_dialog.ShowModal()
        return
        
        
    def install_close(self, evt):
        self.install_dialog.Close()
        self.install_dialog.Destroy()
        return
        
    def dialog_close(self, evt):
        self.scratch_path = None
        self.load_dialog.Destroy()
        self.load_dialog.Close()
        return
    
    def choose_game_for_install(self,evt):
        self.scratch_path = ""
        self.install_dialog.chosen_file_info = {}
        self.iso_file_chooser()
        if self.scratch_path != None:
            path, filename = os.path.split( self.scratch_path )
            if re.search( r'(iso|rar)', filename, re.IGNORECASE ):
                if re.search(r'iso',filename, re.I):
                    self.install_dialog.chosen_file_info['filetype'] = 'iso'
                else:
                    if rar_has_iso(self.ini['unrar'], os.path.join(path, filename) ):
                        self.install_dialog.chosen_file_info['filetype'] = 'rar' 
                    else:
                        wx.MessageBox("rar file does not contain iso to install!","Error")
                        return
                self.install_dialog.chosen_file_info['filename'] = filename
                self.install_dialog.chosen_file_info['path'] = path
                self.install_dialog.chosen_file_info['abspath'] = os.path.join( path, filename )
                self.install_dialog_controls['game_instructions_static'].SetLabel( filename )
                self.install_dialog_controls['install_game_button'].Enable()
                self.ini['last_install_dir'] = path
                print "DEBUG "+ str( self.install_dialog.chosen_file_info )
            else:
                wx.MessageBox("Please select a file of type iso, or rar (containing an iso)","Warning")
                return
            
    def install_this_game(self, evt):
        game_name = self.install_dialog_controls['game_name'].GetValue()
        
        #print "DEBUG "+str(dir(self.install_dialog_controls['media_choice']))
        
        media = self.install_dialog_controls['media_choice'].GetStringSelection()
        if self.install_dialog.chosen_file_info['filetype'] == 'rar':
            # print "DUMMY: extracting rar file [game name]="+game_name + " [media]="+media
            self.install_rar(game_name, media, self.install_dialog.chosen_file_info['abspath'])
        else:
            # print "DUMMY: install iso file [game name]="+game_name + " [media]="+media
            pass
                
    def install_rar(self, game_name, media, rar_filename):
        spawn = rar_extract_process( self.ini['unrar'], rar_filename, rar_filename+".temp" )
        percent_complete = 0
        console_output = ""
        while ( spawn.poll() ):
            last_output = console_output
            last_percent = percent_complete
            self.install_dialog_controls['media_choice']
            percent_complete = rar_pcent_complete( spawn )
            if (last_percent < percent_complete):
                self.install_dialog_controls['progress_bar'].SetValue( percent_complete )
            console_output = spawn.communicate()
            if (last_output != console_output):
                self.install_dialog_controls['console_output'].Append( console_output.strip() )
        return

    def install_iso(self, game_name, media, iso_filename):
        spawn = install_iso_process( (self.ini['iso2opl'], iso_filename, self.current_config, game_name, media ))
        return
        
    def pref_dialog(self, evt):
        #dialog controls
        self.preferences_dialog = self.res.LoadDialog(None, 'pref_dialog')
        self.read_ini()
        
        pref_dialog_control_list = [ 'iso2opl_bin_static',
                                        'opl2iso_bin_static',
                                        'iso2opl_choose_button',
                                        'opl2iso_choose_button',
                                        'unrar_bin_static',
                                        'unrar_choose_button',
                                        'pref_close_button' ]
        
        self.pref_dialog_controls = {}
        
        for item in pref_dialog_control_list:
            self.pref_dialog_controls[item] = xrc.XRCCTRL(self.preferences_dialog, item)
            
        #dialog callbacks
        self.preferences_dialog.Bind(wx.EVT_BUTTON, self.pref_close, self.pref_dialog_controls['pref_close_button'])
        self.preferences_dialog.Bind(wx.EVT_BUTTON, self.choose_iso2opl, self.pref_dialog_controls['iso2opl_choose_button'])
        self.preferences_dialog.Bind(wx.EVT_BUTTON, self.choose_opl2iso, self.pref_dialog_controls['opl2iso_choose_button'])
        self.preferences_dialog.Bind(wx.EVT_BUTTON, self.choose_unrar, self.pref_dialog_controls['unrar_choose_button'])

        if 'iso2opl' in self.ini.keys():
            self.pref_dialog_controls['iso2opl_bin_static'].SetLabel(self.ini['iso2opl'])
        if 'opl2iso' in self.ini.keys():
            self.pref_dialog_controls['opl2iso_bin_static'].SetLabel(self.ini['opl2iso'])
        if 'unrar' in self.ini.keys():
            self.pref_dialog_controls['unrar_bin_static'].SetLabel(self.ini['unrar'])

        self.preferences_dialog.ShowModal()
        return
        
    def pref_close(self,evt):
		self.preferences_dialog.Close()
		self.preferences_dialog.Destroy()
		self.write_ini()
		return
        
    def choose_iso2opl(self,evt):
        self.scratch_path = ""
        self.generic_file_chooser()
        self.ini['iso2opl']=self.scratch_path
        self.pref_dialog_controls['iso2opl_bin_static'].SetLabel(self.ini['iso2opl'])
        return
    
    def choose_opl2iso(self,evt):
        self.scratch_path = ""
        self.generic_file_chooser()
        self.ini['opl2iso']=self.scratch_path
        self.pref_dialog_controls['opl2iso_bin_static'].SetLabel(self.ini['opl2iso'])
        return
    
    def choose_unrar(self,evt):
        self.scratch_path = ""
        self.generic_file_chooser()
        self.ini['unrar']=self.scratch_path
        self.pref_dialog_controls['unrar_bin_static'].SetLabel(self.ini['unrar'])
        return
        
    def load_game_info(self, evt):
        game_name = self.game_list_control.GetStringSelection()
        
        if game_name.strip() =="":
            return
        size = get_game_disk_use( game_name, self.current_config )

        size_string = "%.2f" % (float(size)/1024/1024)
       
        #print self.game_list[ game_name ]
        if game_name.strip() != "":
            self.game_info_group['size_amount_static'].SetLabel( size_string + " MB")
            self.game_info_group['game_name_textctrl'].SetValue( game_name )
            self.game_info_group['part_amount_static'].SetLabel( str(self.game_list[ game_name ][2]) )
            
            if self.game_list[ game_name ][3] == 0x14: 
                media_type = "DVD"
            else:
                media_type = "CD"
				
            self.game_info_group['media_type_static'].SetLabel( media_type )
        
        for item in self.game_info_group.keys():
            self.game_info_group[item].Enable()
        return
        
    def zero_game_info(self):
        #clear details out of the 'Game info' area
        self.game_info_group['size_amount_static'].SetLabel( "0.00 MB")
        self.game_info_group['game_name_textctrl'].SetValue( "" )
        self.game_info_group['part_amount_static'].SetLabel( "0" )
        self.game_info_group['media_type_static'].SetLabel( "--" )
        for item in self.game_info_group.keys():
            self.game_info_group[item].Disable()
        return
    
    def file_open_handle_tree_click(self, evt):
        path = self.load_dialog.load_cfg_dirctrl.GetPath()
        if os.path.isfile( path ):
            path = os.path.split( path )[0]
        if dir_has_file( path, 'ul.cfg' ):
            self.load_dialog.confirm_load_button.Enable()
        else:
            self.load_dialog.confirm_load_button.Disable()
        return
        
    def rename_game_button(self, evt):
        #should validate better here well.
        selected_item = self.game_list_control.GetSelection()
        old_name = self.game_list_control.GetStringSelection()
        new_name = self.game_info_group['game_name_textctrl'].GetValue()
        if old_name == new_name:
            return # no change needed
        if new_name.strip()=="":
            return # dont want to accidentally insert a null name
        rename_game(old_name, new_name, self.current_config)
        self.refresh_game_list()
        self.game_list_control.SetSelection(selected_item)
        self.load_game_info(None)
        return
    
    def load_cfg_file(self, evt):
        path = self.load_dialog.load_cfg_dirctrl.GetPath()
        if os.path.isfile(path):
            path = os.path.split(path)[0]
        
        #clear the game info area
        self.zero_game_info()
        
        self.current_config = os.path.join( path, "ul.cfg")
        
        self.ini['last_cfg'] = self.current_config
        self.write_ini() # save the chosen ul.cfg to opltool.ini so it will auto open on startup
        
        self.load_dialog.Destroy()
        self.load_dialog.Close()
        
        self.refresh_game_list()
        self.current_config_static.SetLabel(self.current_config)
        return
        
    def reload_wrapper(self, evt):
        refresh_game_list()
        return
        
    def refresh_game_list(self):
        self.game_list = read_cfg( self.current_config )
        self.game_list_control.Clear()
        for game in self.game_list:
            self.game_list_control.Append(game, None)
        self.game_list_control.Enable()
        self.current_config_static.SetLabel(self.current_config)
        return
        
    def delete_game_button(self, evt):
        game_name = self.game_list_control.GetStringSelection()
        delete_game( game_name, self.game_list, self.current_config )
        self.refresh_game_list()
        if len(self.game_list) > 0:
            self.game_list_control.SetSelection(0)
            self.load_game_info(None)
        else:
            self.zero_game_info()
        return
    
    def quit_app(self, evt):
        self.frame.Close()
        return
        
    def read_ini(self):
        self.ini = {} #clear any existing ini records
        try:
            inifile = open("opltool.ini","r+")
        except (IOError):
            #print IOError
            return
        for line in inifile:
            k,v = line.split(":",1)
            self.ini[k.strip()]=v.strip()
        inifile.close()
        return
        
    def write_ini(self):
        try:
            inifile = open("opltool.ini","w+") #truncate existing file
        except (IOError):
            print IOError
            return
        for k in self.ini.keys():
            inifile.write(k+':'+self.ini[k]+"\n")
        inifile.close()
        return

        
### Util functions

####### game installation functions
def rar_has_iso(unrar_bin, rar_filename):
    """ Determine if a rar file contains an iso """
    spawn = subprocess.Popen( (unrar_bin, '--list', rar_filename),
                                stdout = subprocess.PIPE,
                                close_fds = True )
    stdout_txt, stderr_txt = spawn.communicate()
    for line in stdout_txt.split("\n"):
        if re.search(r'iso',line):
            return True
    return False

def install_iso_process(args):
    #iso2opl /home/user/WORMS4.ISO /media/disk WORMS_4_MAYHEM DVD
    for variable in (iso2opl_bin, iso_filename, target, game_name, media_type):
        if variable == None or variable.strip()=="":
            return None
    """ Spawn subprocess to install iso """
    spawn = subprocess.Popen( (iso2opl_bin, iso_filename, target, game_name, media_type),
                                stdout = subprocess.PIPE,
                                close_fds = True )
    return spawn
    
def rar_extract_process(unrar_bin, rar_filename, temp_target):

    if not os.path.exists(temp_target):
        os.makedirs(temp_target)
    
    for variable in (unrar_bin, rar_filename, temp_target):
        if variable == None or variable.strip()=="":
            return None
    """ Spawn subprocess to extract rar """
    spawn = subprocess.Popen( (unrar_bin, rar_filename, temp_target),
                                stdout = subprocess.PIPE,
                                close_fds = True )
    return spawn
    
def rar_pcent_complete(spawn):
    output = spawn.communicate()
    percent_complete = 0
    #re.search( r'\d\%', output)
    #percent_complete = 
    return percent_complete

#######

def dir_has_file(path, file):
    dirlist = os.listdir( path )
    for item in dirlist:
        if os.path.isfile(os.path.join(path,item)) and re.search(file, item):
            return True
    return False
    
def read_cfg(filename):
    
    """ 
        read_cfg(filename) - load a dictionary of records (cfg_records) keyed on game name (32 char)
        records in cfg_records take the form:
    
        Field Definitions (USBAdvance origin?):
        
        C code taken from iso2usbld.h (ul.cfg field defs)
         typedef struct {
            char name[32];  // Game name (limited to 32 chars?)
            char image[15]; // SLUSXXXX (15 chars)
            u8   parts;     // number of parts (u8 = unsigned char)
            u8   media; 
            u8   pad[15];
         } cfg_t;
         
         TODO: add validation that this is a good ul.cfg file...
    """  
    cfg_records = {}
    cfg_file = open(filename, 'r')
    for raw_records in cfg_file:
        record_length = len(raw_records)
        cursor = 0
        while cursor < record_length and record_length % 64 == 0:
            
            # String fmt here corresponds to the above C struct
            # note about unicode strings - may need to worry about encoding when packing later
            unpacked_record = struct.unpack('32s15sBB15B', raw_records[cursor:cursor+64])
            cfg_records[unpacked_record[0].strip("\x00")] = unpacked_record
            cursor += 64
    cfg_file.close()
    
    return cfg_records
    
def write_cfg(cfg_records, filename):
    raw_record = ""
    for name in cfg_records:
        raw_record += struct.pack('32s15sBB15B', *cfg_records[name])
    l = open(filename, 'wb')
    l.write(raw_record)
    l.close()
    #print "Wrote records to "+filename+""
    return
    
def rename_game(old_name, new_name, filename):
    #load config entry
    cfg_records = read_cfg(filename)
    
    #store in a temp
    game_record = cfg_records[old_name]
    
    #remove the mapping for this entry
    del cfg_records[old_name]
    
    #copy from tuple
    new_game_record_l = list(game_record)
    new_game_record_l[0] = new_name.ljust(32,"\x00").encode()
    
    #back to tuple
    new_record_t = tuple(new_game_record_l)
    cfg_records[new_name] = new_record_t
    
    #write changes
    write_cfg(cfg_records, filename)
    return
    
def delete_game(name, cfg_records, filename):
    """ remove game files related to entry in ul.cfg, and then the entry in ul.cfg itself """
    file_list = get_game_filenames(name, filename)
    for gfile in file_list:
        os.remove(gfile)
    #remove game from cfg_records
    del cfg_records[name]
    
    #write the changes to the ul.cfg
    write_cfg( cfg_records, filename )
    return

def get_game_filenames(name, cfg_filename):
    """ Get files associate with this game's name, based on SLUS_XXX.XX number """
    cfg_records = read_cfg(cfg_filename)
    working_directory = os.path.split( os.path.abspath( cfg_filename ) )[0]
    game_files = []
    game_record = cfg_records[name]
    #1. get dir listing
    for item in os.listdir( working_directory ):
        #2. find filenames that match SLUS (image) code
        if re.search( game_record[1][3:].strip("\x00"), item ):
            game_filename = os.path.join(working_directory, item)
            game_files.append( game_filename )
    return game_files
    
def get_game_disk_use(name, cfg_filename):
    if name.strip() == "" or cfg_filename.strip() == "":
        return 0
    game_files = get_game_filenames(name, cfg_filename)
    size = 0
    for file in game_files:
        size += os.path.getsize(file)
    return size
	
if __name__ == "__main__":
    app = MainWindow()
    app.MainLoop()
    
