from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.FileList import FileList
from Components.Label import Label
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.config import ConfigText, config, getConfigListEntry
from Screens.MessageBox import MessageBox
from enigma import eTimer, eDVBDB
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.Pixmap import Pixmap
import os

def validate_m3u_file(input_file):
    """
    Validates if the given file is a proper M3U/M3U8 file.
    """
    try:
        with open(input_file, 'r') as file:
            lines = file.readlines()
            if any(line.startswith("#EXTM3U") for line in lines):
                return True
        return False
    except Exception as e:
        print(f"ERROR during file validation: {e}")
        return False

def convert_m3u_to_bouquet(input_file, output_file, service_type, bouquet_name):
    """
    Converts the input M3U/M3U8 file to Enigma2 bouquet format.
    """
    try:
        with open(input_file, 'r') as infile:
            lines = infile.readlines()

        bouquet_data = f"#NAME {bouquet_name}\n"

        for line in lines:
            line = line.strip()
            if line.startswith("#EXTINF"):
                channel_name = line.split(",")[1].strip()
            elif line.startswith("http://") or line.startswith("https://"):
                url = line.replace(":", "%3a")
                bouquet_data += f"#SERVICE {service_type}:0:0:0:0:0:0:0:{url}:{channel_name}\n"
                bouquet_data += f"#DESCRIPTION {channel_name}\n"

        # Register the bouquet by appending to the file
        with open(output_file, 'a') as outfile:
            outfile.write(bouquet_data)

        return True
    except Exception as e:
        print(f"ERROR during conversion: {e}")
        return False

def register_bouquet(bouquet_name):
    """
    Registers the bouquet in bouquets.tv if not already registered.
    """
    try:
        bouquet_file_path = "/etc/enigma2/bouquets.tv"
        bouquet_entry = f"#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.{bouquet_name}.tv\" ORDER BY bouquet\n"
        
        # Read existing content of bouquets.tv
        if os.path.exists(bouquet_file_path):
            with open(bouquet_file_path, "r") as file:
                content = file.readlines()
        else:
            content = []

        # Check if the entry already exists
        if bouquet_entry not in content:
            with open(bouquet_file_path, "a") as file:
                file.write(bouquet_entry)
            print(f"Bouquet {bouquet_name} registered successfully in bouquets.tv.")
        else:
            print(f"Bouquet {bouquet_name} is already registered.")
        
        return True
    except Exception as e:
        print(f"ERROR registering bouquet: {e}")
        return False

