import logging
from typing import Iterable, Optional

def send_email(to: Iterable[str] | str, subject: str, body: str, *, sender: Optional[str]=None) -> bool:
    logging.info("send_email stub: to=%s subject=%s", to, subject)
    return True
