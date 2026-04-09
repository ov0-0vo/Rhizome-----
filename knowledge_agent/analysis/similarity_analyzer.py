import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..knowledge.knowledge_store import KnowledgeStore
from ..knowledge.catalog_manager import CatalogManager
from ..storage.vector_store import VectorStoreManager, create_embeddings

logger = logging.getLogger(__name__)


def pca_reduce(X: np.ndarray, n_components: int = 2) -> np.ndarray:
    if X.shape[0] == 0:
        return np.array([])
    
    X_centered = X - np.mean(X, axis=0)
    
    cov_matrix = np.cov(X_centered.T)
    
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    
    idx = np.argsort(eigenvalues)[::-1]
    eigenvectors = eigenvectors[:, idx]
    
    n_components = min(n_components, eigenvectors.shape[1])
    principal_components = eigenvectors[:, :n_components]
    
    return np.dot(X_centered, principal_components)


@dataclass
class SimilarityResult:
    id1: str
    id2: str
    question1: str
    question2: str
    similarity: float
    catalog_id1: str
    catalog_id2: str


@dataclass
class DistributionStats:
    total_knowledge: int
    total_pairs: int
    mean_similarity: float
    median_similarity: float
    std_similarity: float
    min_similarity: float
    max_similarity: float
    high_similarity_count: int
    high_similarity_threshold: float
    distribution_bins: List[Dict[str, Any]]


