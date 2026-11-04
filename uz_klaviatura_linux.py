#!/usr/bin/env python3
"""
O'zbek lotin 2026 klaviaturasini Windows'dan Linux'ga ko'chirish
================================================================

Muallif: Safarboyev Sarvar (TATU, Dasturiy injiniring fakulteti)

Vazifa
------
Windows uchun berilgan UzbekKeyboardSetup.exe o'rnatuvchisini Linux'da ishlatish.

Yechim bosqichlari
------------------
1. Tahlil: .exe — bu .NET dasturi. Uning ichida Microsoft Keyboard Layout Creator (MSKLC)
   formatidagi 3 ta .klc fayl joylashtirilgan (UTF-16LE matn, "KBD" bilan boshlanib,
   "ENDKBD" bilan tugaydi).
2. Ajratish: .exe baytlari ichidan shu .klc matnlarini qidirib, kesib olamiz.
3. O'girish: .klc dagi har bir tugma (skan-kod + 4 ta daraja: oddiy, Shift, AltGr,
   AltGr+Shift) Linux XKB formatiga o'tkaziladi:
     Windows skan-kodi  ->  XKB tugma nomi  (masalan 0x18 -> <AD09>, ya'ni O tugmasi)
     Unicode kod        ->  XKB keysym       (masalan 00f6 -> odiaeresis, ya'ni ö)
     CapsLock bayrog'i  ->  XKB tugma turi   (ALPHABETIC / FOUR_LEVEL_SEMIALPHABETIC ...)
4. O'rnatish: natijaviy fayl /usr/share/X11/xkb/symbols/uz26 ga yoziladi va GNOME/KDE
   sozlamalarida ko'rinishi uchun rules/evdev.xml ro'yxatiga qo'shiladi.
   Muhim: evdev.xml xkb.dtd bo'yicha tekshiriladi, shuning uchun <configItem> ichidagi
   elementlar tartibi qat'iy (countryList, languageList'dan OLDIN keladi). Tartib
   buzilsa, GNOME butun ro'yxatni rad etadi.
5. Qo'shimcha usul (ikki marta bosish): ss -> ş, cc -> ç, gg -> ğ, oo -> ö.
   Bu XKB bilan bo'lmaydi (XKB oldingi bosishni eslab qolmaydi), shuning uchun
   IBus + m17n kiritish usuli (.mim fayli) yaratiladi.

Ishlatish
---------
  python3 uz_klaviatura_linux.py extract UzbekKeyboardSetup.exe   # .klc fayllarni ajratish
  python3 uz_klaviatura_linux.py convert                          # .klc -> uz26 (XKB)
  sudo python3 uz_klaviatura_linux.py install                     # tizimga o'rnatish
                                                                  # (.exe bo'lmasa dist/uz26 ishlatiladi)
  python3 uz_klaviatura_linux.py gnome classic                    # GNOME'ga qo'shish (AltGr usuli)
  python3 uz_klaviatura_linux.py double                           # ikki marta bosish usuli
  sudo python3 uz_klaviatura_linux.py uninstall                   # o'chirish
"""

import os
import re
import shutil
import subprocess
import sys

XKB_DIR = os.environ.get("XKB_DIR", "/usr/share/X11/xkb")
OUT_DIR = "uz26_build"

# .klc fayl nomi -> (XKB variant nomi, tavsif)
VARIANTS = {
    "uzlat26": ("classic", "Uzbek (Latin 2026, Classic)"),
    "uzlt26d": ("direct", "Uzbek (Latin 2026, Direct)"),
    "uzlt26t": ("turkish", "Uzbek (Latin 2026, Turkish-style)"),
}

