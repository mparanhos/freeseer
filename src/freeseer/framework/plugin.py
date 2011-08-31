import ConfigParser
import os

import pygst
pygst.require("0.10")
import gst

from yapsy.PluginManager import PluginManagerSingleton
from yapsy.ConfigurablePluginManager import ConfigurablePluginManager
from yapsy.IPlugin import IPlugin

class PluginManager:
    def __init__(self, configdir):
        self.firstrun = False
        plugman = PluginManagerSingleton().get()
        
        self.configdir = configdir
        self.configfile = os.path.abspath("%s/plugin.conf" % self.configdir)
        
        self.config = ConfigParser.ConfigParser()
        self.load()
        self.plugmanc = ConfigurablePluginManager(self.config, self, plugman)
        
        # Get the path where the installed plugins are located on systems where
        # freeseer is installed.
        pluginpath = "%s/../plugins" % os.path.dirname(os.path.abspath(__file__))
        
        self.plugmanc.setPluginPlaces([pluginpath, 
                                       "~/.freeseer/plugins", 
                                       "freeseer/plugins"])
        self.plugmanc.setCategoriesFilter({
            "AudioInput" : IAudioInput,
            "AudioMixer" : IAudioMixer,
            "VideoInput" : IVideoInput,
            "VideoMixer" : IVideoMixer,
            "Output" : IOutput,
            })
        self.plugmanc.collectPlugins()
        
        # If config was corrupt or did not exist, reset default plugins.
        if self.firstrun == True:
            self.set_default_plugins()
        
    def __call__(self):
        pass
    
    def load(self):
        try:
            self.config.readfp(open(self.configfile))
        # Config file does not exist, create a default
        except IOError:
            self.firstrun = True # If config was corrupt or did not exist, reset defaults.
            self.save()
            return
        
    def set_default_plugins(self):
        """
        Default the passthrough mixers and ogg output plugins.
        """
        
        self.activate_plugin("Audio Passthrough", "AudioMixer")
        
        # Set Pulse Source as default if available. Else default to ALSA.
        try:
            gst.element_factory_make('pulsesrc', 'testsrc')
            self.activate_plugin("Pulse Audio Source", "AudioInput")
            self.plugmanc.registerOptionFromPlugin("AudioMixer", "Audio Passthrough", "Audio Input", "Pulse Audio Source")
        except:
            self.activate_plugin("ALSA Source", "AudioInput")
            self.plugmanc.registerOptionFromPlugin("AudioMixer", "Audio Passthrough", "Audio Input", "ALSA Source")
            
        self.activate_plugin("Video Passthrough", "VideoMixer")
        self.activate_plugin("USB Source", "VideoInput")
        self.plugmanc.registerOptionFromPlugin("VideoMixer", "Video Passthrough", "Video Input", "USB Source")
        self.activate_plugin("Ogg Output", "Output")
        
    def save(self):
        with open(self.configfile, 'w') as configfile:
            self.config.write(configfile)
        
    def activate_plugin(self, plugin_name, plugin_category):
        self.plugmanc.activatePluginByName(plugin_name, plugin_category, True)
        self.save()
        
    def deactivate_plugin(self, plugin_name, plugin_category):
        self.plugmanc.deactivatePluginByName(plugin_name, plugin_category, True)
        self.save()

class IBackendPlugin(IPlugin):
    name = None
    widget = None
    
    def get_name(self):
        return self.name
    
    def load_config(self, plugman):
        pass
    
    def get_widget(self):
        """
        Implement this method to return the settings widget (Qt based).
        Used by Freeseer configtool 
        """
        return None
    
    def widget_load_config(self, plugman):
        """
        Implement this when using a plugin widget. This function should be used
        to load any required configurations for the plugin widget.
        """
        pass

class IAudioInput(IBackendPlugin):
    
    def get_audioinput_bin(self):
        pass
    
class IAudioMixer(IBackendPlugin):
    
    def get_audiomixer_bin(self):
        pass
    
class IVideoInput(IBackendPlugin):
    
    def get_videoinput_bin(self):
        """
        Returns the Gstreamer Bin for the video input plugin.
        MUST be overridded when creating a video input plugin.
        """
        pass
    
class IVideoMixer(IBackendPlugin):
    
    def get_videomixer_bin(self):
        """
        Returns the Gstreamer Bin for the video mixer plugin.
        MUST be overridded when creating a video mixer plugin.
        """
        pass

class IOutput(IBackendPlugin):
    type = None # Types: audio, video, both
    extension = None
    location = None
    
    def get_type(self):
        return self.type
    
    def get_output_bin(self, metadata=None):
        """
        Returns the Gstreamer Bin for the output plugin.
        MUST be overridded when creating an output plugin.
        """
        pass
    
    def get_extension(self):
        return self.extension
    
    def set_recording_location(self, location):
        self.location = location

    def set_metadata(self, data):
        """
        Set the metadata if supported by Output plugin. 
        """
        pass