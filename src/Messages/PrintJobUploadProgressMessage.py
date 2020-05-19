# Copyright 2020 Luc Rubio <luc@loociano.com>
# Plugin is licensed under the GNU Lesser General Public License v3.0.
from typing import Callable
from UM import i18nCatalog
from UM.Message import Message

I18N_CATALOG = i18nCatalog('cura')


class PrintJobUploadProgressMessage(Message):
    def __init__(self, on_cancelled: Callable) -> None:
        super().__init__(
            title=I18N_CATALOG.i18nc('@info:status', 'Sending Print Job'),
            text=I18N_CATALOG.i18nc('@info:status', 'Uploading print job to printer.'),
            progress=-1,
            lifetime=0,
            dismissable=False,
            use_inactivity_timer=False)
        self._on_cancelled = on_cancelled
        self.addAction('cancel', I18N_CATALOG.i18nc('@action:button', 'Cancel'), 'cancel',
                       I18N_CATALOG.i18nc('@action', 'Cancels job upload.'))
        self.actionTriggered.connect(self._onActionTriggered)

    def show(self) -> None:
        self.setProgress(0)
        super().show()

    def update(self, percentage: int) -> None:
        if not self._visible:
            super().show()
        self.setProgress(percentage)

    def _onActionTriggered(self, message: str, action: str) -> None:
        if action == 'cancel':
            self._on_cancelled()
