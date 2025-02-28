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
from Components.MenuList import MenuList
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

    sanitized_name = bouquet_name.replace(" ", "_").lower()
    output_file = os.path.join(output_dir, f"userbouquet.{sanitized_name}.tv")

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(f"#NAME {bouquet_name}\n")

        for group_name in selected_groups:
            if group_name in groups:
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

def show_groups(self):
    if not self.selected_file:
        self["message_label"].setText("No file selected!")
        return
    groups, has_groups = parse_m3u_by_groups(self.selected_file)
    if not groups:
        self["message_label"].setText("No groups found in file!")
        return
    if not has_groups:
        self.selected_groups = ["All Channels"]
        self.update_status_label()
    else:
        self.session.openWithCallback(self.on_group_selection, GroupSelectionScreen, groups)
        
class GroupSelectionScreen(Screen):
    skin = """
    <screen name="GroupSelectionScreen" position="center,center" size="800,800" title="Select Groups">
        <widget name="group_list" position="20,20" size="760,700" font="Regular;24" scrollbarMode="showAlways" />
        <widget name="button_red" position="20,740" size="180,40" font="Bold;22" halign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="button_green" position="220,740" size="180,40" font="Bold;22" halign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="button_blue" position="420,740" size="180,40" font="Bold;22" halign="center" backgroundColor="#13389F" foregroundColor="#000000" />
    </screen>
    """

    def __init__(self, session, groups):
        Screen.__init__(self, session)
        self.groups = list(groups.keys())
        self.selected_groups = []

        # Inicijalno postavljanje liste sa oznakama
        self["group_list"] = MenuList(self.build_group_list(), enableWrapAround=True)
        self["button_red"] = Button("Cancel")
        self["button_green"] = Button("Confirm")
        self["button_blue"] = Button("Select All")

        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions", "ColorActions"],
            {
                "ok": self.toggle_selection,
                "cancel": self.cancel,
                "up": self["group_list"].up,
                "down": self["group_list"].down,
                "green": self.confirm,
                "red": self.cancel,
                "blue": self.select_all,
            },
            -1
        )

    def build_group_list(self):
        """Kreiranje liste sa oznakama za selektovane grupe."""
        group_list = []
        for group in self.groups:
            if group in self.selected_groups:
                group_list.append(f"✓ {group}")
            else:
                group_list.append(f"  {group}")
        return group_list

    def toggle_selection(self):
        # Uzimamo indeks trenutno izabrane stavke i mapiramo ga na originalno ime grupe
        current_index = self["group_list"].getSelectionIndex()
        if current_index >= 0 and current_index < len(self.groups):
            group_name = self.groups[current_index]  # Koristimo čisto ime iz self.groups
            if group_name in self.selected_groups:
                self.selected_groups.remove(group_name)
            else:
                self.selected_groups.append(group_name)
            # Ažuriramo prikaz liste
            self["group_list"].setList(self.build_group_list())
            print(f"Selected groups: {self.selected_groups}")

    def select_all(self):
        if set(self.groups) == set(self.selected_groups):
            self.selected_groups = []  # Deselektuj sve ako su sve izabrane
        else:
            self.selected_groups = self.groups[:]  # Izaberi sve
        # Ažuriramo prikaz liste
        self["group_list"].setList(self.build_group_list())
        print(f"Selected groups after Select All: {self.selected_groups}")

    def confirm(self):
        self.close(self.selected_groups)

    def cancel(self):
        self.close([])

class MainScreen(Screen, ConfigListScreen):
    version = "1.6"  # Updated version
    skin = f"""
    <screen name="CiefpE2Converter" position="center,center" size="1600,800" title="CiefpE2Converter v{version}">
        <widget name="background" position="1200,0" size="400,800" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpE2Converter/background.png" zPosition="-1" alphatest="on" />
        <widget name="message_label" position="50,30" size="1100,100" font="Regular;24" valign="top" />
        <widget name="file_list" position="50,150" size="600,580" scrollbarMode="showOnDemand" />
        <widget name="status_label" position="700,150" size="500,580" font="Regular;22" halign="left" valign="top" />
        <widget name="button_red" position="50,750" size="200,40" font="Bold;22" halign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="button_yellow" position="250,750" size="200,40" font="Bold;22" halign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
        <widget name="button_blue" position="450,750" size="200,40" font="Bold;22" halign="center" backgroundColor="#13389F" foregroundColor="#000000" />
        <widget name="button_green" position="650,750" size="200,40" font="Bold;22" halign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
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
            ["SetupActions", "DirectionActions", "ColorActions", "TextEditActions"],
            {
                "ok": self.choose_file,
                "cancel": self.exit,
                "up": self["file_list"].up,
                "down": self["file_list"].down,
                "left": self["file_list"].pageUp,
                "right": self["file_list"].pageDown,
                "yellow": self.open_virtual_keyboard,
                "blue": self.show_groups,
                "green": self.convert,
                "red": self.exit,
            },
            -1
        )

        self.selected_file = None
        self.selected_groups = []
        self.selected_service_type = None

    def update_status_label(self):
        if self.selected_groups:
            groups_display = "Selected groups:\n" + "\n".join(f"{idx}. {group}" for idx, group in enumerate(self.selected_groups, 1))
            self["status_label"].setText(groups_display)
        else:
            self["status_label"].setText("No groups selected.")

    def choose_file(self):
        selected = self["file_list"].getSelection()
        if selected is None:
            self["message_label"].setText("No file selected!")
            return
        if self["file_list"].canDescent():
            self["file_list"].descent()
        else:
            self.selected_file = os.path.join(self["file_list"].getCurrentDirectory(), selected[0])
            self["message_label"].setText(f"Bouquet name: {self.bouquet_name.value}\nSelected file: {self.selected_file}")

    def open_virtual_keyboard(self):
        if self.bouquet_name.value is None:
            self.bouquet_name.value = ""
        self.session.openWithCallback(self.on_keyboard_input, VirtualKeyBoard, title="Enter Bouquet Name", text=self.bouquet_name.value)

    def on_keyboard_input(self, text):
        if text is not None:
            self.bouquet_name.value = text
            self["message_label"].setText(f"Bouquet name: {text}\nSelected file: {self.selected_file or 'None'}")

    def show_groups(self):
        if not self.selected_file:
            self["message_label"].setText("No file selected!")
            return
        groups, has_groups = parse_m3u_by_groups(self.selected_file)
        if not groups:
            self["message_label"].setText("No groups found in file!")
            return
        if not has_groups:
            self.selected_groups = ["All Channels"]
            self.update_status_label()
        else:
            self.session.openWithCallback(self.on_group_selection, GroupSelectionScreen, groups)

    def on_group_selection(self, selected_groups):
        if selected_groups:
            self.selected_groups = selected_groups
            self.update_status_label()
        else:
            self["status_label"].setText("Group selection canceled.")

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
            convert_selected_groups(self.selected_file, output_dir, self.selected_service_type, self.selected_groups, self.bouquet_name.value, has_groups)
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
        try:
            print("Exiting MainScreen")
            self.close()
        except Exception as e:
            print(f"Error during exit: {str(e)}")
            self.close()  # Force close even on error