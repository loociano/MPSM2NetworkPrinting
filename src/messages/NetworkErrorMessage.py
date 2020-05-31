"""
Copyright 2020 Luc Rubio <luc@loociano.com>
Plugin is licensed under the GNU Lesser General Public License v3.0.
"""
from UM import i18nCatalog
from UM.Message import Message

I18N_CATALOG = i18nCatalog('cura')


class NetworkErrorMessage(Message):
  """Message displayed when there was an network error."""

  def __init__(self) -> None:
    super().__init__(
        title=I18N_CATALOG.i18nc('@info:title', 'Network error'),
        text=I18N_CATALOG.i18nc(
            '@info:text',
            'There was a problem communicating with the printer.'),
        lifetime=10)