# Windows skan-kodi -> XKB tugma nomi (evdev keycodes)
SCANCODE_TO_XKB = {
    0x29: "TLDE", 0x02: "AE01", 0x03: "AE02", 0x04: "AE03", 0x05: "AE04", 0x06: "AE05",
    0x07: "AE06", 0x08: "AE07", 0x09: "AE08", 0x0A: "AE09", 0x0B: "AE10", 0x0C: "AE11",
    0x0D: "AE12",
    0x10: "AD01", 0x11: "AD02", 0x12: "AD03", 0x13: "AD04", 0x14: "AD05", 0x15: "AD06",
    0x16: "AD07", 0x17: "AD08", 0x18: "AD09", 0x19: "AD10", 0x1A: "AD11", 0x1B: "AD12",
    0x1E: "AC01", 0x1F: "AC02", 0x20: "AC03", 0x21: "AC04", 0x22: "AC05", 0x23: "AC06",
    0x24: "AC07", 0x25: "AC08", 0x26: "AC09", 0x27: "AC10", 0x28: "AC11", 0x2B: "BKSL",
    0x2C: "AB01", 0x2D: "AB02", 0x2E: "AB03", 0x2F: "AB04", 0x30: "AB05", 0x31: "AB06",
    0x32: "AB07", 0x33: "AB08", 0x34: "AB09", 0x35: "AB10", 0x56: "LSGT",
}

# Belgi -> XKB keysym nomi. Ro'yxatda yo'q belgilar U+XXXX ko'rinishida yoziladi.
# ASCII belgilarni nomi bilan yozish shart: aks holda klaviatura yorliqlari (Ctrl+C va h.k.) buziladi.
KEYSYM_NAMES = {
    " ": "space", "!": "exclam", '"': "quotedbl", "#": "numbersign", "$": "dollar",
    "%": "percent", "&": "ampersand", "'": "apostrophe", "(": "parenleft", ")": "parenright",
    "*": "asterisk", "+": "plus", ",": "comma", "-": "minus", ".": "period", "/": "slash",
    ":": "colon", ";": "semicolon", "<": "less", "=": "equal", ">": "greater",
    "?": "question", "@": "at", "[": "bracketleft", "\\": "backslash", "]": "bracketright",
    "^": "asciicircum", "_": "underscore", "`": "grave", "{": "braceleft", "|": "bar",
    "}": "braceright", "~": "asciitilde",
    "ö": "odiaeresis", "Ö": "Odiaeresis", "ç": "ccedilla", "Ç": "Ccedilla",
    "ş": "scedilla", "Ş": "Scedilla", "ğ": "gbreve", "Ğ": "Gbreve",
}


# ---------------------------------------------------------------- 1-2. Ajratish
def extract(exe_path):
    """.exe ichidan UTF-16LE .klc matnlarini topib, alohida fayllarga yozadi."""
    data = open(exe_path, "rb").read()
    start_sig = b"\xff\xfe" + "KBD".encode("utf-16le")  # BOM + "KBD"
    end_sig = "ENDKBD".encode("utf-16le")
    os.makedirs(OUT_DIR, exist_ok=True)
    found = []
    for m in re.finditer(re.escape(start_sig), data):
        end = data.find(end_sig, m.start())
        if end < 0:
            continue
        text = data[m.start():end + len(end_sig)].decode("utf-16le").lstrip("﻿")
        name = re.match(r"KBD\t(\S+)", text).group(1)
        path = os.path.join(OUT_DIR, name + ".klc")
        open(path, "w", encoding="utf-8").write(text)
        found.append(path)
        print("  ajratildi:", path)
    if not found:
        sys.exit("Xato: .exe ichida .klc topilmadi")
    return found


# ---------------------------------------------------------------- 3. O'girish
def to_keysym(value):
    """KLC qiymatini (masalan 'a', '00f6', '-1') XKB keysym nomiga aylantiradi."""
    if value in ("-1", ""):
        return None
    if value.endswith("@"):
        raise ValueError("O'lik tugmalar (dead keys) qo'llab-quvvatlanmaydi: " + value)
    ch = value if len(value) == 1 else chr(int(value, 16))
    if ch.isascii() and ch.isalnum():
        return ch
    return KEYSYM_NAMES.get(ch, "U%04X" % ord(ch))


