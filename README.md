# W910 WebDriver

Open-source browser configurator for the SXS/YXT W910 macro keyboard. It communicates directly with the device through WebHID or Web Bluetooth, without the vendor driver or application.

**[Open W910 WebDriver](https://luftaquila.github.io/w910-webdriver/)**

W910 WebDriver provides full control of both onboard profiles, Normal/Fn key mappings, macros, lighting, and power settings.

## Compatibility

- Desktop Chrome or Edge.
- USB, 2.4 GHz receiver, and Bluetooth configuration supported.
- Bluetooth: switch to `BT`, then hold the bottom RGB light switch for three seconds before connecting.

The browser may identify the keyboard as `YXT K100 Keyboard`.

## Known limits

- Bluetooth reconnection after a page reload requires pairing mode in default Chrome.

## Usage

1. Connect the W910 over USB, its 2.4 GHz receiver, or Bluetooth.
2. Open W910 WebDriver and select the matching connection button.
3. Choose the keyboard in the browser permission dialog.

Export a backup before making large changes. Do not run the vendor configurator at the same time.

## Local development

```sh
npm run serve
```

Open <http://localhost:8000/>.

```sh
npm test
npm run test:python
```

## Reverse engineering

The complete workflow was performed autonomously end-to-end by an LLM agent:

- Vendor software extraction, static analysis, and protocol reconstruction.
- HID frame capture and readback validation on the physical keyboard.
- WebHID implementation, automated tests, documentation, and deployment.

Technical references:

- [Protocol reference](PROTOCOL.md)
- [Firmware extraction status](FIRMWARE.md)
- [Protocol tools](tools/README.md)

Vendor binaries, extracted resources, and packet captures are not included.
