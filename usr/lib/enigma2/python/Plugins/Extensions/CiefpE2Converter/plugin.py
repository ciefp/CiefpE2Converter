from Plugins.Plugin import PluginDescriptor
from .ui import CiefpMainScreen

PLUGIN_VERSION = "2.1"
PLUGIN_NAME = "..:: CiefpE2Converter ::.."

def main(session, **kwargs):
    session.open(CiefpMainScreen)

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