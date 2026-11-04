# O'zbek lotin 2026 klaviaturasi — Linux uchun

> Uzbek Latin 2026 keyboard layouts (ö ş ğ ç ʻ ʼ) ported from a Windows MSKLC installer to Linux XKB, plus an IBus double-press input method.

Windows uchun chiqarilgan `UzbekKeyboardSetup.exe` o'rnatuvchisidagi 3 ta klaviatura Linux'ga (XKB) ko'chirildi. Bundan tashqari, AltGr'siz yozish uchun **ikki marta bosish** usuli qo'shildi (`ss` → ş).

GNOME, KDE Plasma, XFCE, Cinnamon va MATE muhitlarida, X11'da ham, Wayland'da ham ishlaydi. Ubuntu 26.04 (GNOME, Wayland) da sinab ko'rilgan.

## Tez o'rnatish

```bash
git clone https://github.com/<foydalanuvchi>/uz-klaviatura-linux.git
cd uz-klaviatura-linux
sudo python3 uz_klaviatura_linux.py install      # dist/uz26 ni tizimga o'rnatadi
python3 uz_klaviatura_linux.py gnome classic     # GNOME'ga qo'shadi (classic | direct | turkish)
```

So'ng tizimdan chiqib qayta kiring. `Super`+`Space` bosilsa "en" ↔ "uz" almashadi.

## Variantlar

`AltGr` — o'ng tomondagi Alt tugmasi.

| Harf | Klassik (`classic`) | To'g'ridan-to'g'ri (`direct`) | Turkcha uslub (`turkish`) |
|---|---|---|---|
| ö / Ö | `AltGr`+`O` | `[` | `[` |
| ş / Ş | `AltGr`+`S` | `;` | `;` |
| ğ / Ğ | `AltGr`+`G` | `'` | `'` |
| ç / Ç | `AltGr`+`C` | `C` (oddiy c = `AltGr`+`C`) | `,` (vergul = `\`) |
| ʼ / ʻ | `AltGr`+`'` / `AltGr`+`Shift`+`'` | `AltGr`+`]` / `AltGr`+`Shift`+`]` | `AltGr`+`]` / `AltGr`+`Shift`+`]` |

Klassik variantda qolgan barcha tugmalar US klaviaturadagi joyida qoladi. Qolgan ikki variantda joyidan surilgan `[ ; ' , \` belgilari `AltGr` bilan yoziladi.

### Ikki marta bosish usuli (AltGr'siz)

```bash
sudo apt install ibus-m17n
python3 uz_klaviatura_linux.py double
```

| Bosiladi | Chiqadi |
|---|---|
| `ss` / `cc` / `gg` / `oo` | ş / ç / ğ / ö |
| `Ss` yoki `SS` | Ş (qolgan harflarda ham shunday) |
| `sss` | ss — so'zda haqiqatan ikkita harf kerak bo'lganda: `kasssa` → kassa |

## Qanday ishlaydi

`.exe` fayl aslida .NET dasturi bo'lib, ichida Microsoft Keyboard Layout Creator (MSKLC) formatidagi 3 ta `.klc` fayl saqlangan. Skript ularni ajratib oladi va XKB formatiga o'giradi:

```
UzbekKeyboardSetup.exe ──extract──▶ *.klc (UTF-16LE) ──convert──▶ uz26 (XKB) ──install──▶ /usr/share/X11/xkb
```

| MSKLC (.klc) | Linux (XKB) | Misol |
|---|---|---|
| Skan-kod | Tugma nomi | `18` → `<AD09>` (O tugmasi) |
| Unicode kod | Keysym | `00f6` → `odiaeresis` (ö) |
| Ustunlar 0 / 1 / 6 / 7 | Darajalar 1–4 | oddiy, Shift, AltGr, AltGr+Shift |
| `Cap` bayrog'i | Tugma turi | `5` → `FOUR_LEVEL_ALPHABETIC` |

XKB har bir tugmani alohida qayta ishlaydi va oldingi bosishni eslab qolmaydi. Shuning uchun ikki marta bosish usuli XKB orqali emas, IBus + m17n kiritish usuli (`.mim` fayli) bilan qilingan.

### Asl `.exe` dan qayta yig'ish

`.exe` fayl repozitoriyga kiritilmagan (u muallifning fayli). Agar u sizda bo'lsa:

```bash
python3 uz_klaviatura_linux.py extract UzbekKeyboardSetup.exe   # uz26_build/*.klc
python3 uz_klaviatura_linux.py convert                          # uz26_build/uz26
sudo python3 uz_klaviatura_linux.py install
```

## Muammolar va yechimlar

**GNOME'da klaviatura ham, til ko'rsatkichi ham ko'rinmaydi.** GNOME `rules/evdev.xml` faylini `xkb.dtd` bo'yicha qat'iy tekshiradi. `<configItem>` ichida `countryList` elementi `languageList` dan oldin kelishi shart, tartib buzilsa butun fayl rad etiladi. Skript to'g'ri tartibda yozadi. Tekshirish uchun:

```bash
cd /usr/share/X11/xkb/rules && xmllint --noout --valid evdev.xml && echo VALID
```

**Wayland'da `AltGr` ishlamaydi.** O'ng Alt'ni majburan AltGr qilish kerak (`gnome` buyrug'i buni o'zi bajaradi):

```bash
gsettings set org.gnome.desktop.input-sources xkb-options "['lv3:ralt_switch']"
```

**Yangilanishdan keyin klaviatura ro'yxatdan yo'qoldi.** `xkeyboard-config` paketi yangilanganda `evdev.xml` qayta yoziladi. Bunday holda `sudo python3 uz_klaviatura_linux.py install` ni qayta ishga tushiring.

## O'chirish

```bash
sudo python3 uz_klaviatura_linux.py uninstall
gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'us')]"
rm -f ~/.m17n.d/uz-latin2026.mim
```

## Fayllar

| Fayl | Vazifasi |
|---|---|
| `uz_klaviatura_linux.py` | Butun jarayon: ajratish, o'girish, o'rnatish, ikki marta bosish |
| `dist/uz26` | Tayyor XKB fayli (3 ta variant) |
| `dist/uz-latin2026.mim` | Tayyor IBus/m17n kiritish usuli |

## Muallif

Safarboyev Sarvar — TATU, Dasturiy injiniring fakulteti.

Klaviatura joylashuvlari asl `UzbekKeyboardSetup.exe` dan olingan. Ushbu repozitoriydagi kod [MIT litsenziyasi](LICENSE) asosida tarqatiladi.
