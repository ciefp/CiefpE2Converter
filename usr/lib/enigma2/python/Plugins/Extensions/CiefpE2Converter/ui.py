from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.FileList import FileList
from Components.Label import Label
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.config import ConfigText, config, getConfigListEntry
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.Pixmap import Pixmap
from enigma import eDVBDB
from Screens.VirtualKeyBoard import VirtualKeyBoard
import os
import re

# Parse M3U file and group channels by group-title
def parse_m3u_by_groups(input_file):
    groups = {}
    current_group = None
    has_groups = False  # Flag to check if any group exists

    with open(input_file, 'r', encoding='utf-8') as file:
        for line in file:
            if line.startswith("#EXTINF"):
                match = re.search(r'group-title="([^"]+)"', line)
                if match:
                    current_group = match.group(1)
                    if current_group not in groups:
                        groups[current_group] = []
                    has_groups = True
                metadata = line.strip()
            elif line.startswith("http"):
                if current_group:
                    groups[current_group].append((metadata, line.strip()))
                elif not has_groups:
                    # If no groups are found, treat as a single group
                    groups["All Channels"] = groups.get("All Channels", [])
                    groups["All Channels"].append((metadata, line.strip()))
    return groups, has_groups

# Generate bouquet for selected groups
def convert_selected_groups(input_file, output_dir, service_type, selected_groups, bouquet_name, has_groups):
    groups, _ = parse_m3u_by_groups(input_file)

    if not has_groups:
        # If no groups are present, use the "All Channels" group
        selected_groups = ["All Channels"]

    for group_name in selected_groups:
        if group_name in groups:
            sanitized_name = bouquet_name.replace(" ", "_").lower()
            output_file = os.path.join(output_dir, f"userbouquet.{sanitized_name}.tv")
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write(f"#NAME {bouquet_name}\n")
                for metadata, url in groups[group_name]:
                    url_encoded = url.replace(":", "%3a")
                    channel_name = metadata.split(",")[1].strip()
                    if service_type.startswith("streamlink"):
                        if service_type == "streamlink_wrapper":
                            file.write(f"#SERVICE 4097:0:1:0:0:0:0:0:0:0:streamlink%3a//{url_encoded}:{channel_name}\n")
                        else:
                            file.write(f"#SERVICE 4097:0:1:0:0:0:0:0:0:0:http%3a//127.0.0.1%3a8088/{url_encoded}:{channel_name}\n")
                    else:
                        file.write(f"#SERVICE {service_type}:0:0:0:0:0:0:0:{url_encoded}\n")
                    # Add description for each service
                    file.write(f"#DESCRIPTION {channel_name}\n")

# Register the bouquet in bouquets.tv
def register_bouquet(bouquet_name):
    try:
        bouquet_file_path = "/etc/enigma2/bouquets.tv"
        sanitized_name = bouquet_name.replace(" ", "_").lower()
        bouquet_entry = f"#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.{sanitized_name}.tv\" ORDER BY bouquet\n"

        if os.path.exists(bouquet_file_path):
            with open(bouquet_file_path, "r") as file:
                content = file.readlines()
        else:
            content = []

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

