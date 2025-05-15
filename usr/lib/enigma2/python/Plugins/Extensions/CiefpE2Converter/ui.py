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
import urllib.request
import os
import re
from urllib.parse import urlparse

def parse_m3u_by_groups(input_file):
    groups = {}
    channels = []
    current_group = None
    has_groups = False

    with open(input_file, 'r', encoding='utf-8') as file:
        for line in file:
            if line.startswith("#EXTINF"):
                match = re.search(r'group-title="([^"]+)"', line)
                if match:
                    current_group = match.group(1)
                    if not current_group:  # Provera praznog stringa
                        current_group = None
                        continue
                    if current_group not in groups:
                        groups[current_group] = []
                    has_groups = True
                metadata = line.strip()
            elif line.startswith("http"):
                channel_name = metadata.split(",")[1].strip() if "," in metadata else "Unnamed"
                if current_group:
                    groups[current_group].append((metadata, line.strip()))
                else:
                    channels.append((channel_name, line.strip()))

    if not has_groups and channels:
        return channels, False
    return groups, has_groups

def download_m3u(url, base_dir="/tmp/m3u_playlist"):
    """Preuzimanje M3U fajla sa datog URL-a u direktorijum /tmp/m3u_playlist"""
    print(f"Attempting to download M3U from URL: {url}")
    try:
        # Proveravamo da li direktorijum postoji, ako ne, kreiramo ga
        if not os.path.exists(base_dir):
            print(f"Creating directory: {base_dir}")
            os.makedirs(base_dir)
        elif not os.path.isdir(base_dir):
            print(f"Error: {base_dir} exists but is not a directory!")
            return None

        # Generišemo ime fajla na osnovu URL-a
        # Uzimamo username iz URL-a ili padamo na generičko ime ako nije prisutan
        username_match = re.search(r'username=([^&]+)', url)
        if username_match:
            filename_base = username_match.group(1)
        else:
            filename_base = "playlist"

        # Dodajemo .m3u ekstenziju i proveravamo da li fajl već postoji
        output_path = os.path.join(base_dir, f"{filename_base}.m3u")
        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(base_dir, f"{filename_base}_{counter}.m3u")
            counter += 1

        print(f"Saving M3U to: {output_path}")
        urllib.request.urlretrieve(url, output_path)
        print(f"Successfully downloaded M3U to: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error downloading M3U file: {str(e)}")
        print(f"Failed URL: {url}")
        return None

def convert_selected_groups(input_file, output_dir, service_type, selected_items, bouquet_name, has_groups):
    result, _ = parse_m3u_by_groups(input_file)

    sanitized_name = bouquet_name.replace(" ", "_").lower()
    output_file = os.path.join(output_dir, f"userbouquet.{sanitized_name}.tv")

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(f"#NAME {bouquet_name}\n")

        if has_groups:
            # Ako su selektovane grupe
            for group_name in selected_items:
                if group_name in result:
                    for metadata, url in result[group_name]:
                        url_encoded = url.replace(":", "%3a")
                        channel_name = metadata.split(",")[1].strip()
                        if service_type.startswith("streamlink"):
                            if service_type == "streamlink_wrapper":
                                file.write(f"#SERVICE 4097:0:1:0:0:0:0:0:0:0:streamlink%3a//{url_encoded}:{channel_name}\n")
                            else:
                                file.write(f"#SERVICE 4097:0:1:0:0:0:0:0:0:0:http%3a//127.0.0.1%3a8088/{url_encoded}:{channel_name}\n")
                        else:
                            file.write(f"#SERVICE {service_type}:0:0:0:0:0:0:0:{url_encoded}\n")
                        file.write(f"#DESCRIPTION {channel_name}\n")
        else:
            # Ako su selektovani kanali
            for channel_name in selected_items:
                for name, url in result:
                    if name == channel_name:
                        url_encoded = url.replace(":", "%3a")
                        if service_type.startswith("streamlink"):
                            if service_type == "streamlink_wrapper":
                                file.write(f"#SERVICE 4097:0:1:0:0:0:0:0:0:0:streamlink%3a//{url_encoded}:{channel_name}\n")
                            else:
                                file.write(f"#SERVICE 4097:0:1:0:0:0:0:0:0:0:http%3a//127.0.0.1%3a8088/{url_encoded}:{channel_name}\n")
                        else:
                            file.write(f"#SERVICE {service_type}:0:0:0:0:0:0:0:{url_encoded}\n")
                        file.write(f"#DESCRIPTION {channel_name}\n")
                        break

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
    result, has_groups = parse_m3u_by_groups(self.selected_file)
    if not result:
        self["message_label"].setText("No content found in file!")
        return
    if has_groups:
        self.session.openWithCallback(self.on_group_selection, GroupSelectionScreen, result)
    else:
        self.session.openWithCallback(self.on_channel_selection, ChannelSelectionScreen, result)