class SimilarityAnalyzer:
    def __init__(
        self,
        knowledge_store: KnowledgeStore = None,
        catalog_manager: CatalogManager = None
    ):
        self.knowledge_store = knowledge_store or KnowledgeStore()
        self.catalog_manager = catalog_manager or CatalogManager()
        self.vector_store = self.knowledge_store.vector_store
        self.embeddings = create_embeddings()
        self._embedding_cache: Dict[str, np.ndarray] = {}
    
    def get_embedding(self, text: str) -> np.ndarray:
        return np.array(self.embeddings.embed_query(text))
    
    def get_all_embeddings(self) -> Tuple[List[str], np.ndarray]:
        all_knowledge = self.knowledge_store.get_all_knowledge()
        
        if not all_knowledge:
            return [], np.array([])
        
        ids = []
        embeddings = []
        
        for item in all_knowledge:
            text = f"问题: {item.question}\n答案: {item.answer}"
            
            if item.id in self._embedding_cache:
                embedding = self._embedding_cache[item.id]
            else:
                embedding = self.get_embedding(text)
                self._embedding_cache[item.id] = embedding
            
            ids.append(item.id)
            embeddings.append(embedding)
        
        return ids, np.array(embeddings)
    
    def compute_similarity_matrix(self) -> Tuple[List[str], np.ndarray]:
        ids, embeddings = self.get_all_embeddings()
        
        if len(ids) == 0:
            return [], np.array([])
        
        embeddings_normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        similarity_matrix = np.dot(embeddings_normalized, embeddings_normalized.T)
        
        return ids, similarity_matrix
    
    def analyze_distribution(
        self,
        high_similarity_threshold: float = 0.85
    ) -> DistributionStats:
        ids, similarity_matrix = self.compute_similarity_matrix()
        
        if len(ids) == 0:
            return DistributionStats(
                total_knowledge=0,
                total_pairs=0,
                mean_similarity=0.0,
                median_similarity=0.0,
                std_similarity=0.0,
                min_similarity=0.0,
                max_similarity=0.0,
                high_similarity_count=0,
                high_similarity_threshold=high_similarity_threshold,
                distribution_bins=[]
            )
        
        n = len(ids)
        upper_triangle_indices = np.triu_indices(n, k=1)
        similarities = similarity_matrix[upper_triangle_indices]
        
        total_pairs = len(similarities)
        mean_sim = float(np.mean(similarities))
        median_sim = float(np.median(similarities))
        std_sim = float(np.std(similarities))
        min_sim = float(np.min(similarities))
        max_sim = float(np.max(similarities))
        high_sim_count = int(np.sum(similarities >= high_similarity_threshold))
        
        bins = np.linspace(0, 1, 11)
        hist, _ = np.histogram(similarities, bins=bins)
        
        distribution_bins = []
        for i in range(len(hist)):
            distribution_bins.append({
                "range_start": float(bins[i]),
                "range_end": float(bins[i + 1]),
                "count": int(hist[i]),
                "percentage": float(hist[i] / total_pairs * 100) if total_pairs > 0 else 0.0
            })
        
        return DistributionStats(
            total_knowledge=n,
            total_pairs=total_pairs,
            mean_similarity=mean_sim,
            median_similarity=median_sim,
            std_similarity=std_sim,
            min_similarity=min_sim,
            max_similarity=max_sim,
            high_similarity_count=high_sim_count,
            high_similarity_threshold=high_similarity_threshold,
            distribution_bins=distribution_bins
        )
    
    def find_similar_pairs(
        self,
        threshold: float = 0.85,
        limit: int = 50
    ) -> List[SimilarityResult]:
        ids, similarity_matrix = self.compute_similarity_matrix()
        
        if len(ids) == 0:
            return []
        
        n = len(ids)
        results = []
        
        for i in range(n):
            for j in range(i + 1, n):
                sim = similarity_matrix[i, j]
                if sim >= threshold:
                    item1 = self.knowledge_store.get_knowledge(ids[i])
                    item2 = self.knowledge_store.get_knowledge(ids[j])
                    
                    if item1 and item2:
                        results.append(SimilarityResult(
                            id1=ids[i],
                            id2=ids[j],
                            question1=item1.question,
                            question2=item2.question,
                            similarity=float(sim),
                            catalog_id1=item1.catalog_id or "",
                            catalog_id2=item2.catalog_id or ""
                        ))
        
        results.sort(key=lambda x: x.similarity, reverse=True)
        return results[:limit]
    
    def find_duplicates(
        self,
        threshold: float = 0.90
    ) -> List[Dict[str, Any]]:
        similar_pairs = self.find_similar_pairs(threshold=threshold, limit=100)
        
        duplicate_groups = {}
        for pair in similar_pairs:
            if pair.id1 not in duplicate_groups:
                duplicate_groups[pair.id1] = {
                    "primary_id": pair.id1,
                    "primary_question": pair.question1,
                    "duplicates": []
                }
            
            duplicate_groups[pair.id1]["duplicates"].append({
                "id": pair.id2,
                "question": pair.question2,
                "similarity": pair.similarity
            })
        
        return list(duplicate_groups.values())
    
    def get_distribution_chart_data(self) -> Dict[str, Any]:
        stats = self.analyze_distribution()
        
        return {
            "labels": [f"{b['range_start']:.1f}-{b['range_end']:.1f}" for b in stats.distribution_bins],
            "counts": [b['count'] for b in stats.distribution_bins],
            "percentages": [b['percentage'] for b in stats.distribution_bins],
            "statistics": {
                "total_knowledge": stats.total_knowledge,
                "total_pairs": stats.total_pairs,
                "mean": stats.mean_similarity,
                "median": stats.median_similarity,
                "std": stats.std_similarity,
                "min": stats.min_similarity,
                "max": stats.max_similarity,
                "high_similarity_count": stats.high_similarity_count,
                "high_similarity_threshold": stats.high_similarity_threshold
            }
        }
    
    def analyze_catalog_distribution(self) -> List[Dict[str, Any]]:
        all_knowledge = self.knowledge_store.get_all_knowledge()
        catalog_counts: Dict[str, int] = {}
        
        for item in all_knowledge:
            catalog_id = item.catalog_id or "uncategorized"
            catalog_counts[catalog_id] = catalog_counts.get(catalog_id, 0) + 1
        
        results = []
        for catalog_id, count in catalog_counts.items():
            if catalog_id == "uncategorized":
                catalog_name = "未分类"
            else:
                catalog = self.catalog_manager.get_catalog(catalog_id)
                catalog_name = catalog.name if catalog else "未知目录"
            
            results.append({
                "catalog_id": catalog_id,
                "catalog_name": catalog_name,
                "knowledge_count": count
            })
        
        results.sort(key=lambda x: x["knowledge_count"], reverse=True)
        return results
    
    def suggest_catalog_reorganization(
        self,
        max_items_per_catalog: int = 20
    ) -> List[Dict[str, Any]]:
        catalog_distribution = self.analyze_catalog_distribution()
        suggestions = []
        
        for catalog_info in catalog_distribution:
            if catalog_info["knowledge_count"] > max_items_per_catalog:
                suggestions.append({
                    "catalog_id": catalog_info["catalog_id"],
                    "catalog_name": catalog_info["catalog_name"],
                    "current_count": catalog_info["knowledge_count"],
                    "suggested_action": "split",
                    "reason": f"目录下有 {catalog_info['knowledge_count']} 条知识，建议拆分为子目录"
                })
        
        return suggestions
    
    def get_knowledge_space_coordinates(
        self,
        n_components: int = 2
    ) -> Dict[str, Any]:
        ids, embeddings = self.get_all_embeddings()
        
        if len(ids) == 0:
            return {
                "points": [],
                "catalogs": [],
                "statistics": {
                    "total_knowledge": 0,
                    "variance_explained": []
                }
            }
        
        coords_2d = pca_reduce(embeddings, n_components)
        
        all_knowledge = self.knowledge_store.get_all_knowledge()
        knowledge_map = {item.id: item for item in all_knowledge}
        
        catalog_colors = {}
        color_palette = [
            "#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#F44336",
            "#00BCD4", "#795548", "#607D8B", "#E91E63", "#3F51B5",
            "#009688", "#FFC107", "#673AB7", "#03A9F4", "#8BC34A"
        ]
        color_idx = 0
        
        points = []
        for i, kid in enumerate(ids):
            item = knowledge_map.get(kid)
            if not item:
                continue
            
            catalog_id = item.catalog_id or "uncategorized"
            catalog_name = "未分类"
            if catalog_id != "uncategorized":
                catalog = self.catalog_manager.get_catalog(catalog_id)
                catalog_name = catalog.name if catalog else "未知目录"
            
            if catalog_id not in catalog_colors:
                catalog_colors[catalog_id] = {
                    "id": catalog_id,
                    "name": catalog_name,
                    "color": color_palette[color_idx % len(color_palette)]
                }
                color_idx += 1
            
            points.append({
                "id": kid,
                "question": item.question[:50] + "..." if len(item.question) > 50 else item.question,
                "full_question": item.question,
                "catalog_id": catalog_id,
                "catalog_name": catalog_name,
                "color": catalog_colors[catalog_id]["color"],
                "x": float(coords_2d[i, 0]) if coords_2d.shape[1] > 0 else 0.0,
                "y": float(coords_2d[i, 1]) if coords_2d.shape[1] > 1 else 0.0
            })
        
        X_centered = embeddings - np.mean(embeddings, axis=0)
        total_var = np.sum(np.var(X_centered, axis=0))
        
        cov_matrix = np.cov(X_centered.T)
        eigenvalues, _ = np.linalg.eigh(cov_matrix)
        eigenvalues = np.sort(eigenvalues)[::-1]
        
        variance_explained = []
        cumsum = 0
        for i, ev in enumerate(eigenvalues[:n_components]):
            ve = ev / total_var if total_var > 0 else 0
            cumsum += ve
            variance_explained.append({
                "component": i + 1,
                "variance": float(ve),
                "cumulative": float(cumsum)
            })
        
        return {
            "points": points,
            "catalogs": list(catalog_colors.values()),
            "statistics": {
                "total_knowledge": len(points),
                "variance_explained": variance_explained
            }
        }
    
    def get_similarity_heatmap_data(
        self,
        max_items: int = 50,
        cluster_by_catalog: bool = True
    ) -> Dict[str, Any]:
        ids, similarity_matrix = self.compute_similarity_matrix()
        
        if len(ids) == 0:
            return {
                "matrix": [],
                "labels": [],
                "catalogs": []
            }
        
        all_knowledge = self.knowledge_store.get_all_knowledge()
        knowledge_map = {item.id: item for item in all_knowledge}
        
        items_info = []
        for kid in ids:
            item = knowledge_map.get(kid)
            if item:
                items_info.append({
                    "id": kid,
                    "question": item.question[:30] + "..." if len(item.question) > 30 else item.question,
                    "catalog_id": item.catalog_id or "uncategorized",
                    "catalog_name": self._get_catalog_name(item.catalog_id)
                })
        
        if cluster_by_catalog:
            catalog_order = {}
            for info in items_info:
                if info["catalog_id"] not in catalog_order:
                    catalog_order[info["catalog_id"]] = len(catalog_order)
            
            sorted_indices = sorted(
                range(len(items_info)),
                key=lambda i: (catalog_order[items_info[i]["catalog_id"]], items_info[i]["question"])
            )
            
            items_info = [items_info[i] for i in sorted_indices]
            ids = [ids[i] for i in sorted_indices]
            similarity_matrix = similarity_matrix[np.ix_(sorted_indices, sorted_indices)]
        
        if len(ids) > max_items:
            step = len(ids) // max_items
            selected_indices = list(range(0, len(ids), step))[:max_items]
            ids = [ids[i] for i in selected_indices]
            items_info = [items_info[i] for i in selected_indices]
            similarity_matrix = similarity_matrix[np.ix_(selected_indices, selected_indices)]
        
        matrix = []
        for i in range(len(ids)):
            row = []
            for j in range(len(ids)):
                row.append(float(similarity_matrix[i, j]))
            matrix.append(row)
        
        catalogs = []
        seen_catalogs = set()
        for info in items_info:
            if info["catalog_id"] not in seen_catalogs:
                catalogs.append({
                    "id": info["catalog_id"],
                    "name": info["catalog_name"]
                })
                seen_catalogs.add(info["catalog_id"])
        
        return {
            "matrix": matrix,
            "labels": [info["question"] for info in items_info],
            "ids": [info["id"] for info in items_info],
            "catalogs": catalogs,
            "catalog_ids": [info["catalog_id"] for info in items_info]
        }
    
    def get_similarity_network(
        self,
        threshold: float = 0.7,
        max_nodes: int = 100
    ) -> Dict[str, Any]:
        ids, similarity_matrix = self.compute_similarity_matrix()
        
        if len(ids) == 0:
            return {"nodes": [], "edges": []}
        
        all_knowledge = self.knowledge_store.get_all_knowledge()
        knowledge_map = {item.id: item for item in all_knowledge}
        
        degree = np.sum(similarity_matrix >= threshold, axis=1)
        top_indices = np.argsort(degree)[::-1][:max_nodes]
        
        selected_ids = [ids[i] for i in top_indices]
        selected_matrix = similarity_matrix[np.ix_(top_indices, top_indices)]
        
        nodes = []
        for i, kid in enumerate(selected_ids):
            item = knowledge_map.get(kid)
            if not item:
                continue
            
            node_degree = int(np.sum(selected_matrix[i] >= threshold)) - 1
            
            nodes.append({
                "id": kid,
                "label": item.question[:30] + "..." if len(item.question) > 30 else item.question,
                "full_question": item.question,
                "catalog_id": item.catalog_id or "uncategorized",
                "catalog_name": self._get_catalog_name(item.catalog_id),
                "degree": node_degree,
                "size": max(10, min(40, 10 + node_degree * 2))
            })
        
        edges = []
        n = len(selected_ids)
        for i in range(n):
            for j in range(i + 1, n):
                sim = selected_matrix[i, j]
                if sim >= threshold:
                    edges.append({
                        "source": selected_ids[i],
                        "target": selected_ids[j],
                        "weight": float(sim)
                    })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "threshold": threshold
            }
        }
    
    def _get_catalog_name(self, catalog_id: str) -> str:
        if not catalog_id:
            return "未分类"
        catalog = self.catalog_manager.get_catalog(catalog_id)
        return catalog.name if catalog else "未知目录"
    
    def get_knowledge_clusters(
        self,
        n_clusters: int = None
    ) -> Dict[str, Any]:
        ids, embeddings = self.get_all_embeddings()
        
        if len(ids) < 2:
            return {
                "clusters": [],
                "statistics": {"total_knowledge": len(ids)}
            }
        
        if n_clusters is None:
            n_clusters = max(2, min(10, len(ids) // 5))
        
        coords_2d = pca_reduce(embeddings, 2)
        
        n = len(ids)
        k = min(n_clusters, n)
        
        np.random.seed(42)
        centroids = coords_2d[np.random.choice(n, k, replace=False)]
        
        for _ in range(20):
            distances = np.sqrt(
                ((coords_2d[:, np.newaxis, :] - centroids[np.newaxis, :, :]) ** 2).sum(axis=2)
            )
            labels = np.argmin(distances, axis=1)
            
            new_centroids = np.array([
                coords_2d[labels == i].mean(axis=0) if np.sum(labels == i) > 0 else centroids[i]
                for i in range(k)
            ])
            
            if np.allclose(centroids, new_centroids):
                break
            centroids = new_centroids
        
        all_knowledge = self.knowledge_store.get_all_knowledge()
        knowledge_map = {item.id: item for item in all_knowledge}
        
        clusters = []
        for cluster_id in range(k):
            cluster_indices = np.where(labels == cluster_id)[0]
            cluster_points = []
            
            for idx in cluster_indices:
                kid = ids[idx]
                item = knowledge_map.get(kid)
                if item:
                    cluster_points.append({
                        "id": kid,
                        "question": item.question,
                        "catalog_id": item.catalog_id,
                        "catalog_name": self._get_catalog_name(item.catalog_id),
                        "x": float(coords_2d[idx, 0]),
                        "y": float(coords_2d[idx, 1])
                    })
            
            if cluster_points:
                clusters.append({
                    "id": cluster_id,
                    "count": len(cluster_points),
                    "points": cluster_points,
                    "center": {
                        "x": float(centroids[cluster_id, 0]),
                        "y": float(centroids[cluster_id, 1])
                    }
                })
        
        clusters.sort(key=lambda c: c["count"], reverse=True)
        
        return {
            "clusters": clusters,
            "statistics": {
                "total_knowledge": len(ids),
                "n_clusters": len(clusters)
            }
        }
