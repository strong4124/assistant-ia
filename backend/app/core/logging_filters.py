import logging
import re

# Emails : format standard.
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

# Telephones : au moins 8 chiffres consecutifs (espaces/points/tirets
# tolerees entre les groupes), avec ou sans indicatif +XXX. Volontairement
# strict sur "que des chiffres" pour ne pas mordre sur les UUID (qui
# contiennent des lettres hexadecimales) ni sur les codes USSD courts
# type *144#.
_PHONE_RE = re.compile(r"(?<![*#\w])(?:\+?\d[\s.-]?){8,13}\d(?![*#\w])")

_EMAIL_MASK = "[EMAIL_MASQUE]"
_PHONE_MASK = "[TEL_MASQUE]"


def _redact(value: str) -> str:
    value = _EMAIL_RE.sub(_EMAIL_MASK, value)
    value = _PHONE_RE.sub(_PHONE_MASK, value)
    return value


class PIIRedactionFilter(logging.Filter):
    """Masque emails et numeros de telephone dans tous les logs qui passent
    par ce filtre - applique une seule fois au logger racine plutot que
    d'y penser a chaque appel logging.info(...) dans le code metier."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _redact(record.msg)
        if record.args:
            record.args = tuple(
                _redact(arg) if isinstance(arg, str) else arg for arg in record.args
            )
        return True
