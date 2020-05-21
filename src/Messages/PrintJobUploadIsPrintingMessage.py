"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from UM import i18nCatalog
from UM.Message import Message

I18N_CATALOG = i18nCatalog('cura')


class PrintJobUploadIsPrintingMessage(Message):
  """Message displayed when the user attempts to upload print when another
  upload is in progress."""

  def __init__(self) -> None:
    super().__init__(
        title=I18N_CATALOG.i18nc('@info:title', 'Printer is busy'),
        text=I18N_CATALOG.i18nc('@info:status',
                                'Cannot upload when the printer is printing.'),
        lifetime=0)
