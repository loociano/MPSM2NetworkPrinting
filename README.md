# Cura network plugin for Monoprice Select Mini V2

## Overview

This plugin for [Cura](https://github.com/ultimaker/cura) enables network interoperability with Monoprice Select Mini V2 printers.

This software is unofficial and not affiliated with Monoprice.

## How to install

* **Recommended**: go to Cura → Marketplace. Install plugin **Network support for Monoprice Select Mini V2**.

* Manually: download this repository and move to the Cura plugins directory. On Windows, it is 
`C:\Program Files\Ultimaker Cura 4.6\plugins\`.

## How to use

1. **Important**: due to [a bug](https://github.com/Ultimaker/Cura/issues/7739) in Cura, only one network plugin can be enabled when adding network printers by IP address. Please click on **Marketplace** and disable `UM3 Network Printing` plugin temporarily to add the printer.

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

## Author

Luc Rubio <luc@loociano.com>

## License

See [LICENSE](https://github.com/loociano/MPSM2NetworkPrinting/blob/master/LICENSE).

## Donate

If this plugin was useful to you, please consider making a donation.

[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=AHZG8HGU4GM8G)