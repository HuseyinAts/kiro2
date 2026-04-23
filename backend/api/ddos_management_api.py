"""
DDoS Protection Management API (Task 51.4)
Admin endpoints for managing IP whitelist/blacklist and monitoring

Author: Claude
Date: 2025-10-27
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.dependencies import get_current_admin_user
from core.enhanced_ddos_protection import get_ddos_protection
from core.structured_logger import get_logger

logger = get_logger("ddos_management_api")

router = APIRouter(prefix="/api/v1/ddos", tags=["DDoS Management"])


class IPActionRequest(BaseModel):
    """IP action request"""

    ip: str
    reason: str | None = None


class IPListResponse(BaseModel):
    """IP list response"""

    ips: list[str]
    count: int


class IPReputationResponse(BaseModel):
    """IP reputation response"""

    ip: str
    threat_level: str
    total_requests: int
    blocked_count: int
    last_seen: float
    first_seen: float
    suspicious_patterns: list[str]
    whitelist: bool


class DDoSStatisticsResponse(BaseModel):
    """DDoS statistics response"""

    blocked_ips_count: int
    whitelisted_ips_count: int
    blacklisted_ips_count: int
    tracked_ips_count: int
    active_connections: int
    thresholds: dict


@router.post("/whitelist/add", summary="Add IP to Whitelist (Admin Only)")
async def add_to_whitelist(
    request: IPActionRequest,
    current_admin: dict = Depends(get_current_admin_user),
):
    """
    Add IP to whitelist (bypass all DDoS checks) (Task 51.4)

    Requires admin role.
    """
    try:
        ddos_protection = get_ddos_protection()
        ddos_protection.whitelist_ip(request.ip)

        logger.info(
            f"[DDOS API] IP whitelisted: {request.ip}",
            extra_data={"ip": request.ip, "reason": request.reason},
        )

        return {
            "message": f"IP {request.ip} başarıyla whitelist'e eklendi",
            "ip": request.ip,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DDOS API] Failed to whitelist IP: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.post("/whitelist/remove", summary="Remove IP from Whitelist (Admin Only)")
async def remove_from_whitelist(
    request: IPActionRequest,
    current_admin: dict = Depends(get_current_admin_user),
):
    """
    Remove IP from whitelist (Task 51.4)

    Requires admin role.
    """
    try:
        ddos_protection = get_ddos_protection()
        ddos_protection.remove_from_whitelist(request.ip)

        logger.info(f"[DDOS API] IP removed from whitelist: {request.ip}")

        return {
            "message": f"IP {request.ip} whitelist'ten çıkarıldı",
            "ip": request.ip,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DDOS API] Failed to remove from whitelist: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get(
    "/whitelist",
    response_model=IPListResponse,
    summary="Get Whitelisted IPs (Admin Only)",
)
async def get_whitelist(current_admin: dict = Depends(get_current_admin_user)):
    """
    Get list of whitelisted IPs (Task 51.4)

    Requires admin role.
    """
    try:
        ddos_protection = get_ddos_protection()
        ips = ddos_protection.get_whitelisted_ips()

        return IPListResponse(ips=ips, count=len(ips))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DDOS API] Failed to get whitelist: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.post("/blacklist/add", summary="Add IP to Blacklist (Admin Only)")
async def add_to_blacklist(
    request: IPActionRequest,
    current_admin: dict = Depends(get_current_admin_user),
):
    """
    Add IP to permanent blacklist (Task 51.4)

    Requires admin role.
    """
    try:
        ddos_protection = get_ddos_protection()
        reason = request.reason or "Manual block by admin"
        ddos_protection.blacklist_ip(request.ip, reason)

        logger.warning(
            f"[DDOS API] IP blacklisted: {request.ip}",
            extra_data={"ip": request.ip, "reason": reason},
        )

        return {
            "message": f"IP {request.ip} kalıcı olarak engellendi",
            "ip": request.ip,
            "reason": reason,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DDOS API] Failed to blacklist IP: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.post("/blacklist/remove", summary="Remove IP from Blacklist (Admin Only)")
async def remove_from_blacklist(
    request: IPActionRequest,
    current_admin: dict = Depends(get_current_admin_user),
):
    """
    Remove IP from blacklist (Task 51.4)

    Requires admin role.
    """
    try:
        ddos_protection = get_ddos_protection()
        ddos_protection.remove_from_blacklist(request.ip)

        logger.info(f"[DDOS API] IP removed from blacklist: {request.ip}")

        return {
            "message": f"IP {request.ip} blacklist'ten çıkarıldı",
            "ip": request.ip,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DDOS API] Failed to remove from blacklist: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get(
    "/blacklist",
    response_model=IPListResponse,
    summary="Get Blacklisted IPs (Admin Only)",
)
async def get_blacklist(current_admin: dict = Depends(get_current_admin_user)):
    """
    Get list of blacklisted IPs (Task 51.4)

    Requires admin role.
    """
    try:
        ddos_protection = get_ddos_protection()
        ips = ddos_protection.get_blacklisted_ips()

        return IPListResponse(ips=ips, count=len(ips))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DDOS API] Failed to get blacklist: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get(
    "/blocked",
    response_model=IPListResponse,
    summary="Get Currently Blocked IPs (Admin Only)",
)
async def get_blocked_ips(current_admin: dict = Depends(get_current_admin_user)):
    """
    Get list of currently blocked IPs (temporary blocks) (Task 51.4)

    Requires admin role.
    """
    try:
        ddos_protection = get_ddos_protection()
        ips = ddos_protection.get_blocked_ips()

        return IPListResponse(ips=ips, count=len(ips))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DDOS API] Failed to get blocked IPs: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.post("/unblock", summary="Manually Unblock IP (Admin Only)")
async def unblock_ip(
    request: IPActionRequest,
    current_admin: dict = Depends(get_current_admin_user),
):
    """
    Manually unblock a temporarily blocked IP (Task 51.4)

    Requires admin role.
    """
    try:
        ddos_protection = get_ddos_protection()
        ddos_protection.unblock_ip(request.ip)

        logger.info(f"[DDOS API] IP manually unblocked: {request.ip}")

        return {
            "message": f"IP {request.ip} engeli kaldırıldı",
            "ip": request.ip,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DDOS API] Failed to unblock IP: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get(
    "/reputation/{ip}",
    response_model=IPReputationResponse,
    summary="Get IP Reputation (Admin Only)",
)
async def get_ip_reputation(
    ip: str,
    current_admin: dict = Depends(get_current_admin_user),
):
    """
    Get reputation information for an IP (Task 51.4)

    Requires admin role.
    """
    try:
        ddos_protection = get_ddos_protection()
        reputation = ddos_protection.get_ip_reputation(ip)

        if not reputation:
            raise HTTPException(
                status_code=404, detail=f"IP {ip} için reputation bilgisi bulunamadı"
            )

        return IPReputationResponse(
            ip=reputation.ip,
            threat_level=reputation.threat_level.value,
            total_requests=reputation.total_requests,
            blocked_count=reputation.blocked_count,
            last_seen=reputation.last_seen,
            first_seen=reputation.first_seen,
            suspicious_patterns=reputation.suspicious_patterns,
            whitelist=reputation.whitelist,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DDOS API] Failed to get IP reputation: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get(
    "/statistics",
    response_model=DDoSStatisticsResponse,
    summary="Get DDoS Statistics (Admin Only)",
)
async def get_ddos_statistics(current_admin: dict = Depends(get_current_admin_user)):
    """
    Get DDoS protection statistics (Task 51.4)

    Requires admin role.
    """
    try:
        ddos_protection = get_ddos_protection()
        stats = ddos_protection.get_statistics()

        return DDoSStatisticsResponse(**stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DDOS API] Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")
