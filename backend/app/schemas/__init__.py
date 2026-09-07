"""Pydantic-схемы (сериализаторы) для API.

Единая точка импорта всех схем модулей.
"""

from app.schemas.auth import (  # noqa: F401
    ChangePasswordRequest,
    DelegationCreate,
    DelegationOut,
    LoginRequest,
    PermissionOut,
    RefreshRequest,
    RoleCreate,
    RoleOut,
    RoleUpdate,
    RoleWithPermissions,
    TokenPair,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.schemas.structure import (  # noqa: F401
    AssetAttributeCreate,
    AssetAttributeOut,
    AssetStatusCreate,
    AssetStatusOut,
    AssetTypeCreate,
    AssetTypeOut,
    BuildingCreate,
    BuildingOut,
    BuildingUpdate,
    MaterialCreate,
    MaterialOut,
    RoomCreate,
    RoomOut,
    RoomUpdate,
    UnitCreate,
    UnitOut,
)
from app.schemas.asset import (  # noqa: F401
    AssetCreate,
    AssetListOut,
    AssetOut,
    AssetSearchParams,
    AssetUpdate,
    ReserveNumberOut,
    ReserveNumberRequest,
)
from app.schemas.operation import (  # noqa: F401
    AssetMoveCreate,
    AssetMoveOut,
    IssuanceCreate,
    IssuanceOut,
    IssuanceReturnRequest,
    RepairCreate,
    RepairOut,
    RepairUpdate,
    StatusChangeRequest,
    WriteOffCreate,
    WriteOffOut,
    WriteOffUpdate,
)
from app.schemas.inventory import (  # noqa: F401
    DiscrepancyOut,
    DiscrepancyUpdate,
    InventoryApproveRequest,
    InventoryCreate,
    InventoryItemOut,
    InventoryItemUpdate,
    InventoryOut,
    InventoryUpdate,
)
from app.schemas.document import (  # noqa: F401
    DocumentCreate,
    DocumentOut,
    DocumentSignRequest,
    DocumentUpdate,
)
from app.schemas.audit import AuditLogOut  # noqa: F401
from app.schemas.report import (  # noqa: F401
    ReportCreate,
    ReportJobOut,
)