class PlaylistSelectionScreen(Screen):
    skin = """
    <screen name="PlaylistSelectionScreen" position="center,center" size="1200,800" title="..:: Select Playlist Link ::..">
        <widget name="link_list" position="20,20" size="1160,700" scrollbarMode="showAlways" itemHeight="33" font="Regular;28" />
        <widget name="button_red" position="20,740" size="180,40" font="Bold;22" halign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="button_green" position="220,740" size="180,40" font="Bold;22" halign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
    </screen>
    """

    def __init__(self, session, txt_file):
        Screen.__init__(self, session)
        self.txt_file = txt_file
        self.links = self.load_links()

        self["link_list"] = MenuList(self.links, enableWrapAround=True)
        self["button_red"] = Button("Cancel")
        self["button_green"] = Button("Confirm")

        # Ispravljena definicija ActionMap
        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions", "ColorActions"],
            {
                "ok": self.confirm,
                "cancel": self.cancel,
                "up": self["link_list"].up,
                "down": self["link_list"].down,
                "green": self.confirm,
                "red": self.cancel,
            },
            -1
        )

    def load_links(self):
        """Učitavanje linkova iz playlist.txt"""
        links = []
        print(f"Loading links from file: {self.txt_file}")
        try:
            with open(self.txt_file, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line.startswith("http"):
                        links.append(line)
                        print(f"Found link: {line}")
        except Exception as e:
            print(f"Error loading playlist.txt: {str(e)}")
        if not links:
            print("No valid links found in playlist.txt!")
            links = ["No valid links found in file!"]
        else:
            print(f"Total links loaded: {len(links)}")
        return links

    def confirm(self):
        selected_index = self["link_list"].getSelectionIndex()
        if selected_index >= 0 and self.links[selected_index].startswith("http"):
            selected_link = self.links[selected_index]
            print(f"Confirmed link: {selected_link}")
            self.close(selected_link)  # Vraćamo selektovani link
        else:
            print("Invalid or no link selected!")
            self.close(None)

    def cancel(self):
        print("Selection canceled!")
        self.close(None)


class ChannelSelectionScreen(Screen):
    skin = """
    <screen name="ChannelSelectionScreen" position="center,center" size="1200,800" title="..:: Select Channels ::..">
        <widget name="channel_list" position="20,20" size="810,700" scrollbarMode="showAlways" itemHeight="33" font="Regular;28" />
        <widget name="background" position="820,0" size="350,800" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpE2Converter/background3.png" zPosition="-1" alphatest="on" />
        <widget name="button_red" position="20,740" size="180,40" font="Bold;22" halign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="button_green" position="220,740" size="180,40" font="Bold;22" halign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="button_yellow" position="420,740" size="180,40" font="Bold;22" halign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
        <widget name="button_blue" position="620,740" size="180,40" font="Bold;22" halign="center" backgroundColor="#13389F" foregroundColor="#000000" />
    </screen> 
    """

    def __init__(self, session, channels):
        Screen.__init__(self, session)
        self.session = session
        self.all_channels = channels  # Čuvamo originalnu listu svih kanala iz M3U fajla
        self.selected_channels = []

        # Grupisanje serija i kreiranje prikazane liste bez sortiranja
        self.channels = self.process_channels(channels)

        self["channel_list"] = MenuList(self.build_channel_list(), enableWrapAround=True)
        self["background"] = Pixmap()
        self["button_red"] = Button("Cancel")
        self["button_green"] = Button("Confirm")
        self["button_blue"] = Button("Select All")
        self["button_yellow"] = Button("Select Similar")

        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions", "ColorActions"],
            {
                "ok": self.toggle_selection,
                "cancel": self.cancel,
                "up": self["channel_list"].up,
                "down": self["channel_list"].down,
                "green": self.confirm,
                "red": self.cancel,
                "blue": self.select_all,
                "yellow": self.select_similar,
            },
            -1
        )

    def process_channels(self, channels):
        """Grupisanje serija i kreiranje liste za prikaz, očuvanje originalnog redosleda"""
        series_dict = {}
        display_list = []
        seen_series = set()  # Pratimo već viđene serije da ih ne dupliramo

        for channel_name, _ in channels:
            # Provera da li je kanal serija (npr. "The X Files S01 E01")
            series_match = re.match(r"^(.*?)\s+S\d+\s*E\d+$", channel_name, re.IGNORECASE)
            if series_match:
                series_name = series_match.group(1).strip()  # npr. "The X Files"
                if series_name not in series_dict:
                    series_dict[series_name] = []
                series_dict[series_name].append(channel_name)
                # Dodajemo naziv serije samo prvi put kada je vidimo
                if series_name not in seen_series:
                    display_list.append(series_name)
                    seen_series.add(series_name)
            else:
                # Ako nije serija, dodajemo direktno u listu
                display_list.append(channel_name)

        return display_list  # Vraćamo listu bez sortiranja

    def build_channel_list(self):
        return [f"✓ {channel}" if channel in self.selected_channels else f"  {channel}" for channel in self.channels]

    def toggle_selection(self):
        current_index = self["channel_list"].getSelectionIndex()
        if current_index >= 0 and current_index < len(self.channels):
            channel_name = self.channels[current_index]
            if channel_name in self.selected_channels:
                self.selected_channels.remove(channel_name)
            else:
                self.selected_channels.append(channel_name)
            self["channel_list"].setList(self.build_channel_list())

    def select_all(self):
        if set(self.channels) == set(self.selected_channels):
            self.selected_channels = []
        else:
            self.selected_channels = self.channels[:]
        self["channel_list"].setList(self.build_channel_list())

    def select_similar(self):
        current_index = self["channel_list"].getSelectionIndex()
        if current_index < 0 or current_index >= len(self.channels):
            return
        current_channel = self.channels[current_index]

        # Identifikujemo bazni prefiks
        base_pattern = re.match(r"^(.*?)([:\-]\s*|\s+)(.*)$", current_channel)
        if base_pattern:
            base_name = base_pattern.group(1) + base_pattern.group(2)
        else:
            base_name = re.sub(r"\s*(HD|SD|\d+)$", "", current_channel, flags=re.IGNORECASE).strip()

        # Selekcija svih kanala koji počinju sa baznim prefiksom
        for channel in self.channels:
            if channel.startswith(base_name) and channel not in self.selected_channels:
                self.selected_channels.append(channel)
        self["channel_list"].setList(self.build_channel_list())
        print(f"Selected similar channels with prefix: {base_name}")

    def get_full_series_channels(self, series_name):
        """Vraća sve epizode za datu seriju iz originalne liste"""
        series_channels = []
        for channel_name, _ in self.all_channels:
            if re.match(rf"^{re.escape(series_name)}\s+S\d+\s*E\d+$", channel_name, re.IGNORECASE):
                series_channels.append(channel_name)
        return series_channels

    def confirm(self):
        # Proširujemo selekciju da uključimo sve epizode serija
        final_selection = []
        for selected in self.selected_channels:
            if any(re.match(rf"^{re.escape(selected)}\s+S\d+\s*E\d+$", ch[0], re.IGNORECASE) for ch in
                   self.all_channels):
                # Ako je serija, dodajemo sve epizode
                final_selection.extend(self.get_full_series_channels(selected))
            else:
                # Ako nije serija, dodajemo samo selektovani kanal
                final_selection.append(selected)
        Screen.close(self, final_selection)

    def cancel(self):
        Screen.close(self, [])

