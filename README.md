
# CiefpE2Converter v2.1
![CiefpE2Converter Banner](https://raw.githubusercontent.com/ciefp/CiefpE2Converter/main/preview.jpg)
> **The most advanced M3U to Enigma2 Bouquet converter with group & series support!**  
> Convert any IPTV M3U playlist (local or online) into fully functional Enigma2 bouquets – with smart series detection, multi-group selection, and streamlink support!

---

### Features

- **Smart M3U Parser** – Full support for `#EXTINF` with `group-title`, tvg-name, logos
- **Group-based selection** – Choose only the categories you want (Sport, Movies, XXX, EX-YU, etc.)
- **Smart Series Detection** – Automatically groups episodes like `Breaking Bad S01 E01`
- **Select Similar Channels** – One click to select all "Sport TV", "Arena", "HBO", etc.
- **Online M3U Support** – Load from `playlist.txt` with multiple links
- **Streamlink Integration** – Full support for `http://127.0.0.1:8088/` and `streamlink://`
- **6 Service Types**:
  - GStreamer (4097)
  - Exteplayer3 (5002)
  - DVB (1:0:1)
  - Radio
  - Streamlink (local)
  - Streamlink Wrapper
- **Auto bouquet registration** in `bouquets.tv`
- **Reload bouquets** directly from plugin
- **Clean, modern UI** with background images and color buttons
- **Virtual keyboard** for bouquet naming

---

### Supported Formats

```
.m3u   |   .m3u8   |   .txt (with direct links)
```

Works with:
- X-Streamity
- E2m3u2bouquet
- Jedi Maker Xtream
- Any IPTV provider (Stalker, XC, M3U URL)

---

### Preview

| Main Screen | Group Selection | Series Detection |
|-------------|------------------|------------------|
| ![Main](https://raw.githubusercontent.com/ciefp/CiefpE2Converter/main/screenshot1.jpg) | ![Groups](https://raw.githubusercontent.com/ciefp/CiefpE2Converter/main/screenshot2.jpg) | ![Series](https://raw.githubusercontent.com/ciefp/CiefpE2Converter/main/screenshot3.jpg) |

---

### Installation

#### Method 1: One-click (Recommended)
```bash
wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpE2Converter/main/installer.sh -O - | /bin/sh
```

#### Method 2: Manual
```bash
opkg update
wget https://github.com/ciefp/CiefpE2Converter/archive/refs/heads/main.tar.gz -O /tmp/CiefpE2Converter.tar.gz
tar -xzf /tmp/CiefpE2Converter.tar.gz -C /usr/lib/enigma2/python/Plugins/Extensions/
rm /tmp/CiefpE2Converter.tar.gz
```

> Restart Enigma2 → Find **CiefpE2Converter** in Plugins menu

---

### How to Use

1. Place your `.m3u`, `.m3u8` or `playlist.txt` in **/tmp/**
2. Open **CiefpE2Converter**
3. Select file → Press **Blue** to choose groups/channels
4. Use **Yellow** to select similar (e.g. all "HBO", "Sport", "EXYU")
5. Press **Green** → Choose service type
6. Enter bouquet name → **Convert**
7. Reload bouquets → Done!

---

### playlist.txt Example (for online lists)

```txt
http://provider.com/get.php?username=USER&password=PASS&type=m3u_plus&output=ts
http://second-provider.com/playlist.m3u8
https://free-iptv.github.io/list.m3u
```

→ Plugin will download and let you choose which one to convert!

---

### File Locations

- Plugin: `/usr/lib/enigma2/python/Plugins/Extensions/CiefpE2Converter/`
- Downloaded M3U: `/tmp/m3u_playlist/`
- Output bouquets: `/etc/enigma2/userbouquet.*.tv`
- Registered in: `/etc/enigma2/bouquets.tv`

---

### Requirements

- Python 3
- Enigma2 image (OpenATV, OpenPLI, VTI, BlackHole, etc.)
- For Streamlink: `opkg install streamlinksrv`

---

### Changelog

**v2.1** (November 2025)
- Added **online M3U downloader** from `playlist.txt`
- Smart **series detection** (S01 E01 → grouped automatically)
- **Select Similar** button (Yellow) – grabs all channels with same prefix
- Improved **streamlink wrapper** support
- Auto directory creation for downloads
- Better error handling & logging
- New backgrounds and modern UI
- Fixed bouquet registration duplicates

---

### Known Compatible Plugins

| Plugin | Compatible? | Notes |
|-------|-------------|-------|
| X-Streamity | Yes | Use Streamlink mode |
| Jedi Maker Xtream | Yes | Use 4097 or 5002 |
| E2m3u2bouquet | Yes | Full replacement |
| XCplugin | Yes | Use GStreamer |

---

### Credits

- **Developer**: ciefp  
- **Tested on**: OpenATV 7.4, OpenPLI 9, BlackHole 4.4

---

### Support

Stuck? Need help?

- Open an **Issue** on GitHub
- Join: [LinuxSat-Support](https://www.linuxsat-support.com)

- Telegram: ciefpsettings
- Facebook: ciefpsettings

---

### Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ciefp/CiefpE2Converter&type=Date)](https://star-history.com/#ciefp/CiefpE2Converter&Date)
