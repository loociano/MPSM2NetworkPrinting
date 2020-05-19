# Copyright 2020 Luc Rubio <luc@loociano.com>
# Plugin is licensed under the GNU Lesser General Public License v3.0.
from UM import i18nCatalog
from UM.Message import Message

I18N_CATALOG = i18nCatalog('cura')


class PrintJobUploadCancelMessage(Message):
    def __init__(self) -> None:
        super().__init__(
            title=I18N_CATALOG.i18nc('@info:title', 'Print Cancelled'),
            text=I18N_CATALOG.i18nc('@info:status', 'Print job was cancelled.'),
            lifetime=0)
