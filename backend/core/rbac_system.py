"""
Role-Based Access Control (RBAC) System - Hierarchical Permission Management
Comprehensive RBAC framework for the Türkiye Üniversite Sınavları Hazırlık Platformu

Bu dosya kapsamlı RBAC sistemi sağlar:
- Hierarchical role structure with inheritance
- Dynamic permission management
- Resource-based access control
- Permission caching for performance
- Audit logging for all authorization decisions
- Temporal permissions (time-based access)
- Context-aware authorization
- Permission delegation and inheritance
"""

import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .error_context import async_error_context
from .error_monitoring import log_error

# Import error handling
from .exceptions import ErrorSeverity, NotFoundError, ValidationError

# Import enhanced database patterns


logger = logging.getLogger(__name__)


# Helper function to get value from enum or string
def _get_value(obj) -> str:
    """Get string value from enum or return string as-is"""
    if obj is None:
        return "none"
    if hasattr(obj, 'value'):
        return obj.value
    return str(obj)


# ==================== RBAC ENUMS ====================


class ResourceType(Enum):
    """System resource types"""

    USER = "user"
    EXAM = "exam"
    QUESTION = "question"
    CONTENT = "content"
    REPORT = "report"
    SYSTEM = "system"
    COURSE = "course"
    ANALYTICS = "analytics"
    NOTIFICATION = "notification"
    PAYMENT = "payment"
    FILE = "file"
    CHAT = "chat"


