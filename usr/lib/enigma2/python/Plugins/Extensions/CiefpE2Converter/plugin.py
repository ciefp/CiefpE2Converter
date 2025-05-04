from Plugins.Plugin import PluginDescriptor
from .ui import MainScreen

PLUGIN_VERSION = "1.9"
PLUGIN_NAME = "..:: CiefpE2Converter ::.."

def main(session, **kwargs):
    session.open(MainScreen)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="CiefpE2Converter",
            description=f"Convert m3u to enigma2 (Version {PLUGIN_VERSION})",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="/usr/lib/enigma2/python/Plugins/Extensions/CiefpE2Converter/icon.png",
            fnc=main,
        )
    ]
