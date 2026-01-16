
from fastapi import APIRouter, HTTPException

from ....core.state import clusters_cache
from ....domain import Cluster
from ....infrastructure.clients.openai import analyze_cluster_coverage, is_ai_available

router = APIRouter()

@router.get("/cluster/{cluster_id}", response_model=Cluster)
def get_cluster_detail(cluster_id: str) -> Cluster:
    if cluster_id not in clusters_cache:
        raise HTTPException(status_code=404, detail="Cluster not found")

    cluster = clusters_cache[cluster_id]

    if not cluster.analysis and is_ai_available():
        cluster.analysis = analyze_cluster_coverage(cluster.articles)
        clusters_cache[cluster_id] = cluster

    return cluster