class Action(Enum):
    """System actions/permissions"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"
    REJECT = "reject"
    PUBLISH = "publish"
    ARCHIVE = "archive"
    EXPORT = "export"
    IMPORT = "import"
    SHARE = "share"
    ASSIGN = "assign"
    GRADE = "grade"
    MODERATE = "moderate"


class PermissionEffect(Enum):
    """Permission effect types"""

    ALLOW = "allow"
    DENY = "deny"


class RoleType(Enum):
    """Role categorization"""

    SYSTEM = "system"  # Built-in system roles
    CUSTOM = "custom"  # User-defined roles
    TEMPORARY = "temporary"  # Time-bound roles
    INHERITED = "inherited"  # Roles inherited from groups


class AuditAction(Enum):
    """Authorization audit actions"""

    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    PERMISSION_CHECKED = "permission_checked"
    RESOURCE_ACCESSED = "resource_accessed"


# ==================== RBAC DATA CLASSES ====================


@dataclass
class Permission:
    """Individual permission definition"""

    id: str
    name: str
    description: str
    resource_type: ResourceType
    action: Action
    effect: PermissionEffect = PermissionEffect.ALLOW
    conditions: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        if not self.id:
            self.id = f"{self.resource_type.value}:{self.action.value}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "resource_type": self.resource_type.value,
            "action": self.action.value,
            "effect": self.effect.value,
            "conditions": self.conditions,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Permission":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            resource_type=ResourceType(data["resource_type"]),
            action=Action(data["action"]),
            effect=PermissionEffect(data.get("effect", "allow")),
            conditions=data.get("conditions"),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(UTC),
        )


@dataclass
class Role:
    """Role definition with hierarchical support"""

    id: str
    name: str
    description: str
    role_type: RoleType
    permissions: list[str] = field(default_factory=list)  # Permission IDs
    parent_roles: list[str] = field(default_factory=list)  # Parent role IDs
    child_roles: list[str] = field(default_factory=list)  # Child role IDs
    is_active: bool = True
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_valid(self) -> bool:
        """Check if role is currently valid"""
        if not self.is_active:
            return False

        now = datetime.now(UTC)

        if self.valid_from and now < self.valid_from:
            return False

        if self.valid_until and now > self.valid_until:
            return False

        return True

    def add_permission(self, permission_id: str) -> None:
        """Add permission to role"""
        if permission_id not in self.permissions:
            self.permissions.append(permission_id)
            self.updated_at = datetime.now(UTC)

    def remove_permission(self, permission_id: str) -> None:
        """Remove permission from role"""
        if permission_id in self.permissions:
            self.permissions.remove(permission_id)
            self.updated_at = datetime.now(UTC)

    def add_parent_role(self, parent_role_id: str) -> None:
        """Add parent role (inherit permissions)"""
        if parent_role_id not in self.parent_roles:
            self.parent_roles.append(parent_role_id)
            self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "role_type": self.role_type.value,
            "permissions": self.permissions,
            "parent_roles": self.parent_roles,
            "child_roles": self.child_roles,
            "is_active": self.is_active,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class UserRole:
    """User-role assignment with context"""

    id: str
    user_id: str
    role_id: str
    assigned_by: str
    assigned_at: datetime
    expires_at: datetime | None = None
    context: dict[
        str, Any
    ] | None = None  # Additional context like department, course, etc.
    is_active: bool = True

    def is_valid(self) -> bool:
        """Check if user role assignment is valid"""
        if not self.is_active:
            return False

        if self.expires_at and datetime.now(UTC) > self.expires_at:
            return False

        return True


@dataclass
class AuthorizationContext:
    """Context for authorization decisions"""

    user_id: str
    resource_type: ResourceType | str = "general"  # Can be enum or string
    action: Action | None = None  # Made optional for compatibility
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    additional_context: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    # Additional fields for auth_dependencies.py compatibility
    user_role: str | None = None
    required_permissions: list[str] = field(default_factory=list)
    required_roles: list[str] = field(default_factory=list)
    resource_owner_id: str | None = None
    request_path: str | None = None
    request_method: str | None = None


@dataclass
class AuthorizationResult:
    """Result of authorization check"""

    granted: bool
    reason: str
    matched_permissions: list[str] = field(default_factory=list)
    matched_roles: list[str] = field(default_factory=list)
    context: AuthorizationContext | None = None
    cached: bool = False
    message: str = ""  # Alias for reason (backward compatibility)
    granted_permissions: list[str] = field(default_factory=list)  # Alias for matched_permissions

    def __post_init__(self):
        # Sync aliases
        if not self.message:
            self.message = self.reason
        if not self.granted_permissions:
            self.granted_permissions = self.matched_permissions

    @property
    def authorized(self) -> bool:
        """Alias for granted (backward compatibility with auth_dependencies.py)"""
        return self.granted

    def to_dict(self) -> dict[str, Any]:
        return {
            "granted": self.granted,
            "authorized": self.authorized,
            "reason": self.reason,
            "message": self.message,
            "matched_permissions": self.matched_permissions,
            "matched_roles": self.matched_roles,
            "cached": self.cached,
        }


# ==================== PERMISSION MANAGER ====================


class PermissionManager:
    """Manage individual permissions"""

    def __init__(self):
        self.permissions: dict[str, Permission] = {}
        self._initialize_system_permissions()

    def _initialize_system_permissions(self) -> None:
        """Initialize system-level permissions"""

        # System permissions
        system_permissions = [
            Permission(
                "system:read",
                "Sistem Okuma",
                "Sistem bilgilerini okuyabilir",
                ResourceType.SYSTEM,
                Action.READ,
            ),
            Permission(
                "system:update",
                "Sistem Güncelleme",
                "Sistem ayarlarını güncelleyebilir",
                ResourceType.SYSTEM,
                Action.UPDATE,
            ),
            Permission(
                "system:execute",
                "Sistem Yürütme",
                "Sistem komutlarını çalıştırabilir",
                ResourceType.SYSTEM,
                Action.EXECUTE,
            ),
            # User permissions
            Permission(
                "user:create",
                "Kullanıcı Oluşturma",
                "Yeni kullanıcı oluşturabilir",
                ResourceType.USER,
                Action.CREATE,
            ),
            Permission(
                "user:read",
                "Kullanıcı Okuma",
                "Kullanıcı bilgilerini okuyabilir",
                ResourceType.USER,
                Action.READ,
            ),
            Permission(
                "user:update",
                "Kullanıcı Güncelleme",
                "Kullanıcı bilgilerini güncelleyebilir",
                ResourceType.USER,
                Action.UPDATE,
            ),
            Permission(
                "user:delete",
                "Kullanıcı Silme",
                "Kullanıcıyı silebilir",
                ResourceType.USER,
                Action.DELETE,
            ),
            # Exam permissions
            Permission(
                "exam:create",
                "Sınav Oluşturma",
                "Yeni sınav oluşturabilir",
                ResourceType.EXAM,
                Action.CREATE,
            ),
            Permission(
                "exam:read",
                "Sınav Okuma",
                "Sınav bilgilerini okuyabilir",
                ResourceType.EXAM,
                Action.READ,
            ),
            Permission(
                "exam:update",
                "Sınav Güncelleme",
                "Sınav bilgilerini güncelleyebilir",
                ResourceType.EXAM,
                Action.UPDATE,
            ),
            Permission(
                "exam:delete",
                "Sınav Silme",
                "Sınavı silebilir",
                ResourceType.EXAM,
                Action.DELETE,
            ),
            Permission(
                "exam:grade",
                "Sınav Değerlendirme",
                "Sınavları değerlendirebilir",
                ResourceType.EXAM,
                Action.GRADE,
            ),
            Permission(
                "exam:publish",
                "Sınav Yayınlama",
                "Sınavları yayınlayabilir",
                ResourceType.EXAM,
                Action.PUBLISH,
            ),
            # Question permissions
            Permission(
                "question:create",
                "Soru Oluşturma",
                "Yeni soru oluşturabilir",
                ResourceType.QUESTION,
                Action.CREATE,
            ),
            Permission(
                "question:read",
                "Soru Okuma",
                "Soru bilgilerini okuyabilir",
                ResourceType.QUESTION,
                Action.READ,
            ),
            Permission(
                "question:update",
                "Soru Güncelleme",
                "Soru bilgilerini güncelleyebilir",
                ResourceType.QUESTION,
                Action.UPDATE,
            ),
            Permission(
                "question:delete",
                "Soru Silme",
                "Soruyu silebilir",
                ResourceType.QUESTION,
                Action.DELETE,
            ),
            Permission(
                "question:approve",
                "Soru Onaylama",
                "Soruları onaylayabilir",
                ResourceType.QUESTION,
                Action.APPROVE,
            ),
            # Content permissions
            Permission(
                "content:create",
                "İçerik Oluşturma",
                "Yeni içerik oluşturabilir",
                ResourceType.CONTENT,
                Action.CREATE,
            ),
            Permission(
                "content:read",
                "İçerik Okuma",
                "İçerik bilgilerini okuyabilir",
                ResourceType.CONTENT,
                Action.READ,
            ),
            Permission(
                "content:update",
                "İçerik Güncelleme",
                "İçerik bilgilerini güncelleyebilir",
                ResourceType.CONTENT,
                Action.UPDATE,
            ),
            Permission(
                "content:delete",
                "İçerik Silme",
                "İçeriği silebilir",
                ResourceType.CONTENT,
                Action.DELETE,
            ),
            Permission(
                "content:moderate",
                "İçerik Moderasyon",
                "İçerikleri moderate edebilir",
                ResourceType.CONTENT,
                Action.MODERATE,
            ),
            # Report permissions
            Permission(
                "report:create",
                "Rapor Oluşturma",
                "Yeni rapor oluşturabilir",
                ResourceType.REPORT,
                Action.CREATE,
            ),
            Permission(
                "report:read",
                "Rapor Okuma",
                "Rapor bilgilerini okuyabilir",
                ResourceType.REPORT,
                Action.READ,
            ),
            Permission(
                "report:export",
                "Rapor Dışa Aktarma",
                "Raporları dışa aktarabilir",
                ResourceType.REPORT,
                Action.EXPORT,
            ),
            # Analytics permissions
            Permission(
                "analytics:read",
                "Analitik Okuma",
                "Analitik verilerini okuyabilir",
                ResourceType.ANALYTICS,
                Action.READ,
            ),
            Permission(
                "analytics:export",
                "Analitik Dışa Aktarma",
                "Analitik verilerini dışa aktarabilir",
                ResourceType.ANALYTICS,
                Action.EXPORT,
            ),
        ]

        for permission in system_permissions:
            self.permissions[permission.id] = permission

    def create_permission(self, permission: Permission) -> bool:
        """Create new permission"""
        if permission.id in self.permissions:
            return False

        self.permissions[permission.id] = permission
        logger.info(f"Created permission: {permission.id}")
        return True

    def get_permission(self, permission_id: str) -> Permission | None:
        """Get permission by ID"""
        return self.permissions.get(permission_id)

    def get_permissions_by_resource(
        self, resource_type: ResourceType
    ) -> list[Permission]:
        """Get all permissions for a resource type"""
        return [
            perm
            for perm in self.permissions.values()
            if perm.resource_type == resource_type
        ]

    def get_permissions_by_action(self, action: Action) -> list[Permission]:
        """Get all permissions for an action"""
        return [perm for perm in self.permissions.values() if perm.action == action]

    def update_permission(self, permission: Permission) -> bool:
        """Update existing permission"""
        if permission.id not in self.permissions:
            return False

        self.permissions[permission.id] = permission
        logger.info(f"Updated permission: {permission.id}")
        return True

    def delete_permission(self, permission_id: str) -> bool:
        """Delete permission"""
        if permission_id in self.permissions:
            del self.permissions[permission_id]
            logger.info(f"Deleted permission: {permission_id}")
            return True
        return False

    def get_all_permissions(self) -> list[Permission]:
        """Get all permissions"""
        return list(self.permissions.values())


# ==================== ROLE MANAGER ====================


class RoleManager:
    """Manage roles and role hierarchies"""

    def __init__(self, permission_manager: PermissionManager):
        self.permission_manager = permission_manager
        self.roles: dict[str, Role] = {}
        self.role_hierarchy: dict[str, set[str]] = defaultdict(set)  # child -> parents
        self._initialize_system_roles()

    def _initialize_system_roles(self) -> None:
        """Initialize system-level roles"""

        # Super Admin Role
        super_admin = Role(
            id="super_admin",
            name="Süper Yönetici",
            description="Tüm sistem yetkilerine sahip süper yönetici",
            role_type=RoleType.SYSTEM,
            permissions=[
                perm.id for perm in self.permission_manager.get_all_permissions()
            ],
        )

        # Admin Role
        admin = Role(
            id="admin",
            name="Yönetici",
            description="Sistem yöneticisi",
            role_type=RoleType.SYSTEM,
            permissions=[
                "user:create",
                "user:read",
                "user:update",
                "user:delete",
                "exam:create",
                "exam:read",
                "exam:update",
                "exam:delete",
                "exam:publish",
                "question:create",
                "question:read",
                "question:update",
                "question:delete",
                "question:approve",
                "content:create",
                "content:read",
                "content:update",
                "content:delete",
                "content:moderate",
                "report:create",
                "report:read",
                "report:export",
                "analytics:read",
                "analytics:export",
            ],
        )

        # Teacher Role
        teacher = Role(
            id="teacher",
            name="Öğretmen",
            description="Öğretmen kullanıcısı",
            role_type=RoleType.SYSTEM,
            permissions=[
                "user:read",
                "exam:create",
                "exam:read",
                "exam:update",
                "exam:grade",
                "question:create",
                "question:read",
                "question:update",
                "content:create",
                "content:read",
                "content:update",
                "report:read",
            ],
        )

        # Student Role
        student = Role(
            id="student",
            name="Öğrenci",
            description="Öğrenci kullanıcısı",
            role_type=RoleType.SYSTEM,
            permissions=["exam:read", "question:read", "content:read"],
        )

        # Parent Role
        parent = Role(
            id="parent",
            name="Veli",
            description="Veli kullanıcısı",
            role_type=RoleType.SYSTEM,
            permissions=["report:read"],
        )

        # Guest Role
        guest = Role(
            id="guest",
            name="Misafir",
            description="Misafir kullanıcısı",
            role_type=RoleType.SYSTEM,
            permissions=["content:read"],
        )

        # Store roles
        for role in [super_admin, admin, teacher, student, parent, guest]:
            self.roles[role.id] = role

        # Set up hierarchy (child -> parent relationships)
        self._add_role_hierarchy("admin", "super_admin")
        self._add_role_hierarchy("teacher", "admin")
        self._add_role_hierarchy("student", "teacher")
        self._add_role_hierarchy("parent", "student")
        self._add_role_hierarchy("guest", "parent")

    def create_role(self, role: Role) -> bool:
        """Create new role"""
        if role.id in self.roles:
            return False

        # Validate permissions exist
        for perm_id in role.permissions:
            if not self.permission_manager.get_permission(perm_id):
                raise ValidationError(f"Permission {perm_id} does not exist")

        self.roles[role.id] = role
        logger.info(f"Created role: {role.id}")
        return True

    def get_role(self, role_id: str) -> Role | None:
        """Get role by ID"""
        return self.roles.get(role_id)

    def get_roles_by_type(self, role_type: RoleType) -> list[Role]:
        """Get roles by type"""
        return [role for role in self.roles.values() if role.role_type == role_type]

    def update_role(self, role: Role) -> bool:
        """Update existing role"""
        if role.id not in self.roles:
            return False

        role.updated_at = datetime.now(UTC)
        self.roles[role.id] = role
        logger.info(f"Updated role: {role.id}")
        return True

    def delete_role(self, role_id: str) -> bool:
        """Delete role"""
        if role_id in self.roles and self.roles[role_id].role_type != RoleType.SYSTEM:
            del self.roles[role_id]
            # Clean up hierarchy
            self._remove_from_hierarchy(role_id)
            logger.info(f"Deleted role: {role_id}")
            return True
        return False

    def _add_role_hierarchy(self, child_role_id: str, parent_role_id: str) -> None:
        """Add parent-child relationship"""
        self.role_hierarchy[child_role_id].add(parent_role_id)

        # Update role objects
        if (
            child_role_id in self.roles
            and parent_role_id not in self.roles[child_role_id].parent_roles
        ):
            self.roles[child_role_id].parent_roles.append(parent_role_id)

        if (
            parent_role_id in self.roles
            and child_role_id not in self.roles[parent_role_id].child_roles
        ):
            self.roles[parent_role_id].child_roles.append(child_role_id)

    def _remove_from_hierarchy(self, role_id: str) -> None:
        """Remove role from hierarchy"""
        # Remove as child
        if role_id in self.role_hierarchy:
            del self.role_hierarchy[role_id]

        # Remove as parent
        for child_id, parents in self.role_hierarchy.items():
            parents.discard(role_id)

    def get_inherited_permissions(self, role_id: str) -> set[str]:
        """Get all permissions including inherited ones"""
        visited = set()
        all_permissions = set()

        def collect_permissions(current_role_id: str):
            if current_role_id in visited or current_role_id not in self.roles:
                return

            visited.add(current_role_id)
            role = self.roles[current_role_id]

            # Add direct permissions
            all_permissions.update(role.permissions)

            # Add inherited permissions
            for parent_id in self.role_hierarchy.get(current_role_id, set()):
                collect_permissions(parent_id)

        collect_permissions(role_id)
        return all_permissions

    def get_role_hierarchy_path(self, role_id: str) -> list[str]:
        """Get hierarchy path from role to root"""
        path = [role_id]
        current = role_id

        while self.role_hierarchy.get(current):
            parent = next(iter(self.role_hierarchy[current]))  # Get first parent
            if parent in path:  # Prevent cycles
                break
            path.append(parent)
            current = parent

        return path

    def get_all_roles(self) -> list[Role]:
        """Get all roles"""
        return list(self.roles.values())


# ==================== RBAC MANAGER ====================


class RBACManager:
    """Main RBAC manager combining permissions, roles, and user assignments"""

    def __init__(self):
        self.permission_manager = PermissionManager()
        self.role_manager = RoleManager(self.permission_manager)

        # User role assignments (in production, this would be in database)
        self.user_roles: dict[str, list[UserRole]] = defaultdict(list)

        # Permission cache for performance
        self.permission_cache: dict[str, dict[str, Any]] = {}
        self.cache_ttl = 300  # 5 minutes

        # Audit log
        self.audit_log: list[dict[str, Any]] = []

    async def assign_role_to_user(
        self,
        user_id: str,
        role_id: str,
        assigned_by: str,
        expires_at: datetime | None = None,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Assign role to user"""

        async with async_error_context(
            operation_name="assign_role_to_user",
            entity_id=user_id,
            business_operation="role_assignment",
        ) as ctx:
            try:
                # Validate role exists
                role = self.role_manager.get_role(role_id)
                if not role:
                    raise NotFoundError(f"Role {role_id} not found")

                if not role.is_valid():
                    raise ValidationError(f"Role {role_id} is not valid")

                # Check if user already has this role
                existing_assignment = next(
                    (
                        ur
                        for ur in self.user_roles[user_id]
                        if ur.role_id == role_id and ur.is_valid()
                    ),
                    None,
                )

                if existing_assignment:
                    ctx.add_annotation("User already has this role")
                    return False

                # Create user role assignment
                user_role = UserRole(
                    id=f"{user_id}:{role_id}:{datetime.now().timestamp()}",
                    user_id=user_id,
                    role_id=role_id,
                    assigned_by=assigned_by,
                    assigned_at=datetime.now(UTC),
                    expires_at=expires_at,
                    context=context,
                )

                self.user_roles[user_id].append(user_role)

                # Clear permission cache for user
                self._clear_user_cache(user_id)

                # Audit log
                await self._log_audit_event(
                    AuditAction.ROLE_ASSIGNED,
                    user_id,
                    {
                        "role_id": role_id,
                        "assigned_by": assigned_by,
                        "expires_at": expires_at,
                    },
                )

                ctx.add_annotation(f"Role {role_id} assigned to user {user_id}")
                logger.info(f"Assigned role {role_id} to user {user_id}")

                return True

            except Exception as e:
                ctx.add_annotation(f"Role assignment failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                raise

    async def revoke_role_from_user(
        self, user_id: str, role_id: str, revoked_by: str
    ) -> bool:
        """Revoke role from user"""

        async with async_error_context(
            operation_name="revoke_role_from_user",
            entity_id=user_id,
            business_operation="role_revocation",
        ) as ctx:
            try:
                user_role_assignments = self.user_roles.get(user_id, [])

                # Find and deactivate the role assignment
                revoked = False
                for user_role in user_role_assignments:
                    if user_role.role_id == role_id and user_role.is_valid():
                        user_role.is_active = False
                        revoked = True
                        break

                if revoked:
                    # Clear permission cache for user
                    self._clear_user_cache(user_id)

                    # Audit log
                    await self._log_audit_event(
                        AuditAction.ROLE_REVOKED,
                        user_id,
                        {"role_id": role_id, "revoked_by": revoked_by},
                    )

                    ctx.add_annotation(f"Role {role_id} revoked from user {user_id}")
                    logger.info(f"Revoked role {role_id} from user {user_id}")

                return revoked

            except Exception as e:
                ctx.add_annotation(f"Role revocation failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                raise

    async def check_permission(
        self, auth_context: AuthorizationContext
    ) -> AuthorizationResult:
        """Check if user has permission for specific action on resource"""

        async with async_error_context(
            operation_name="check_permission",
            entity_id=auth_context.user_id,
            business_operation="authorization_check",
        ) as ctx:
            ctx.tags.update(
                {
                    "user_id": auth_context.user_id,
                    "resource_type": _get_value(auth_context.resource_type),
                    "action": _get_value(auth_context.action),
                    "resource_id": auth_context.resource_id or "any",
                }
            )

            try:
                # Check cache first
                cache_key = self._get_cache_key(auth_context)
                cached_result = self._get_cached_permission(cache_key)

                if cached_result:
                    ctx.add_annotation("Permission check served from cache")
                    cached_result.cached = True
                    return cached_result

                # Get user roles
                user_roles = self.get_active_user_roles(auth_context.user_id)

                if not user_roles:
                    result = AuthorizationResult(
                        granted=False,
                        reason="User has no active roles",
                        context=auth_context,
                    )
                    ctx.add_annotation("Permission denied: no active roles")
                    await self._log_audit_event(
                        AuditAction.PERMISSION_DENIED,
                        auth_context.user_id,
                        {
                            "reason": "no_active_roles",
                            "resource": _get_value(auth_context.resource_type),
                        },
                    )
                    return result

                # Check permissions for each role
                granted_permissions = []
                matched_roles = []

                required_permission_id = (
                    f"{_get_value(auth_context.resource_type)}:{_get_value(auth_context.action)}"
                )

                for user_role in user_roles:
                    role = self.role_manager.get_role(user_role.role_id)
                    if not role or not role.is_valid():
                        continue

                    # Get all permissions including inherited
                    all_permissions = self.role_manager.get_inherited_permissions(
                        role.id
                    )

                    if required_permission_id in all_permissions:
                        granted_permissions.append(required_permission_id)
                        matched_roles.append(role.id)

                # Determine final result
                if granted_permissions:
                    result = AuthorizationResult(
                        granted=True,
                        reason=f"Permission granted via roles: {', '.join(matched_roles)}",
                        matched_permissions=granted_permissions,
                        matched_roles=matched_roles,
                        context=auth_context,
                    )
                    ctx.add_annotation("Permission granted")
                    await self._log_audit_event(
                        AuditAction.PERMISSION_GRANTED,
                        auth_context.user_id,
                        {"permissions": granted_permissions, "roles": matched_roles},
                    )
                else:
                    result = AuthorizationResult(
                        granted=False,
                        reason=f"User does not have required permission: {required_permission_id}",
                        matched_roles=[ur.role_id for ur in user_roles],
                        context=auth_context,
                    )
                    ctx.add_annotation("Permission denied")
                    await self._log_audit_event(
                        AuditAction.PERMISSION_DENIED,
                        auth_context.user_id,
                        {"required_permission": required_permission_id},
                    )

                # Cache result
                self._cache_permission_result(cache_key, result)

                return result

            except Exception as e:
                ctx.add_annotation(f"Permission check failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                return AuthorizationResult(
                    granted=False,
                    reason=f"Permission check error: {e!s}",
                    context=auth_context,
                )

    def get_active_user_roles(self, user_id: str) -> list[UserRole]:
        """Get all active roles for a user"""
        return [
            user_role
            for user_role in self.user_roles.get(user_id, [])
            if user_role.is_valid()
        ]

    def get_user_permissions(self, user_id: str) -> set[str]:
        """Get all permissions for a user"""
        all_permissions = set()

        for user_role in self.get_active_user_roles(user_id):
            role_permissions = self.role_manager.get_inherited_permissions(
                user_role.role_id
            )
            all_permissions.update(role_permissions)

        return all_permissions

    def _get_cache_key(self, auth_context: AuthorizationContext) -> str:
        """Generate cache key for authorization context"""
        key_data = f"{auth_context.user_id}:{_get_value(auth_context.resource_type)}:{_get_value(auth_context.action)}:{auth_context.resource_id or 'any'}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached_permission(self, cache_key: str) -> AuthorizationResult | None:
        """Get cached permission result"""
        cached_data = self.permission_cache.get(cache_key)

        if cached_data:
            cache_time = cached_data.get("timestamp", 0)
            if datetime.now().timestamp() - cache_time < self.cache_ttl:
                return AuthorizationResult(**cached_data["result"])

        return None

    def _cache_permission_result(
        self, cache_key: str, result: AuthorizationResult
    ) -> None:
        """Cache permission result"""
        self.permission_cache[cache_key] = {
            "result": {
                "granted": result.granted,
                "reason": result.reason,
                "matched_permissions": result.matched_permissions,
                "matched_roles": result.matched_roles,
            },
            "timestamp": datetime.now().timestamp(),
        }

    def _clear_user_cache(self, user_id: str) -> None:
        """Clear cached permissions for a user"""
        keys_to_remove = [
            key
            for key in self.permission_cache.keys()
            if key.startswith(hashlib.md5(user_id.encode()).hexdigest()[:8])
        ]

        for key in keys_to_remove:
            del self.permission_cache[key]

    async def _log_audit_event(
        self, action: AuditAction, user_id: str, details: dict[str, Any]
    ) -> None:
        """Log audit event"""
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action.value,
            "user_id": user_id,
            "details": details,
        }

        self.audit_log.append(event)

        # Keep only last 10000 audit entries
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]

    def get_rbac_stats(self) -> dict[str, Any]:
        """Get RBAC system statistics"""
        return {
            "permissions_count": len(self.permission_manager.permissions),
            "roles_count": len(self.role_manager.roles),
            "user_assignments_count": sum(
                len(roles) for roles in self.user_roles.values()
            ),
            "active_assignments_count": sum(
                len([ur for ur in roles if ur.is_valid()])
                for roles in self.user_roles.values()
            ),
            "cache_size": len(self.permission_cache),
            "audit_events_count": len(self.audit_log),
            "roles_by_type": {
                role_type.value: len(self.role_manager.get_roles_by_type(role_type))
                for role_type in RoleType
            },
        }


