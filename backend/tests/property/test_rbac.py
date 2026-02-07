"""
Property-Based Tests - RBAC Role Inheritance

Bu modul, hypothesis kullanarak Role-Based Access Control (RBAC)
rol mirasi icin property-based testler icerir.

Property 4: Child roles inherit parent permissions
- Alt roller ust rol izinlerini miras almali
- Rol hiyerarsisi gecisli olmali
- Dogrudan izinler miras alinan izinlerle birlestirilmeli

Requirements:
- REQ-4.1: Hierarchical role inheritance
- REQ-4.2: Permission transitivity
- REQ-4.3: Direct + inherited permission merging
- REQ-4.4: Role validity time constraints
"""

from datetime import datetime, timedelta
from datetime import UTC
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

import pytest
from hypothesis import assume, given, settings, strategies as st

import sys
sys.path.insert(0, "c:/Users/husey/kiro2/backend")


# RBAC test icin minimal implementation
class ResourceType(str, Enum):
    """Kaynak tipleri."""
    USER = "user"
    EXAM = "exam"
    QUESTION = "question"
    CONTENT = "content"
    REPORT = "report"
    SYSTEM = "system"


class Action(str, Enum):
    """Eylem tipleri."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"


@dataclass
class Permission:
    """Izin tanimi."""
    id: str
    resource_type: str
    action: str

    @classmethod
    def from_string(cls, perm_str: str) -> "Permission":
        """'resource:action' formatindan Permission olusturur."""
        parts = perm_str.split(":")
        return cls(
            id=perm_str,
            resource_type=parts[0],
            action=parts[1] if len(parts) > 1 else "read"
        )


@dataclass
class Role:
    """Rol tanimi."""
    id: str
    name: str
    permissions: set[str] = field(default_factory=set)
    parent_roles: list[str] = field(default_factory=list)
    is_active: bool = True
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    def is_valid(self, check_time: datetime | None = None) -> bool:
        """Rol gecerliligi kontrolu."""
        if not self.is_active:
            return False

        now = check_time or datetime.now(UTC)

        if self.valid_from and now < self.valid_from:
            return False

        if self.valid_until and now > self.valid_until:
            return False

        return True


class RBACSystem:
    """
    RBAC sistemi.

    Rol hiyerarsisi ve izin mirasi yonetir.
    Production RBACManager'i simule eder.
    """

    def __init__(self):
        self.roles: dict[str, Role] = {}
        self.user_roles: dict[str, list[str]] = defaultdict(list)

    def create_role(
        self,
        role_id: str,
        name: str,
        permissions: set[str] | None = None,
        parent_roles: list[str] | None = None
    ) -> Role:
        """Yeni rol olusturur."""
        role = Role(
            id=role_id,
            name=name,
            permissions=permissions or set(),
            parent_roles=parent_roles or []
        )
        self.roles[role_id] = role
        return role

    def add_permission_to_role(self, role_id: str, permission: str) -> bool:
        """Role izin ekler."""
        if role_id not in self.roles:
            return False
        self.roles[role_id].permissions.add(permission)
        return True

    def add_parent_role(self, child_role_id: str, parent_role_id: str) -> bool:
        """Alt role ust rol ekler (inheritance)."""
        if child_role_id not in self.roles or parent_role_id not in self.roles:
            return False

        if parent_role_id not in self.roles[child_role_id].parent_roles:
            self.roles[child_role_id].parent_roles.append(parent_role_id)

        return True

    def get_direct_permissions(self, role_id: str) -> set[str]:
        """Rolun dogrudan izinlerini dondurur (miras haric)."""
        if role_id not in self.roles:
            return set()
        return self.roles[role_id].permissions.copy()

    def get_inherited_permissions(self, role_id: str, visited: set[str] | None = None) -> set[str]:
        """Rolun miras alinan izinlerini dondurur (recursive)."""
        if role_id not in self.roles:
            return set()

        if visited is None:
            visited = set()

        # Cycle detection
        if role_id in visited:
            return set()

        visited.add(role_id)
        role = self.roles[role_id]

        # Dogrudan izinler
        all_permissions = role.permissions.copy()

        # Ust rollerden miras alinan izinler
        for parent_id in role.parent_roles:
            parent_permissions = self.get_inherited_permissions(parent_id, visited.copy())
            all_permissions.update(parent_permissions)

        return all_permissions

    def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """Kullaniciya rol atar."""
        if role_id not in self.roles:
            return False
        if role_id not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role_id)
        return True

    def get_user_permissions(self, user_id: str) -> set[str]:
        """Kullanicinin tum izinlerini dondurur."""
        all_permissions = set()
        for role_id in self.user_roles.get(user_id, []):
            role = self.roles.get(role_id)
            if role and role.is_valid():
                all_permissions.update(self.get_inherited_permissions(role_id))
        return all_permissions

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Kullanicinin belirli bir izni olup olmadigini kontrol eder."""
        return permission in self.get_user_permissions(user_id)

    def get_role_hierarchy_depth(self, role_id: str, visited: set[str] | None = None) -> int:
        """Rol hiyerarsisi derinligini dondurur."""
        if role_id not in self.roles:
            return 0

        if visited is None:
            visited = set()

        if role_id in visited:
            return 0  # Cycle

        visited.add(role_id)
        role = self.roles[role_id]

        if not role.parent_roles:
            return 1

        max_parent_depth = max(
            self.get_role_hierarchy_depth(p, visited.copy())
            for p in role.parent_roles
        )

        return 1 + max_parent_depth


