from enum import Enum
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    '''
    Enum classes for returning type of memory format.
    '''
    long_term = 'long_term'
    event = 'event'
    none = 'none'


class Classifier(BaseModel):
    '''
    Returns Response to the user query along with the type of memory the chat needs to be saved as.
    '''    
    mtype: MemoryType = Field(description="Classification of memory")

    class Config:
        use_enum_values = True


class ResponseFormatter(BaseModel):
    '''
    Returns Response to the user query along with the type of memory the chat needs to be saved as.
    '''    
    response: str = Field(description="Response to the user prompt")
    mtype: MemoryType = Field(description="Classification of memory")

    class Config:
        use_enum_values = True