# ==================== GLOBAL RBAC MANAGER ====================

# Global RBAC manager instance
rbac_manager: RBACManager | None = None


def get_rbac_manager() -> RBACManager:
    """Get global RBAC manager instance"""
    global rbac_manager

    if rbac_manager is None:
        rbac_manager = RBACManager()

    return rbac_manager


# ==================== UTILITY FUNCTIONS ====================


async def check_user_permission(
    user_id: str,
    resource_type: ResourceType,
    action: Action,
    resource_id: str | None = None,
    additional_context: dict[str, Any] | None = None,
) -> bool:
    """Convenience function to check user permission"""

    auth_context = AuthorizationContext(
        user_id=user_id,
        resource_type=resource_type,
        action=action,
        resource_id=resource_id,
        additional_context=additional_context or {},
    )

    rbac = get_rbac_manager()
    result = await rbac.check_permission(auth_context)

    return result.granted


async def assign_role(user_id: str, role_id: str, assigned_by: str) -> bool:
    """Convenience function to assign role"""

    rbac = get_rbac_manager()
    return await rbac.assign_role_to_user(user_id, role_id, assigned_by)


async def revoke_role(user_id: str, role_id: str, revoked_by: str) -> bool:
    """Convenience function to revoke role"""

    rbac = get_rbac_manager()
    return await rbac.revoke_role_from_user(user_id, role_id, revoked_by)


def get_user_roles(user_id: str) -> list[str]:
    """Get list of user's active role IDs"""

    rbac = get_rbac_manager()
    user_roles = rbac.get_active_user_roles(user_id)

    return [ur.role_id for ur in user_roles]


def get_user_permissions(user_id: str) -> list[str]:
    """Get list of user's permissions"""

    rbac = get_rbac_manager()
    permissions = rbac.get_user_permissions(user_id)

    return list(permissions)


# ==================== INITIALIZATION ====================


def initialize_rbac_system() -> RBACManager:
    """Initialize RBAC system with default data"""

    rbac = get_rbac_manager()

    logger.info("RBAC system initialized with:")
    logger.info(f"- {len(rbac.permission_manager.permissions)} permissions")
    logger.info(f"- {len(rbac.role_manager.roles)} roles")

    return rbac
