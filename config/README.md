# MCS4 Monitor - Version 3.2.0 Phase A Regression

This version adds the first automated Phase A regression test suite.

## New

- `database/appendix12.json` is included as data file instead of being created only at runtime.
- `tests/regression_phase_a.py` validates:
  - WordType / flag bit extraction
  - Page / Line decoding
  - 12-bit value decoding with sign and sensor fault
  - mixed 5-byte / 8-byte frame reading
  - WordType 0 decoding
  - Appendix 12 required simulator entries
- `run_regression_tests.bat` starts the tests from Windows.
- Decoder Compliance entry for regression testing updated.

## Start application

```cmd
start_dev.bat
```

## Run regression tests

```cmd
run_regression_tests.bat
```

Optional with MCS log files:

```cmd
run_regression_tests.bat recordings\example.mcslog
```
