from typing import List

from traitlets.config import LoggingConfigurable


class CondaStoreBuidler(LoggingConfigurable):
    # build_artifact types which the builder is responsible for
    build_artifacts: List[str] = []

    # builders which this builder depends upon
    depends_on: List["CondaStoreBuilder"] = []

    def build_artifact(self, conda_store: "CondaStore", artifact_type: str, build_id: str):
        pass

    def delete_artifact(self, conda_store: "CondaStore", artifact_type: str, build_id: str):
        pass
