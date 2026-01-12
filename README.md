# Polar Verity Sense Batter Monitor for Home Assistant

A Home Assistant custom component that integrates the Polar Verity Sense optical heart rate monitor via Bluetooth, providing battery level monitoring and alerts.

## Requirements

- Home Assistant 2023.1 or later
- Bluetooth adapter on your Home Assistant server
- Polar Verity Sense optical heart rate sensor

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/polar_verity_sense` folder to your Home Assistant's `custom_components` directory
2. If the `custom_components` directory doesn't exist, create it in the same location as your `configuration.yaml`
3. Restart Home Assistant

```
config/
└── custom_components/
    └── polar_verity_sense/
        ├── __init__.py
        ├── manifest.json
        ├── const.py
        ├── config_flow.py
        └── sensor.py
```

## Configuration

### Setup via UI

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Polar Verity Sense"
4. Select your device from the list of discovered devices
5. Click **Submit**

Your Polar Verity Sense battery sensor will now be available as `sensor.polar_verity_sense_battery`

### Making Your Device Discoverable

Make sure your Polar Verity Sense is:
- Powered on
- Within Bluetooth range of your Home Assistant server
- Not connected to another device (like your phone)

## Usage

### Battery Sensor

The integration creates a battery sensor entity:
- **Entity ID**: `sensor.polar_verity_sense_battery`
- **Device Class**: Battery
- **Unit**: Percentage (%)
- **Update Interval**: 5 minutes (configurable in `const.py`)

### Example Automations

#### Low Battery Alert

Get notified when battery drops below 20%:

```yaml
automation:
  - alias: "Polar Low Battery Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.polar_verity_sense_battery
        below: 20
    action:
      - service: notify.notify
        data:
          title: "Polar Verity Sense Low Battery"
          message: "Battery is at {{ states('sensor.polar_verity_sense_battery') }}%. Please charge soon."
```

#### Daily Battery Report

Get a daily status update:

```yaml
automation:
  - alias: "Daily Polar Battery Report"
    trigger:
      - platform: time
        at: "09:00:00"
    action:
      - service: notify.notify
        data:
          message: "Polar Verity Sense battery: {{ states('sensor.polar_verity_sense_battery') }}%"
```

#### Charge Reminder

Persistent notification when battery is low, cleared when charged:

```yaml
automation:
  - alias: "Polar Charge Reminder"
    trigger:
      - platform: numeric_state
        entity_id: sensor.polar_verity_sense_battery
        below: 20
    action:
      - service: persistent_notification.create
        data:
          title: "Charge Polar Verity Sense"
          message: "Battery level: {{ states('sensor.polar_verity_sense_battery') }}%"
          notification_id: polar_low_battery

  - alias: "Clear Polar Charge Reminder"
    trigger:
      - platform: numeric_state
        entity_id: sensor.polar_verity_sense_battery
        above: 80
    action:
      - service: persistent_notification.dismiss
        data:
          notification_id: polar_low_battery
```

### Dashboard Card

Add a simple gauge card to your dashboard:

```yaml
type: gauge
entity: sensor.polar_verity_sense_battery
name: Polar Verity Sense
min: 0
max: 100
severity:
  green: 50
  yellow: 30
  red: 0
```

## Configuration Options

You can customize the update interval by editing `const.py`:

```python
DEFAULT_SCAN_INTERVAL = 300  # Seconds (5 minutes)
```

Available options:
- `300` (5 minutes) - Default, good balance
- `600` (10 minutes) - Less frequent for longer battery life
- `60` (1 minute) - More frequent monitoring

After changing, restart Home Assistant.

## Troubleshooting

### Device Not Found

- Ensure your Polar Verity Sense is powered on
- Make sure it's not connected to another device
- Verify Bluetooth is enabled in Home Assistant
- Check that your Bluetooth adapter has sufficient range

### Connection Issues

- Try restarting the Polar Verity Sense
- Restart Home Assistant's Bluetooth integration
- Check Home Assistant logs for detailed error messages

### Check Logs

View logs in Home Assistant:
1. Go to **Settings** → **System** → **Logs**
2. Search for "polar_verity_sense"

Or view the full log file:
```bash
tail -f /config/home-assistant.log | grep polar
```

## Technical Details

### Bluetooth Specifications

- **Service UUID**: `0000180f-0000-1000-8000-00805f9b34fb` (Battery Service)
- **Characteristic UUID**: `00002a19-0000-1000-8000-00805f9b34fb` (Battery Level)
- **Connection Type**: Bluetooth Low Energy (BLE)

### Dependencies

- `bleak-retry-connector>=3.1.1` - Bluetooth connection management

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Thanks to Polar for creating great fitness sensors
- Home Assistant community for the excellent platform and documentation

## Support

If you encounter any issues or have questions:
- Open an issue on GitHub
- Check the Home Assistant community forums
- Review the troubleshooting section above

## Changelog

### Version 1.0.0
- Initial release
- Battery level monitoring
- Auto-discovery support
- Config flow UI setup