class GroupSelectionScreen(Screen):
    skin = """
    <screen name="GroupSelectionScreen" position="center,center" size="1200,800" title="..:: Select Groups ::..">
        <widget name="group_list" position="20,20" size="810,700" scrollbarMode="showAlways" itemHeight="33" font="Regular;28" />
        <widget name="background" position="820,0" size="350,800" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpE2Converter/background2.png" zPosition="-1" alphatest="on" />
        <widget name="button_red" position="20,740" size="180,40" font="Bold;22" halign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="button_green" position="220,740" size="180,40" font="Bold;22" halign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="button_yellow" position="420,740" size="180,40" font="Bold;22" halign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
        <widget name="button_blue" position="620,740" size="180,40" font="Bold;22" halign="center" backgroundColor="#13389F" foregroundColor="#000000" />
    </screen>
    """

    def __init__(self, session, groups):
        Screen.__init__(self, session)
        self.session = session
        print(f"GroupSelectionScreen: Received groups = {groups}")
        self.groups = list(groups.keys())  # Samo grupe
        self.selected_groups = []

        # Dijagnostika
        print(f"GroupSelectionScreen: Number of groups = {len(self.groups)}, groups = {self.groups}")
        if not self.groups:
            self.groups = ["No groups found"]

        self["group_list"] = MenuList(self.build_group_list(), enableWrapAround=True)
        self["background"] = Pixmap()
        self["button_red"] = Button("Cancel")
        self["button_green"] = Button("Confirm")
        self["button_blue"] = Button("Select All")
        self["button_yellow"] = Button("Select Similar")

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
                "yellow": self.select_similar,
            },
            -1
        )
        print("GroupSelectionScreen: Initialization complete")

    def build_group_list(self):
        return [f"✓ {group}" if group in self.selected_groups else f"  {group}" for group in self.groups]

    def toggle_selection(self):
        current_index = self["group_list"].getSelectionIndex()
        if current_index >= 0 and current_index < len(self.groups):
            group_name = self.groups[current_index]
            if group_name in self.selected_groups:
                self.selected_groups.remove(group_name)
            else:
                self.selected_groups.append(group_name)
            self["group_list"].setList(self.build_group_list())

    def select_all(self):
        if set(self.groups) == set(self.selected_groups):
            self.selected_groups = []
        else:
            self.selected_groups = self.groups[:]
        self["group_list"].setList(self.build_group_list())

    def select_similar(self):
        current_index = self["group_list"].getSelectionIndex()
        if current_index < 0 or current_index >= len(self.groups):
            return
        current_group = self.groups[current_index]

        # Identifikujemo bazni prefiks
        base_pattern = re.match(r"^(.*?)([:\-]\s*|\s+)(.*)$", current_group)
        if base_pattern:
            base_name = base_pattern.group(1) + base_pattern.group(2)  # npr. "Sport TV ", "XXX:", "EXYU:"
        else:
            # Ako nema separatora, uzimamo ceo naziv do poslednjeg razmaka ili kraja
            base_name = re.sub(r"\s*(HD|SD|\d+)$", "", current_group, flags=re.IGNORECASE).strip()

        # Selekcija svih grupa koje počinju sa baznim prefiksom
        for group in self.groups:
            if group.startswith(base_name) and group not in self.selected_groups:
                self.selected_groups.append(group)
        self["group_list"].setList(self.build_group_list())
        print(f"Selected similar groups with prefix: {base_name}")

    def confirm(self):
        Screen.close(self, self.selected_groups)

    def cancel(self):
        Screen.close(self, [])

