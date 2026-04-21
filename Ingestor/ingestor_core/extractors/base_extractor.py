from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..models import IngestionOptions

ExtractedData = Tuple[
    str,
    Any,
    Optional[Dict[str, str]],
    Optional[List[Dict[str, Any]]],
    Dict[str, Any],
]


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, path: Path, options: IngestionOptions) -> ExtractedData:
        raise NotImplementedError
