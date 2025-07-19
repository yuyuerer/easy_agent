from pydantic import BaseModel


# The response format for the agent as a Pydantic base model.
class AnalystResponse(BaseModel):
    requirement: str
    research_result: str