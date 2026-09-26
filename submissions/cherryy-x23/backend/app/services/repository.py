import abc
import threading
from copy import deepcopy
from typing import Any, Dict, List, Optional


class InspectionRepository(abc.ABC):
    """
    Abstract repository interface for inspection record persistence.
    Allows transparent substitution of InMemory repository with PostgreSQL/MongoDB in future phases.
    """

    @abc.abstractmethod
    def create(self, inspection: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abc.abstractmethod
    def get(self, inspection_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    def list(
        self,
        org_id: str,
        status: Optional[str] = None,
        verdict: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    def update(self, inspection_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    def clear(self) -> None:
        pass


class InMemoryInspectionRepository(InspectionRepository):
    """
    Thread-safe in-memory repository for Phase 4 development and testing.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._storage: Dict[str, Dict[str, Any]] = {}

    def create(self, inspection: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            iid = inspection["inspection_id"]
            self._storage[iid] = deepcopy(inspection)
            return deepcopy(self._storage[iid])

    def get(self, inspection_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            record = self._storage.get(inspection_id)
            return deepcopy(record) if record else None

    def list(
        self,
        org_id: str,
        status: Optional[str] = None,
        verdict: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            results = []
            # Tenancy isolation: strictly filter by org_id first
            for item in self._storage.values():
                if item.get("org_id") != org_id:
                    continue
                if status and item.get("status") != status:
                    continue
                if verdict and item.get("verdict") != verdict:
                    continue
                results.append(deepcopy(item))
                if len(results) >= limit:
                    break
            # Sort by created_at descending
            results.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
            return results

    def update(self, inspection_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            if inspection_id not in self._storage:
                return None
            record = self._storage[inspection_id]
            record.update(deepcopy(updates))
            return deepcopy(record)

    def clear(self) -> None:
        with self._lock:
            self._storage.clear()


# Default singleton instance for application runtime
_default_repo = InMemoryInspectionRepository()


def get_repository() -> InspectionRepository:
    return _default_repo
