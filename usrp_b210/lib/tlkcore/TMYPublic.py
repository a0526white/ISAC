from enum import Enum, Flag, auto, IntEnum
from typing import Union

class RIS_Dir(dict):
    """
    A dict structure for RIS direction includes distance and angle.

    Args:
        distance (float): Distance from RIS to the source/target
        angle (tuple): Angle of the target, given in (theta, phi) format or theta only with phi=0, Defaults to (0,0)

    Examples:
        * For a distance of 1 meter and an angle of (0, 0):
            >>> RIS_Dir(1)
        * For a distance of 1 meter and an angle of (0, 0):
            >>> RIS_Dir(1, (0, 0))
        * For a distance of 1 meter and an angle of (30, 0):
            >>> RIS_Dir(1, (30, 0))
    """
    def __init__(self, distance, angle:Union[int, tuple]=(0,0)):
        self['distance'] = distance
        if isinstance(angle, int):
            self['angle'] = (angle, 0)
        # elif isinstance(angle, tuple):
        #     # TODO: for multiple reflection angle only
        #     self['angle'] = [angle]
        else:
            self['angle'] = angle

class RIS_ModuleConfig(dict):
    """
    A data structure for RIS module configuration.

    Args:
        central_freq_mhz (int): Operating central frequency in MHz.
        module (Union[int, list]): Specifies the target module partition to control.
            It can be a single value (e.g. 1), or a list (e.g. [1, 2]),
            or a nested list (e.g. [[1, 2]] or [[1, 2], [3, 4]]). Defaults to 1.
        module_rotate (dict): Specifies the clockwise rotation degree for each module, therefore the actual pattern will be counter-clockwise rotation
            The degree must be a multiple of 90.

    Examples:
        * 28GHz with only module 1, no rotation:
            >>> RIS_ModuleConfig(28000, 1)
        * 28GHz with module 1 and 2 in landscape orientation, no rotation:
            >>> RIS_ModuleConfig(28000, [1, 2])
        * 28GHz with module 1 and 2 in portrait orientation, rotate module 1 by 90 degrees:
            >>> RIS_ModuleConfig(28000, [[1], [2]], {'1': 90})
        * 28GHz with module 1 and 2 in landscape orientation, rotate module 1 by 90 degrees and module 2 by 180 degrees:
            >>> RIS_ModuleConfig(28000, [1, 2], {'1': 90, '2': 180})
        * 28GHz with module 1,2,3,4 in landscape orientation, no rotation:
            >>> RIS_ModuleConfig(28000, [1, 2, 3, 4])
        * 28GHz with module 1,2,3,4 in portrait orientation, no rotation:
            >>> RIS_ModuleConfig(28000, [[1], [2], [3], [4]])
        * 28GHz with module 1,2,3,4 in square orientation, rotate module 1 by 90 degrees and module 2 by 180 degrees:
            >>> RIS_ModuleConfig(28000, [[1, 2],
                                         [3, 4]], {'1': 90, '2': 180})
    """
    def __init__(self, central_freq_mhz:float, module:Union[int, list]=1, module_rotate=None):
        self['central_freq_mhz'] = central_freq_mhz
        self['module'] = module
        self['module_rotate'] = module_rotate

class DevInterface(Flag):
    """
    Defines device connect interface for scanning.
    """
    UNKNOWN = 0
    LAN     = auto()
    COMPORT = auto()
    USB     = auto()
    ALL     = LAN | COMPORT | USB

class ScanFilter(Flag):
    NONE    = 0
    NORMAL  = auto()
    DFU     = auto()
    ALL     = NORMAL | DFU

class IPMode(Enum):
    """
    Defines device IP mode as DHCP or static IP mode.
    """
    DHCP        = 0
    STATIC_IP   = auto()

class RFMode(Enum):
    """
    Defines RF mode of beamform devices series.
    """
    TX      = 0
    RX      = auto()

class CellRFMode(Enum):
    STANDBY = -1
    TX      = 0
    RX      = auto()

class BeamType(Enum):
    """
    Defines beam type of beamform devices series for beam configuration.
    """
    BEAM    = 0
    CHANNEL = auto()

