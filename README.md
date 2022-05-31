# Cura Network Plugin for Monoprice Select Mini V2

This [plugin](https://marketplace.ultimaker.com/app/cura/plugins/loociano/MPSM2NetworkPrinting)
for [Cura](https://github.com/ultimaker/cura) enables network interoperability
with Monoprice Select Mini V2 printers.

Plugin is compatible with Monoprice Select Mini V1 and Delta printers, with
limited support ⁠—I do not own these.

_This software is unofficial and not affiliated with Monoprice. Use at your own
risk._

## Donate

If this plugin was useful to you, please consider making a donation.

[![paypal](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/paypal.png?raw=true)](https://paypal.me/loociano)
[![revolut](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/revolut.png?raw=true)](https://revolut.me/loociano)

[Or donate with credit card](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=AHZG8HGU4GM8G)

## Requirements

1. Setup Wi-Fi on the printer,
   by [following one of these methods](https://www.mpselectmini.com/wifi/start).

   Once completed, the printer's IP address should appear on the LCD screen.
   Example: `192.168.0.136`.

1. Install [Cura 4.4.0](https://ultimaker.com/software/ultimaker-cura) or newer.

## How to install this plugin

1. On Cura, click on the Marketplace button on the top right corner.

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/marketplace.png?raw=true)

2. Find and select **Monoprice Select Mini V2**

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-marketplace.png?raw=true)

3. Click Install
4. Restart Cura.

## How to use

1. In Cura, go to Settings → Printer →  **Add Printer**.

1. Click **Add printer by IP**.

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-add-a-printer.png?raw=true)

1. Type network address and click **Add**.

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-add-printer-by-ip-address.png?raw=true)

1. If connection is successful, the printer details are displayed. Click **Connect**.

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-add-printer-by-ip-address-connect.png?raw=true)

1. Click **Next** to select default Machine Settings.

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-machine-settings.png?raw=true)

1. The printer is added. You may check the status of the printer in the **
   Monitor** tab.

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-monitor-tab.png?raw=true)

1. To start a print, slice a model and click **Print over network**.

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-prepare-model.png?raw=true)

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-sending-print-job.png?raw=true)

## Frequently Asked Questions (FAQ)

### Does the plugin require additional hardware?

No. The plugin uses the printer's built-in Wi-Fi.

### Does the plugin stream gcode to the printer?

No. The plugin transfers all the gcode at once. This is equivalent to copying
the gcode file to the SD Card via USB or uploading with the Web UI. Only when
the full model is transferred, print starts.

### Does the plugin transfer the model reliably?

Yes. The plugin transfers the model
using [TCP](https://en.wikipedia.org/wiki/Transmission_Control_Protocol), which
provides reliable delivery of data.

### How fast does the plugin transfer models?

It depends on the model's size and detail. Expect less than a minute for small
models, and between 2-10 minutes for larger ones.

## Troubleshooting

### Cannot connect to the printer

**Update to Cura 4.7 or later**. In earlier versions, you need to temporarily
disable the **UM3 Network Printing** plugin to add the printer over the network.
Go to Marketplace → Installed and disable **UM3 Network Printing** plugin.
Restart Cura to apply changes.

![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/um3-network-printing-disabled.png?raw=true)

### How do I report an issue?

Please file
an [issue](https://github.com/loociano/MPSM2NetworkPrinting/issues/new) (
requires a GitHub account). If you do not have a GitHub account, feel free to
post in
the [Facebook group](https://www.facebook.com/groups/MP.Select.Mini.Owners) or
the [subreddit](https://www.reddit.com/r/MPSelectMiniOwners).

## Development

* Clone or download
  this [repository](https://github.com/loociano/MPSM2NetworkPrinting) into
  Cura's user plugins directory.

  _On MS Windows, it is located
  on `C:\Users\<user>\AppData\Roaming\cura\<cura_version>\plugins`_

* (Optional) Clone or
  download [monoprice-select-mini-v2-api-mock](https://github.com/loociano/monoprice-select-mini-v2-api-mock)
  to simulate a Monoprice Select Mini V2 printer running locally.

## Author

Luc Rubio

## License

See [LICENSE](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/LICENSE).