def parse_klc(path):
    """.klc LAYOUT bo'limidan (skan-kod, caps bayrog'i, [daraja1..daraja4]) ro'yxatini qaytaradi.
    KLC ustunlari: SC VK Cap  0(oddiy) 1(Shift) 2(Ctrl) 6(AltGr) 7(AltGr+Shift)"""
    text = open(path, encoding="utf-8").read()
    body = text.split("\nLAYOUT", 1)[1]
    body = re.split(r"\n(?:DEADKEY|KEYNAME|LIGATURE|DESCRIPTIONS)", body)[0]
    keys = []
    for line in body.splitlines():
        cols = line.split("//")[0].split()
        if len(cols) < 8 or not re.fullmatch(r"[0-9a-fA-F]{2}", cols[0]):
            continue
        sc = int(cols[0], 16)
        if sc not in SCANCODE_TO_XKB:
            continue  # bo'sh joy, raqamli klaviatura — US'dagidek qoladi
        caps = int(cols[2])
        levels = [to_keysym(cols[3]), to_keysym(cols[4]), to_keysym(cols[6]), to_keysym(cols[7])]
        keys.append((sc, caps, levels))
    return keys


def xkb_key_line(sc, caps, levels):
    """Bitta tugma uchun XKB qatorini yasaydi. CapsLock bayrog'i tugma turini belgilaydi:
    1 -> CapsLock harfga ta'sir qiladi, 4 -> AltGr darajasiga ham ta'sir qiladi."""
    if levels[2] is None and levels[3] is None:
        syms = levels[:2]
        kind = "ALPHABETIC" if caps & 1 else "TWO_LEVEL"
    else:
        syms = [s or "NoSymbol" for s in levels]
        if caps & 4:
            kind = "FOUR_LEVEL_ALPHABETIC"
        elif caps & 1:
            kind = "FOUR_LEVEL_SEMIALPHABETIC"
        else:
            kind = "FOUR_LEVEL"
    return '    key <%s> { type[Group1]="%s", [ %s ] };' % (SCANCODE_TO_XKB[sc], kind, ", ".join(syms))


def convert():
    """Barcha .klc fayllarni bitta XKB symbols fayliga (uz26) o'giradi."""
    parts = ["// O'zbek lotin 2026 klaviaturasi (UzbekKeyboardSetup.exe dan o'girilgan)\n"]
    for i, (klc, (variant, desc)) in enumerate(VARIANTS.items()):
        path = os.path.join(OUT_DIR, klc + ".klc")
        lines = [
            ("default " if i == 0 else "") + "partial alphanumeric_keys",
            'xkb_symbols "%s" {' % variant,
            '    include "us(basic)"',            # asos — US klaviatura
            '    name[Group1] = "%s";' % desc,
            "",
        ]
        lines += [xkb_key_line(*k) for k in parse_klc(path)]
        lines += ["", '    include "level3(ralt_switch)"', "};", ""]  # o'ng Alt = AltGr
        parts.append("\n".join(lines))
        print("  o'girildi: %s -> uz26(%s)" % (klc, variant))
    out = os.path.join(OUT_DIR, "uz26")
    open(out, "w", encoding="utf-8").write("\n".join(parts))
    print("  natija:", out)
    return out


# ---------------------------------------------------------------- 4. O'rnatish
REGISTRY_BLOCK = """<!-- uz26-begin -->
    <layout>
      <configItem>
        <name>uz26</name>
        <shortDescription>uz</shortDescription>
        <description>Uzbek (Latin 2026)</description>
        <countryList><iso3166Id>UZ</iso3166Id></countryList>
        <languageList><iso639Id>uzb</iso639Id></languageList>
      </configItem>
      <variantList>
%s      </variantList>
    </layout>
<!-- uz26-end -->
""" % "".join(
    "        <variant><configItem><name>%s</name><description>%s</description></configItem></variant>\n"
    % v for v in VARIANTS.values())
BLOCK_RE = re.compile(r"<!-- uz26-begin -->.*?<!-- uz26-end -->\n?", re.S)


def registry_files():
    """evdev.xml va base.xml (ular bitta faylga havola bo'lishi mumkin — takrorlamaymiz)."""
    seen = set()
    for name in ("evdev.xml", "base.xml"):
        p = os.path.realpath(os.path.join(XKB_DIR, "rules", name))
        if os.path.isfile(p) and p not in seen:
            seen.add(p)
            yield p