class MainScreen(Screen, ConfigListScreen):
    skin = """
    <screen name="CiefpE2Converter" position="center,center" size="1200,600" title="CiefpE2Converter">
        <!-- Main Area (70% of the screen) -->
        <widget name="main_area" position="0,0" size="840,600" />
    
        <!-- Background Image (30% of the screen) -->
        <widget name="background" position="840,0" size="360,600" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpE2Converter/background.png" zPosition="-1" alphatest="on" />
    
        <!-- Message Label -->
        <widget name="message_label" position="50,50" size="740,40" font="Regular;24" valign="center" />
    
        <!-- File List (in the 70% section) -->
        <widget name="file_list" position="50,100" size="740,300" scrollbarMode="showOnDemand" />
    
        <!-- Config List (in the 70% section) -->
        <widget name="config" position="50,420" size="740,150" scrollbarMode="showOnDemand" />
    
        <!-- Red Button (in the 70% section) -->
        <widget name="button_red" position="50,500" size="150,50" font="Bold;22" halign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
    
        <!-- Green Button (in the 70% section) -->
        <widget name="button_green" position="200,500" size="150,50" font="Bold;22" halign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
    
        <!-- Yellow Button (in the 70% section) -->
        <widget name="button_yellow" position="350,500" size="150,50" font="Bold;22" halign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
    
        <!-- Blue Button (in the 70% section) -->
        <widget name="button_blue" position="500,500" size="150,50" font="Bold;22" halign="center" backgroundColor="#13389F" foregroundColor="#000000" />
    
        <!-- Status Label (in the 70% section) -->
        <widget name="status_label" position="10,520" size="800,60" font="Regular;22" halign="center" />
    </screen>
"""

    def __init__(self, session):
        Screen.__init__(self, session)

        self.bouquet_name = ConfigText(default="IPTV Mix Bouquet", fixed_size=False)

        ConfigListScreen.__init__(self, [
            getConfigListEntry("Bouquet Name:", self.bouquet_name)
        ])

        self["background"] = Pixmap()
        self["message_label"] = Label("Select a file and define bouquet name")
        self["status_label"] = Label("")

        # File List Widget
        self["file_list"] = FileList("/tmp", showDirectories=True, matchingPattern=".*\\.(m3u|m3u8)$")

        # Buttons
        self["button_red"] = Button("Exit")
        self["button_green"] = Button("Convert 4097")
        self["button_yellow"] = Button("Enter Bouquet Name")  # Changed label to indicate it opens virtual keyboard
        self["button_blue"] = Button("Convert 5002")

        # Actions - Updated for Python 3.12.4 with correct references
        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions", "TextEditActions"],  # Test with different contexts
            {
                "ok": self.choose_file,
                "green": lambda: self.convert("4097:0:1"),
                "yellow": self.open_virtual_keyboard,  # Yellow button now opens virtual keyboard
                "blue": lambda: self.convert("5002:0:1"),
                "cancel": self.exit,
            },
            -1,
        )

        self.selected_file = None

    def choose_file(self):
        selected = self["file_list"].getSelection()
        if selected is None:
            self["message_label"].setText("No file selected!")
            return

        if self["file_list"].canDescent():
            self["file_list"].descent()
        else:
            self.selected_file = os.path.join(self["file_list"].getCurrentDirectory(), selected[0])
            self["message_label"].setText(f"Selected file: {self.selected_file}")

    def open_virtual_keyboard(self):
        print("Yellow button pressed! Opening virtual keyboard...")
        if self.bouquet_name.value is None:
            self.bouquet_name.value = ""
        self.session.openWithCallback(self.on_keyboard_input, VirtualKeyBoard, title="Enter Bouquet Name", text=self.bouquet_name.value)

    def on_keyboard_input(self, text):
        if text is not None:
            self.bouquet_name.value = text
            self["message_label"].setText(f"Bouquet name updated: {text}")

    def convert(self, service_type):
        if not self.selected_file or not validate_m3u_file(self.selected_file):
            self["message_label"].setText("Invalid or no file selected!")
            return

        bouquet_name = self.bouquet_name.value.strip()
        if not bouquet_name:
            self["message_label"].setText("Please enter a bouquet name!")
            return

        sanitized_name = bouquet_name.replace(" ", "_").lower()
        output_file = os.path.join("/etc/enigma2", f"userbouquet.{sanitized_name}.tv")

        if convert_m3u_to_bouquet(self.selected_file, output_file, service_type, bouquet_name):
            self["message_label"].setText("Conversion successful!")

            # Register the bouquet in bouquets.tv
            if register_bouquet(sanitized_name):
                self["message_label"].setText("Bouquet successfully registered!")
            else:
                self["message_label"].setText("Failed to register bouquet.")

            # Ask user if they want to reload settings after conversion
            self.session.openWithCallback(self.on_reload_response, MessageBox,
                                          "Do you want to reload settings?", MessageBox.TYPE_YESNO)
        else:
            self["message_label"].setText("Conversion failed!")

    def on_reload_response(self, answer):
        if answer:  # If 'Yes' is pressed
            self.reload_settings()
        else:
            self["message_label"].setText("Reload canceled!")

    def reload_settings(self):
        """Reload Enigma2 settings."""
        try:
            eDVBDB.getInstance().reloadServicelist()
            eDVBDB.getInstance().reloadBouquets()
            self.session.open(MessageBox, "Reload successful!   ..::ciefpsettings::..", MessageBox.TYPE_INFO, timeout=5)
        except Exception as e:
            self.session.open(MessageBox, f"Reload failed: {str(e)}", MessageBox.TYPE_ERROR, timeout=5)

    def exit(self):
        self.close()