class TestRoleInheritanceProperties:
    """Rol mirasi property-based testleri."""

    def setup_method(self):
        """Her test oncesi RBAC sistemi olustur."""
        self.rbac = RBACSystem()

        # Temel roller ve izinler olustur
        self.rbac.create_role(
            "super_admin",
            "Super Admin",
            permissions={"system:execute", "user:delete", "content:delete"}
        )
        self.rbac.create_role(
            "admin",
            "Admin",
            permissions={"user:create", "user:update", "content:create"},
            parent_roles=["super_admin"]
        )
        self.rbac.create_role(
            "teacher",
            "Teacher",
            permissions={"exam:create", "exam:read", "question:create"},
            parent_roles=["admin"]
        )
        self.rbac.create_role(
            "student",
            "Student",
            permissions={"exam:read", "content:read"},
            parent_roles=["teacher"]
        )

    @given(
        role_index=st.integers(min_value=0, max_value=3)
    )
    @settings(max_examples=100)
    def test_child_inherits_parent_permissions(self, role_index: int):
        """
        Property 4.1: Alt roller ust rol izinlerini miras almali.

        REQ-4.1: Hierarchical role inheritance
        """
        roles = ["student", "teacher", "admin", "super_admin"]
        role_id = roles[role_index]

        inherited = self.rbac.get_inherited_permissions(role_id)
        direct = self.rbac.get_direct_permissions(role_id)

        # Dogrudan izinler miras icinde olmali
        assert direct.issubset(inherited), \
            f"Direct permissions should be subset of inherited for {role_id}"

    @given(
        user_id=st.text(min_size=5, max_size=20)
    )
    @settings(max_examples=100)
    def test_student_inherits_all_ancestor_permissions(self, user_id: str):
        """
        Property 4.2: Student tum ust rollerin izinlerini miras almali.

        Student -> Teacher -> Admin -> Super Admin zinciri.
        """
        self.rbac.assign_role_to_user(user_id, "student")

        user_permissions = self.rbac.get_user_permissions(user_id)

        # Student'in kendi izni
        assert "exam:read" in user_permissions
        assert "content:read" in user_permissions

        # Teacher'dan miras
        assert "exam:create" in user_permissions
        assert "question:create" in user_permissions

        # Admin'den miras
        assert "user:create" in user_permissions
        assert "content:create" in user_permissions

        # Super Admin'den miras
        assert "system:execute" in user_permissions

    @given(
        permission=st.sampled_from([
            "exam:read", "exam:create", "user:create",
            "system:execute", "content:read"
        ])
    )
    @settings(max_examples=100)
    def test_permission_transitivity(self, permission: str):
        """
        Property 4.3: Izin mirasi gecisli olmali.

        A -> B -> C hiyerarsisinde, C'nin A'nin izinlerini olmali.
        """
        # Student en alt rol, tum izinleri miras almali
        student_perms = self.rbac.get_inherited_permissions("student")

        # Bu izin varsa, super_admin'de de olmali
        super_admin_perms = self.rbac.get_inherited_permissions("super_admin")

        # Super admin'in izni student'ta da olmali (gecislilik)
        for perm in super_admin_perms:
            assert perm in student_perms, \
                f"Super admin permission {perm} should be inherited by student"

    @given(
        role_count=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=100)
    def test_deep_hierarchy_inheritance(self, role_count: int):
        """
        Property 4.4: Derin hiyerarsi zincirinde miras dogru calismal.

        N seviyeli hiyerarside en alt rol tum izinleri almali.
        """
        # Yeni RBAC sistemi
        rbac = RBACSystem()

        # Derin hiyerarsi olustur
        previous_role = None
        all_permissions = set()

        for i in range(role_count):
            role_id = f"role_{i}"
            permission = f"resource_{i}:action_{i}"
            all_permissions.add(permission)

            parent_roles = [previous_role] if previous_role else []
            rbac.create_role(role_id, f"Role {i}", {permission}, parent_roles)

            previous_role = role_id

        # En alt rol tum izinleri miras almali
        bottom_role = f"role_{role_count - 1}"
        inherited = rbac.get_inherited_permissions(bottom_role)

        assert inherited == all_permissions, \
            f"Bottom role should inherit all {role_count} permissions"

    @given(
        num_permissions=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100)
    def test_direct_and_inherited_merge(self, num_permissions: int):
        """
        Property 4.5: Dogrudan ve miras izinler birlestirilmeli.

        REQ-4.3: Direct + inherited permission merging
        """
        rbac = RBACSystem()

        # Ust rol
        parent_perms = {f"parent:perm_{i}" for i in range(num_permissions)}
        rbac.create_role("parent", "Parent", parent_perms)

        # Alt rol (kendi izinleri + miras)
        child_perms = {f"child:perm_{i}" for i in range(num_permissions)}
        rbac.create_role("child", "Child", child_perms, ["parent"])

        inherited = rbac.get_inherited_permissions("child")

        # Hem kendi hem miras izinler olmali
        assert child_perms.issubset(inherited), \
            "Child's direct permissions should be in inherited"
        assert parent_perms.issubset(inherited), \
            "Parent's permissions should be inherited"

        # Toplam izin sayisi dogu olmali
        assert len(inherited) == 2 * num_permissions

    @given(
        user_id=st.text(min_size=5, max_size=20)
    )
    @settings(max_examples=100)
    def test_inactive_role_no_permissions(self, user_id: str):
        """
        Property 4.6: Inaktif rol izin vermemeli.

        REQ-4.4: Role validity constraints
        """
        rbac = RBACSystem()

        # Inaktif rol
        role = rbac.create_role("inactive", "Inactive", {"test:read"})
        role.is_active = False

        rbac.assign_role_to_user(user_id, "inactive")

        permissions = rbac.get_user_permissions(user_id)

        assert len(permissions) == 0, \
            "Inactive role should grant no permissions"

    @given(
        hours_offset=st.integers(min_value=-48, max_value=48)
    )
    @settings(max_examples=100)
    def test_time_bounded_role(self, hours_offset: int):
        """
        Property 4.7: Zaman sinirli roller dogru calismal.

        valid_from ve valid_until kontrolleri.
        """
        rbac = RBACSystem()
        now = datetime.now(UTC)

        # 24 saat gecerli rol
        role = rbac.create_role("timed", "Timed Role", {"temp:read"})
        role.valid_from = now - timedelta(hours=12)
        role.valid_until = now + timedelta(hours=12)

        check_time = now + timedelta(hours=hours_offset)
        is_valid = role.is_valid(check_time)

        # -12 ile +12 saat arasi gecerli
        expected_valid = -12 <= hours_offset <= 12
        assert is_valid == expected_valid, \
            f"Role validity at offset {hours_offset}h should be {expected_valid}"


