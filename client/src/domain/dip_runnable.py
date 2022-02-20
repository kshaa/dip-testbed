from typing import Optional
from src.domain.dip_client_error import DIPClientError


class DIPRunnable:
    async def run(self) -> Optional[DIPClientError]:
        pass
