# Cura network plugin for Monoprice Select Mini V2

![](https://travis-ci.org/loociano/MPSM2NetworkPrinting.svg?branch=master)

This [**plugin**](https://marketplace.ultimaker.com/app/cura/plugins/loociano/MPSM2NetworkPrinting) for 
[Cura](https://github.com/ultimaker/cura) enables network interoperability with Monoprice Select Mini V2 printers.

Plugin is compatible with Monoprice Select Mini V1 and Delta printers, with limited support ⁠—I do not own these.

_This software is unofficial and not affiliated with Monoprice. Use at your own risk._

## Requirements

1. Setup Wi-Fi on the printer, by [following one of these methods](https://www.mpselectmini.com/wifi/start). 

   Once completed, the printer's IP address should appear on the LCD screen. Example: `192.168.0.136`.

1. Install [Cura 4.4.0](https://ultimaker.com/software/ultimaker-cura) or later.

## How to install

* **Recommended**: open Cura → Marketplace → Install **Monoprice Select Mini V2**. Restart Cura.

  ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/marketplace.png?raw=true)

  ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-marketplace.png?raw=true)

* Manually: download the latest [plugin release](https://github.com/loociano/MPSM2NetworkPrinting/releases) and drag and
drop the `.curapackage` file into Cura. Restart Cura.

## How to use

1. **Update to Cura 4.7 or later**. In earlier versions, you need to
temporarily disable the **UM3 Network Printing** plugin to add the printer over the network. Go to Marketplace → 
Installed and disable **UM3 Network Printing** plugin. Restart Cura to apply changes.

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/um3-network-printing-disabled.png?raw=true)

1. In Cura, go to Settings → Printer →  **Add Printer**.

1. Click **Add printer by IP**.

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-add-a-printer.png?raw=true)

1. Type network address and click **Add**.

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-add-printer-by-ip-address.png?raw=true)

1. If connection is successful, the printer details are displayed. Click **Connect**.

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-add-printer-by-ip-address-connect.png?raw=true)

1. Click **Next** to select default Machine Settings.

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-machine-settings.png?raw=true)

1. The printer is added. You may check the status of the printer in the **Monitor** tab.

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-monitor-tab.png?raw=true)

1. To start a print, slice a model and click **Print over network**.

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-prepare-model.png?raw=true)

   ![](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/png/cura-sending-print-job.png?raw=true)

## Development

* Clone or download this [repository](https://github.com/loociano/MPSM2NetworkPrinting) into Cura's user plugins 
directory.

   _On MS Windows, it is located on `C:\Users\<user>\AppData\Roaming\cura\<cura_version>\plugins`_

* (Optional) Clone or download [monoprice-select-mini-v2-api-mock](https://github.com/loociano/monoprice-select-mini-v2-api-mock) 
to simulate a Monoprice Select Mini V2 printer running locally.

## Author

Luc Rubio <luc@loociano.com>

## License

See [LICENSE](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/LICENSE).

## Donate

If this plugin was useful to you, please consider making a donation.

[![paypal](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/resources/svg/paypal.svg?raw=true)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=AHZG8HGU4GM8G)
