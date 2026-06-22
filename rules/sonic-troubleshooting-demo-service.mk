# sonic-troubleshooting-demo-service wheel package
#
# Place this file in: sonic-buildimage/rules/
# Then add to the platform config or build directly:
#   make target/python-wheels/bullseye/sonic_troubleshooting_demo_service-0.1.0-py3-none-any.whl

SONIC_TROUBLESHOOTING_DEMO_SERVICE_VERSION = 0.1.0
SONIC_TROUBLESHOOTING_DEMO_SERVICE_NAME = sonic_troubleshooting_demo_service

SONIC_TROUBLESHOOTING_DEMO_SERVICE = $(SONIC_TROUBLESHOOTING_DEMO_SERVICE_NAME)-$(SONIC_TROUBLESHOOTING_DEMO_SERVICE_VERSION)-py3-none-any.whl
$(SONIC_TROUBLESHOOTING_DEMO_SERVICE)_SRC_PATH = $(SRC_PATH)/sonic-troubleshooting-demo-service
$(SONIC_TROUBLESHOOTING_DEMO_SERVICE)_PYTHON_VERSION = 3
$(SONIC_TROUBLESHOOTING_DEMO_SERVICE)_NAME = $(SONIC_TROUBLESHOOTING_DEMO_SERVICE_NAME)
$(SONIC_TROUBLESHOOTING_DEMO_SERVICE)_VERSION = $(SONIC_TROUBLESHOOTING_DEMO_SERVICE_VERSION)

# Runtime Redis access — no SONiC-specific C dependencies needed
$(SONIC_TROUBLESHOOTING_DEMO_SERVICE)_DEBS_DEPENDS = $(LIBSWSSCOMMON) \
                                                      $(PYTHON3_SWSSCOMMON)

# Build-only: no other SONiC wheels needed before this one
# Add here if the service later depends on sonic-py-common or sonic-utilities
# $(SONIC_TROUBLESHOOTING_DEMO_SERVICE)_DEPENDS += $(SONIC_PY_COMMON_PY3)

SONIC_PYTHON_WHEELS += $(SONIC_TROUBLESHOOTING_DEMO_SERVICE)