def install():
    src = os.path.join(OUT_DIR, "uz26")
    if not os.path.exists(src):
        # .exe dan o'girilmagan bo'lsa — repozitoriydagi tayyor dist/uz26 ishlatiladi
        src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "uz26")
    shutil.copy(src, os.path.join(XKB_DIR, "symbols", "uz26"))
    print("  o'rnatildi:", os.path.join(XKB_DIR, "symbols", "uz26"))
    for p in registry_files():
        text = BLOCK_RE.sub("", open(p, encoding="utf-8").read())
        pos = text.find("</layoutList>")
        pos = text.rfind("\n", 0, pos) + 1  # qator boshiga qo'yamiz
        open(p, "w", encoding="utf-8").write(text[:pos] + REGISTRY_BLOCK + text[pos:])
        print("  ro'yxatga qo'shildi:", p)
    print("Tayyor. Tizimdan chiqib qayta kiring.")


def uninstall():
    for p in registry_files():
        text = open(p, encoding="utf-8").read()
        open(p, "w", encoding="utf-8").write(BLOCK_RE.sub("", text))
    sym = os.path.join(XKB_DIR, "symbols", "uz26")
    if os.path.exists(sym):
        os.remove(sym)
    print("O'chirildi.")


def gsettings(key, value):
    subprocess.run(["gsettings", "set", "org.gnome.desktop.input-sources", key, value], check=True)


def gnome(variant="classic"):
    """GNOME kirish manbalariga qo'shadi va o'ng Alt'ni AltGr qiladi (Wayland uchun shart)."""
    gsettings("sources", "[('xkb', 'us'), ('xkb', 'uz26+%s')]" % variant)
    gsettings("xkb-options", "['lv3:ralt_switch']")
    print("GNOME: us + uz26(%s). Almashtirish: Super+Space" % variant)


# ---------------------------------------------------------------- 5. Ikki marta bosish
def double_press():
    """IBus + m17n uchun .mim kiritish usulini yaratadi:
    ss->ş cc->ç gg->ğ oo->ö;  uch marta bosilsa ikki harf qoladi (sss->ss)."""
    rules = []
    for low, special in (("s", "ş"), ("c", "ç"), ("g", "ğ"), ("o", "ö")):
        up, sp_up = low.upper(), special.upper()
        rules += [
            '  ("%s" ?%s)' % (low * 2, special), '  ("%s" "%s")' % (low * 3, low * 2),
            '  ("%s" ?%s)' % (up * 2, sp_up), '  ("%s%s" ?%s)' % (up, low, sp_up),
            '  ("%s" "%s")' % (up * 3, up * 2), '  ("%s%s" "%s%s")' % (up, low * 2, up, low),
        ]
    mim = (
        "(input-method uz latin2026)\n"
        '(description "Uzbek Latin 2026: ss->ş cc->ç gg->ğ oo->ö, sss->ss")\n'
        '(title "UZ")\n'
        "(map\n (trans\n" + "\n".join(rules) + "))\n"
        "(state\n (init\n  (trans)))\n"
    )
    folder = os.path.expanduser("~/.m17n.d")
    os.makedirs(folder, exist_ok=True)
    open(os.path.join(folder, "uz-latin2026.mim"), "w", encoding="utf-8").write(mim)
    print("  yaratildi: ~/.m17n.d/uz-latin2026.mim  (kerak: sudo apt install ibus-m17n)")
    gsettings("sources", "[('xkb', 'us'), ('ibus', 'm17n:uz:latin2026')]")
    gsettings("xkb-options", "[]")
    subprocess.run(["ibus", "restart"], check=False)
    print("GNOME: us + UZ (ikki marta bosish). Almashtirish: Super+Space")


# ---------------------------------------------------------------- Asosiy
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "extract" and len(sys.argv) > 2:
        extract(sys.argv[2])
    elif cmd == "convert":
        convert()
    elif cmd == "install":
        install()
    elif cmd == "uninstall":
        uninstall()
    elif cmd == "gnome":
        gnome(sys.argv[2] if len(sys.argv) > 2 else "classic")
    elif cmd == "double":
        double_press()
    else:
        print(__doc__)