class RetCode(Enum):
    """
    Error code to represent the status of operations in TLKCore.
    """
    def __str__(self):
        return self.name
    def __int__(self):
        return self.value
    OK                      = 0
    WARNING                 = auto()
    ERROR                   = auto()
    NO_RESPONSE             = auto()
    # genereal operations
    ERROR_GET_SN            = 10
    ERROR_DEV_TYPE          = auto()
    ERROR_SCAN              = auto()
    ERROR_INIT_OBJECT       = auto()
    ERROR_DEV_NOT_INIT      = auto()
    ERROR_METHOD_NOT_FOUND  = auto()
    ERROR_METHOD_NOT_SUPPORT= auto()
    ERROR_REFLECTION        = auto()
    ERROR_POWER             = auto()
    ERROR_EXPORT_LOG        = auto()
    ERROR_FW_NOT_SUPPORT    = auto()

    # Communication interface related
    ERROR_COMM_NOT_INIT     = 30
    ERROR_COMM_INIT         = auto()
    ERROR_DISCONNECT        = auto()
    ERROR_SOCKET            = auto()
    ERROR_SEND_CMD          = auto()
    ERROR_RESP_CMD          = auto()
    ERROR_SEND_CMD_TIMEOUT  = auto()
    ERROR_COMPORT           = auto()
    ERROR_USB               = auto()

    # CMD to device
    ERROR_CMD               = 40
    ERROR_CMD_INIT          = auto()
    ERROR_CMD_PARAM         = auto()

    # WEB - Database related
    ERROR_DB_SERVER         = 50
    ERROR_DB_FEEDBACK       = auto()

    # DFU - Device Firmware Update related
    ERROR_DFU               = 60
    ERROR_DFU_NOT_SUPPORT   = auto()
    ERROR_DFU_TYPE          = auto()
    ERROR_DFU_HEADER        = auto()
    ERROR_DFU_TRANSMIT      = auto()

    # Beamforming device
    ERROR_BF_STATE          = 100
    ERROR_BF_AAKIT          = auto()
    ERROR_BF_NO_AAKIT       = auto()
    ERROR_BF_CALI_PATH      = auto()
    ERROR_BF_BEAM           = auto()
    ERROR_BF_GAIN           = auto()
    ERROR_BF_PHASE          = auto()
    ERROR_BF_RFMODE         = auto()
    ERROR_BF_CALI_INCOMPLTE = auto()
    ERROR_BF_CALI_PARSE     = auto()
    ERROR_BF_TC             = auto()
    ERROR_BF_BEAM_FILE      = auto()
    # PD device
    ERROR_PD_CALI           = 150
    ERROR_PD_SOURCE         = auto()
    # RIS device
    ERROR_RIS_MODULE        = 160
    ERROR_RIS_CONFIG        = auto()
    # UDM/UDB device
    ERROR_FREQ_RANGE        = 240
    ERROR_LICENSE_LENGTH    = auto()
    ERROR_LICENSE_KEY       = auto()
    ERROR_REF_CHANGE        = auto()
    # UD device
    ERROR_UD_FREQ           = 245
    ERROR_FREQ_EQUATION     = 250
    WARNING_HARMONIC        = auto()
    ERROR_HARMONIC_BLOCK    = auto()
    ERROR_PLO_UNLOCK        = 253
    ERROR_PLO_CRC           = auto()
    ERROR_UD_STATE          = auto()

class UDFreq(Enum):
    """
    UD frequency related categories, also used for key name of dict when calling :func:`~tlkcore.tmydev.DevUDBox.getUDFreq`
    """
    def __str__(self):
        return self.name
    UDFreq  = 0
    RFFreq  = auto()
    IFFreq  = auto()

class UDState(Enum):
    """
    The state of UDBox5G
    """
    NO_SET          = -1
    PLO_LOCK        = 0
    CH1             = auto()
    CH2             = auto() # ignore it if single UD
    OUT_10M         = auto()
    OUT_100M        = auto()
    SOURCE_100M     = auto() # 0:Internal, 1:External
    LED_100M        = auto() # 0:OFF, 1:WHITE, 2:BLUE
    PWR_5V          = auto()
    PWR_9V          = auto()

class UDMState(Flag):
    """
    The state of UDM
    """
    NO_SET      = 0
    SYSTEM      = auto()
    PLO_LOCK    = auto()
    REF_LOCK    = auto()
    LICENSE     = auto()
    ALL         = SYSTEM | PLO_LOCK | REF_LOCK | LICENSE

class UDM_SYS(Enum):
    """
    It defines the :attr:`UDMState.SYSTEM` state of UDM
    """
    SYS_ERROR       = -1
    NORMAL          = 0

class UD_PLO(Enum):
    """
    It defines the :attr:`UDMState.PLO_LOCK` state of UD series
    """
    UNLOCK          = -1
    LOCK            = 0

class UD_REF(Enum):
    """
    It defines the :attr:`UDMState.REF_LOCK` state of UD series
    """
    UNLOCK          = -1
    INTERNAL        = 0
    EXTERNAL        = auto()

class UDM_LICENSE(Enum):
    """
    It defines the :attr:`UDMState.LICENSE` state of UDM
    """
    VERIFY_FAIL_FLASH   = -2
    VERIFY_FAIL_DIGEST  = -1
    NON_LICENSE         = 0
    VERIFY_PASS         = auto()

class UD_SN_TYPE(Flag):
    """
    The SN type of UD
    """
    UD_BOX      = 1
    UD_MODULE   = auto()
    ALL         = UD_BOX | UD_MODULE

class UD_LO_CONFIG(Enum):
    """
    It defines the LO config for UDB series
    """
    LO_CFG_INTERNAL     = 0
    LO_CFG_INTERNAL_OUT = auto()
    LO_CFG_EXTERNAL_IN  = auto()
    def __str__(self):
        return self.name

class POLARIZATION(Flag):
    HORIZON         = 1
    VERTICAL        = auto()
    DUAL            = HORIZON | VERTICAL
    def __str__(self):
        return self.name.lower()

class POLAR_SYNTHESIS(IntEnum):
    FORWARD             = 0
    BACKWARD            = 180
    RIGHT_HAND_CIRCULAR = 90
    LEFT_HAND_CIRCULAR  = 270
    def __str__(self):
        return self.name
    def __int__(self):
        return self.value
