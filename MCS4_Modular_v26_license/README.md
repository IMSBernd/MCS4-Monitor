# MCS4 Monitor – Version 2.4 License RC

This package contains the MCS4 Monitor with a PC-bound offline license system.

## Important workflow

### Local development
1. Run `install_requirements.bat` if needed.
2. Run `create_local_demo_license.bat` once.
3. Run `start_dev.bat`.

### Customer workflow
1. Customer runs `get_machine_id.bat`.
2. Customer sends you the displayed Machine ID.
3. You run `create_customer_license.bat` and enter customer name, Machine ID and license duration, for example 30 days.
4. Send `license.mcs` together with the customer build.

## Included license tools
- `get_machine_id.bat` – reads the current PC ID.
- `create_local_demo_license.bat` – creates a local 30-day demo license for your development PC.
- `create_customer_license.bat` – creates a PC-bound license for a customer Machine ID.
- `check_license.bat` – validates the local license file.

## Notes
- The license is bound to the Machine ID.
- If the PC does not match, the software does not start.
- If the license is expired, the software does not start.
- The current implementation uses an offline signed license file. Keep your distribution ZIP/EXE controlled.
