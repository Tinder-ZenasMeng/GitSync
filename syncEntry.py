import dataclasses

@dataclasses.dataclass
class SyncEntry(object):
    sourceRepo: str
    sourceUrl: str
    destUrl: str
    yamlPath: str