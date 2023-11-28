import enum

class SequenceStageEnum(enum.Enum):
    Initialized = "Initialized"
    Introduction_Sent = "Introduction Sent"
    Participant_Confirmation = "Participant Confirmation"
    Wishlist_Request_Sent = "Wishlist Request Sent"
    Address_Request_Sent = "Address Request Sent"
    Other_Question_Sent = "Other Question Sent"
    Request_Received = "Request Received"
    Technical_Error = "Technical Error"
    Unable_to_Process = "Unable to Process"

class MessageQueueStatusEnum(enum.Enum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    PROCESSING = "processing"
    PROCESSED = "processed"
    RECEIVED = "received"
    HOLD = "hold"
    ERROR = "error"

class OpenAIMessageTypesEnum(enum.Enum):
    CHAT = "chat"
    ADDRESS = "address"
    WIHSLIST = "wishlist"
    ERROR = "error"

samurai_claus_images = [
    'https://i.imgur.com/zfiMcvz.png',
    'https://i.imgur.com/bdTPTvf.png',
    'https://i.imgur.com/eHgw8hH.png',
    'https://i.imgur.com/YvNNIw3.png',
    'https://i.imgur.com/BRcodYS.png',
    'https://i.imgur.com/5GhS4cP.png',
    'https://i.imgur.com/6M5TiSB.png',
    'https://i.imgur.com/znZchtP.png',
    'https://i.imgur.com/5UC034y.png',
    'https://i.imgur.com/ciCsYeJ.png',
    'https://i.imgur.com/adwxlAu.png',
    'https://i.imgur.com/y0VZZci.png',
]