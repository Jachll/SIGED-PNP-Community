ADMIN_ROLES = ("admin",)
OPERATIONAL_ROLES = ("admin", "analista")
ANALYTICS_ROLES = ("admin", "analista", "consulta")
TERRITORIAL_READ_ROLES = ANALYTICS_ROLES

ROLE_POLICIES = {
    "administrative": ADMIN_ROLES,
    "operational": OPERATIONAL_ROLES,
    "analytics": ANALYTICS_ROLES,
    "territorial_read": TERRITORIAL_READ_ROLES,
}
