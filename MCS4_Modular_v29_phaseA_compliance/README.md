# MCS4 Monitor Version 2.6 - Phase A Decoder Compliance

This release adds the first Phase A compliance module.

New:
- New tab: Decoder Compliance / Decoder-Konformität / مطابقة المفكك
- PDF-to-software audit table for MCS-4 telegram parsing
- Compliance rows for RS422, Sync, WordType, flags, telegram length, Data Value, Page/Line, 12-bit data field and remaining open WordTypes
- Excel export now includes a Decoder Compliance sheet
- Multilingual labels for English, German and Arabic

Important:
- This version does not yet complete all WordType decoders.
- It documents what is implemented, what is partial, and what remains open.
- Next Phase A steps are dedicated WordType decoders and full Appendix 12 audit.

Start:
```cmd
start_dev.bat
```


## v2.6.1 Fix
- Decoder Compliance table is now populated automatically at application startup.
- Content is visible even before Simulator/RS422/Player is started.