class TestRBACHierarchyProperties:
    """RBAC hiyerarsisi property-based testleri."""

    def setup_method(self):
        """Her test oncesi RBAC sistemi olustur."""
        self.rbac = RBACSystem()

    @given(
        depth=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_hierarchy_depth_calculation(self, depth: int):
        """
        Property 4.8: Hiyerarsi derinligi dogru hesaplanmali.
        """
        # depth seviyeli hiyerarsi olustur
        previous = None
        for i in range(depth):
            role_id = f"level_{i}"
            parents = [previous] if previous else []
            self.rbac.create_role(role_id, f"Level {i}", set(), parents)
            previous = role_id

        # En alt rolun derinligi
        bottom_depth = self.rbac.get_role_hierarchy_depth(f"level_{depth - 1}")

        assert bottom_depth == depth, \
            f"Hierarchy depth should be {depth}, got {bottom_depth}"

    @given(
        branch_count=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=100)
    def test_multiple_parents_merge_permissions(self, branch_count: int):
        """
        Property 4.9: Coklu ust rolden izinler birlestirilmeli.

        Diamond inheritance pattern.
        """
        # Birden fazla ust rol
        parent_perms = []
        for i in range(branch_count):
            perms = {f"parent_{i}:read", f"parent_{i}:write"}
            self.rbac.create_role(f"parent_{i}", f"Parent {i}", perms)
            parent_perms.extend(perms)

        # Alt rol tum ust rollerden miras aliyor
        parent_ids = [f"parent_{i}" for i in range(branch_count)]
        self.rbac.create_role("child", "Child", {"child:own"}, parent_ids)

        inherited = self.rbac.get_inherited_permissions("child")

        # Tum ust rol izinleri miras alinmali
        for perm in parent_perms:
            assert perm in inherited, \
                f"Permission {perm} should be inherited from parents"

    @given(
        num_users=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100)
    def test_role_shared_among_users(self, num_users: int):
        """
        Property 4.10: Ayni rol birden fazla kullaniciya atanabilmeli.
        """
        self.rbac.create_role("shared", "Shared Role", {"shared:read"})

        users = [f"user_{i}" for i in range(num_users)]
        for user_id in users:
            self.rbac.assign_role_to_user(user_id, "shared")

        # Tum kullanicilar ayni izne sahip olmali
        for user_id in users:
            assert self.rbac.has_permission(user_id, "shared:read"), \
                f"User {user_id} should have shared:read permission"

    @given(
        role_count=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=100)
    def test_user_multiple_roles(self, role_count: int):
        """
        Property 4.11: Kullanici birden fazla role sahip olabilmeli.
        """
        user_id = "multi_role_user"
        all_permissions = set()

        for i in range(role_count):
            perms = {f"role_{i}:read", f"role_{i}:write"}
            all_permissions.update(perms)
            self.rbac.create_role(f"role_{i}", f"Role {i}", perms)
            self.rbac.assign_role_to_user(user_id, f"role_{i}")

        user_perms = self.rbac.get_user_permissions(user_id)

        assert user_perms == all_permissions, \
            f"User should have all permissions from {role_count} roles"


class TestRBACCycleDetectionProperties:
    """RBAC dongu tespiti property-based testleri."""

    def setup_method(self):
        """Her test oncesi RBAC sistemi olustur."""
        self.rbac = RBACSystem()

    @given(
        cycle_size=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=100)
    def test_circular_hierarchy_handled(self, cycle_size: int):
        """
        Property 4.12: Dongusel hiyerarsi dogru ele alinmali.

        A -> B -> C -> A gibi dongulerde sonsuz dongu olmamali.
        """
        # Dongusel hiyerarsi olustur
        for i in range(cycle_size):
            role_id = f"cycle_{i}"
            perms = {f"perm_{i}"}
            # Son rol ilk role bagli (dongu)
            parent = f"cycle_{(i + 1) % cycle_size}"
            self.rbac.create_role(role_id, f"Cycle {i}", perms)

        # Simdi parent baglantilari ekle
        for i in range(cycle_size):
            role_id = f"cycle_{i}"
            parent = f"cycle_{(i + 1) % cycle_size}"
            self.rbac.add_parent_role(role_id, parent)

        # Izinleri al - sonsuz donguye girmemeli
        try:
            perms = self.rbac.get_inherited_permissions("cycle_0")
            # Sonlu sayida izin donmeli
            assert len(perms) <= cycle_size, \
                f"Cycle detection should limit permissions to {cycle_size}"
        except RecursionError:
            pytest.fail("Cycle detection failed - infinite recursion")

    @given(
        permission=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz:_"),
            min_size=5,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_permission_format_preserved(self, permission: str):
        """
        Property 4.13: Izin formati korunmali.

        "resource:action" formati her zaman gecerli olmali.
        """
        # ":" icermeli (gecerli format)
        assume(":" in permission)

        self.rbac.create_role("test", "Test", {permission})
        perms = self.rbac.get_inherited_permissions("test")

        assert permission in perms, \
            f"Permission {permission} should be preserved exactly"
