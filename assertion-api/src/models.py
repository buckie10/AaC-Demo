from pydantic import BaseModel, ConfigDict, Field


class Connection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: str
    target: str


class Component(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    type: str
    connections: list[Connection] = Field(default_factory=list)


class Deployment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    application: str
    components: list[Component]


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    manifestVersion: str
    deployment: Deployment