class MainScreen(Screen, ConfigListScreen):
    version = "2.0"
    skin = f"""
    <screen name="CiefpE2Converter" position="center,center" size="1600,800" title="..:: CiefpE2Converter v{version} ::..">
        <widget name="background" position="1200,0" size="400,800" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpE2Converter/background.png" zPosition="-1" alphatest="on" />
        <widget name="message_label" position="50,30" size="1100,100" font="Regular;24" valign="top" />
        <widget name="file_list" position="50,150" size="600,580" scrollbarMode="showOnDemand" />
        <widget name="status_label" position="700,150" size="500,580" font="Regular;22" halign="left" valign="top" />
        <widget name="button_red" position="50,750" size="200,40" font="Bold;22" halign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="button_green" position="250,750" size="200,40" font="Bold;22" halign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="button_yellow" position="450,750" size="200,40" font="Bold;22" halign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
        <widget name="button_blue" position="650,750" size="200,40" font="Bold;22" halign="center" backgroundColor="#13389F" foregroundColor="#000000" />
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session  # Čuvamo sesiju eksplicitno
        self._close_method = self.close  # Sačuvajmo originalni close metod
        self.bouquet_name = ConfigText(default="IPTV Mix Bouquet", fixed_size=False)
        ConfigListScreen.__init__(self, [getConfigListEntry("Bouquet Name:", self.bouquet_name)])

        self["background"] = Pixmap()
        self["message_label"] = Label("Select a file and define bouquet name")
        self["status_label"] = Label("")
        self["file_list"] = FileList("/tmp", showDirectories=True, matchingPattern=".*\\.(m3u|m3u8|txt)$")

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
            file_path = os.path.join(self["file_list"].getCurrentDirectory(), selected[0])
            if file_path.endswith(".txt"):
                self.session.openWithCallback(self.on_playlist_selection, PlaylistSelectionScreen, file_path)
            else:
                self.selected_file = file_path
                self["message_label"].setText(
                    f"Bouquet name: {self.bouquet_name.value}\nSelected file: {self.selected_file}")

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
        result, has_groups = parse_m3u_by_groups(self.selected_file)
        print(f"show_groups: has_groups = {has_groups}, result = {result}")
        if not result:
            self["message_label"].setText("No content found in file!")
            return
        if has_groups:
            self.session.openWithCallback(self.on_group_selection, GroupSelectionScreen, result)
        else:
            self.session.openWithCallback(self.on_channel_selection, ChannelSelectionScreen, result)

    def on_group_selection(self, selected_items):
        if selected_items is not None:
            self.selected_groups = selected_items
            self.update_status_label()
        else:
            self["status_label"].setText("Group selection canceled.")

    def on_channel_selection(self, selected_items):
        if selected_items is not None:
            self.selected_groups = selected_items
            self.update_status_label()
        else:
            self["status_label"].setText("Channel selection canceled.")

    def on_playlist_selection(self, selected_link):
        print(f"Selected link from PlaylistSelectionScreen: {selected_link}")
        if selected_link:
            downloaded_file = download_m3u(selected_link)
            if downloaded_file:
                self.selected_file = downloaded_file
                print(f"Assigned downloaded file to selected_file: {self.selected_file}")
                self["message_label"].setText(
                    f"Bouquet name: {self.bouquet_name.value}\nSelected file: {self.selected_file}")
                self.show_groups()
            else:
                self["message_label"].setText("Failed to download M3U file!")
                print("Download failed, no file assigned.")
        else:
            self["message_label"].setText("No link selected!")
            print("No link was selected in PlaylistSelectionScreen.")

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
            Screen.close(self)  # Umesto poziva na _close_method
        except Exception as e:
            print(f"Error during exit: {str(e)}")
            Screen.close(self)  # Osiguraj da se ekran zatvori