# Main Screen
class MainScreen(Screen, ConfigListScreen):
    skin = """
    <screen name="CiefpE2Converter" position="center,center" size="1200,600" title="CiefpE2Converter">
        <widget name="background" position="840,0" size="360,600" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpE2Converter/background.png" zPosition="-1" alphatest="on" />
        <widget name="message_label" position="50,50" size="740,100" font="Regular;24" valign="top" />
        <widget name="file_list" position="50,150" size="740,300" scrollbarMode="showOnDemand" />
        <widget name="button_red" position="50,500" size="150,50" font="Bold;22" halign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="button_yellow" position="200,500" size="150,50" font="Bold;22" halign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
        <widget name="button_blue" position="350,500" size="150,50" font="Bold;22" halign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="button_green" position="500,500" size="150,50" font="Bold;22" halign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="status_label" position="10,560" size="800,40" font="Regular;22" halign="center" />
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.bouquet_name = ConfigText(default="IPTV Mix Bouquet", fixed_size=False)
        ConfigListScreen.__init__(self, [getConfigListEntry("Bouquet Name:", self.bouquet_name)])

        self["background"] = Pixmap()
        self["message_label"] = Label("Select a file and define bouquet name")
        self["status_label"] = Label("")
        self["file_list"] = FileList("/tmp", showDirectories=True, matchingPattern=".*\\.(m3u|m3u8)$")

        self["button_red"] = Button("Exit")
        self["button_yellow"] = Button("Define Name")
        self["button_blue"] = Button("Select Groups")
        self["button_green"] = Button("Convert")

        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions", "TextEditActions"],
            {
                "ok": self.choose_file,
                "yellow": self.open_virtual_keyboard,
                "blue": self.show_groups,
                "green": self.convert,
                "cancel": self.exit,
            },
            -1,
        )

        self.selected_file = None
        self.selected_groups = []
        self.selected_service_type = None

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
        if self.bouquet_name.value is None:
            self.bouquet_name.value = ""
        self.session.openWithCallback(self.on_keyboard_input, VirtualKeyBoard, title="Enter Bouquet Name", text=self.bouquet_name.value)

    def on_keyboard_input(self, text):
        if text is not None:
            self.bouquet_name.value = text
            self["message_label"].setText(f"Bouquet name updated: {text}")

    def show_groups(self):
        if not self.selected_file:
            self["message_label"].setText("No file selected!")
            return

        groups, has_groups = parse_m3u_by_groups(self.selected_file)
        if not groups:
            self["message_label"].setText("No groups found in file!")
            return

        # Ako nema grupisanja, omogućiti konverziju celog fajla
        if not has_groups:
            self.selected_groups = ["All Channels"]
            self["status_label"].setText("No groups found, converting entire file.")
        else:
            # Prikaz svih grupa sa mogućnošću selekcije više
            choices = [(group, group) for group in groups.keys()]
            choices.insert(0, ("Select All", "Select All"))
            self.session.openWithCallback(self.on_group_selection, ChoiceBox, title="Select Groups", list=choices)

    def on_group_selection(self, selected):
        if selected:
            # Ako je selektovana opcija "Select All", selektujemo sve grupe
            if selected[0] == "Select All":
                self.selected_groups = list(parse_m3u_by_groups(self.selected_file)[0].keys())
            else:
                # Dodavanje ili uklanjanje grupe sa liste selektovanih
                if selected[1] in self.selected_groups:
                    self.selected_groups.remove(selected[1])
                else:
                    self.selected_groups.append(selected[1])

            # Ažuriranje statusa sa svim selektovanim grupama
            self["status_label"].setText(f"Selected groups: {', '.join(self.selected_groups)}")
        else:
            self["status_label"].setText("No group selected!")

    def convert(self):
        if not self.selected_groups:
            self["message_label"].setText("No groups selected!")
            return

        choices = [
            ("Gstreamer (4097:0:1)", "4097:0:1"),
            ("Exteplayer3 (5002:0:1)", "5002:0:1"),
            ("DVB (1:0:1)", "1:0:1"),
            ("Radio (4097:0:2)", "4097:0:2"),
            ("Streamlink (http%3a//127.0.0.1%3a8088/)", "streamlink"),
            ("Streamlink Wrapper (streamlink%3a//)", "streamlink_wrapper"),
        ]
        self.session.openWithCallback(self.on_service_type_selection, ChoiceBox, title="Select Service Type", list=choices)

    def on_service_type_selection(self, selected):
        if selected:
            self.selected_service_type = selected[1]
            output_dir = "/etc/enigma2"
            groups, has_groups = parse_m3u_by_groups(self.selected_file)

            # Ako nema grupisanja, tretiramo ceo fajl kao jednu grupu
            convert_selected_groups(self.selected_file, output_dir, self.selected_service_type, self.selected_groups, self.bouquet_name.value, has_groups)

            for group in self.selected_groups:
                register_bouquet(self.bouquet_name.value)

            self.session.openWithCallback(self.on_reload_response, MessageBox, "Conversion completed! Reload settings?", MessageBox.TYPE_YESNO)

    def on_reload_response(self, answer):
        if answer:
            self.reload_settings()
        else:
            self["message_label"].setText("Reload canceled!")

    def reload_settings(self):
        try:
            eDVBDB.getInstance().reloadServicelist()
            eDVBDB.getInstance().reloadBouquets()
            self.session.open(MessageBox, "Reload successful!", MessageBox.TYPE_INFO, timeout=5)
        except Exception as e:
            self.session.open(MessageBox, f"Reload failed: {str(e)}", MessageBox.TYPE_ERROR, timeout=5)

    def exit(self):
        self.close()
