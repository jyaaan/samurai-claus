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