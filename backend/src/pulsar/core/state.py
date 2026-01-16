from ..domain import Cluster

# TODO: This thing will actually frickin EXPLODE
clusters_cache: dict[str, Cluster] = {}
jobs: dict[str, dict] = {}
