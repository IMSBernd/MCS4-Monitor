# MCS4 Modular v27 I18N

Version 2.5 adds bilingual UI support.

## New
- Language dropdown in the header: English / Deutsch
- UI labels, tabs, table headers, status messages and export/license messages are loaded from `lang/en.json` and `lang/de.json`
- Keeps the existing PC-bound license system from Version 2.4

## Test
1. Run `create_local_demo_license.bat` if no license exists.
2. Run `start_dev.bat`.
3. Switch the language dropdown between English and Deutsch.
4. Test Simulator, Recorder, Player, Export and Analyzer.

Next planned work: PDF decoder compliance report, full WordType implementation, complete Appendix 12 audit.
