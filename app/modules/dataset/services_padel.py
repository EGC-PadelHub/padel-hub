"""
Service for calculating and managing padel-specific dataset metrics.
"""
import csv
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.modules.dataset.models import PadelDatasetMetrics, DataSet
from app import db

logger = logging.getLogger(__name__)


class PadelMetricsService:
    """Service for calculating statistics from padel match CSV files."""

    @staticmethod
    def calculate_metrics_from_csv(csv_path: str) -> Dict[str, Any]:
        """
        Analyze a padel CSV file and extract statistics.
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            Dictionary with calculated metrics
        """
        metrics = {
            "total_matches": 0,
            "tournaments": set(),
            "players": set(),
            "categories": set(),
            "dates": [],
            "has_set3": False,
            "total_sets": 0
        }

        try:
            # Try different encodings
            encodings = ["utf-8", "utf-8-sig", "utf-16", "latin-1", "cp1252"]
            file_content = None
            
            for enc in encodings:
                try:
                    with open(csv_path, "r", encoding=enc, newline="") as f:
                        file_content = f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if not file_content:
                logger.warning(f"Could not decode CSV file: {csv_path}")
                return metrics

            # Parse CSV
            from io import StringIO
            reader = csv.DictReader(StringIO(file_content))
            
            for row in reader:
                metrics["total_matches"] += 1
                
                # Collect tournament names
                if row.get("nombre_torneo"):
                    metrics["tournaments"].add(row["nombre_torneo"])
                
                # Collect player names
                for player_field in [
                    "pareja1_jugador1", "pareja1_jugador2",
                    "pareja2_jugador1", "pareja2_jugador2"
                ]:
                    if row.get(player_field):
                        metrics["players"].add(row[player_field])
                
                # Collect categories
                if row.get("categoria"):
                    metrics["categories"].add(row["categoria"])
                
                # Parse dates
                if row.get("fecha_inicio_torneo"):
                    try:
                        date_str = row["fecha_inicio_torneo"]
                        # Parse DD.MM.YYYY format
                        date_obj = datetime.strptime(date_str, "%d.%m.%Y")
                        metrics["dates"].append(date_obj)
                    except ValueError:
                        pass
                
                # Check for third set
                if row.get("set3_pareja1") or row.get("set3_pareja2"):
                    metrics["has_set3"] = True
                    metrics["total_sets"] += 3
                else:
                    metrics["total_sets"] += 2

        except Exception as e:
            logger.exception(f"Error calculating metrics from CSV: {e}")

        return metrics

    @staticmethod
    def create_or_update_metrics(dataset: DataSet, csv_path: str) -> Optional[PadelDatasetMetrics]:
        """
        Calculate and save padel metrics for a dataset.
        
        Args:
            dataset: The DataSet object
            csv_path: Path to the CSV file
            
        Returns:
            PadelDatasetMetrics object or None if error
        """
        try:
            metrics = PadelMetricsService.calculate_metrics_from_csv(csv_path)
            
            # Get or create metrics record
            padel_metrics = PadelDatasetMetrics.query.filter_by(dataset_id=dataset.id).first()
            if not padel_metrics:
                padel_metrics = PadelDatasetMetrics(dataset_id=dataset.id)
            
            # Update fields
            padel_metrics.total_matches = metrics["total_matches"]
            padel_metrics.total_tournaments = len(metrics["tournaments"])
            padel_metrics.unique_players = len(metrics["players"])
            
            # Date range
            if metrics["dates"]:
                padel_metrics.date_range_start = min(metrics["dates"]).date()
                padel_metrics.date_range_end = max(metrics["dates"]).date()
            
            # Categories as JSON
            padel_metrics.categories = json.dumps(list(metrics["categories"]))
            
            # Tournament names as JSON
            padel_metrics.tournament_names = json.dumps(list(metrics["tournaments"]))
            
            # Set 3 stats
            padel_metrics.has_set3_matches = metrics["has_set3"]
            if metrics["total_matches"] > 0:
                padel_metrics.avg_sets_per_match = metrics["total_sets"] / metrics["total_matches"]
            
            db.session.add(padel_metrics)
            db.session.commit()
            
            return padel_metrics
            
        except Exception as e:
            logger.exception(f"Error creating/updating padel metrics: {e}")
            db.session.rollback()
            return None

    @staticmethod
    def get_metrics(dataset_id: int) -> Optional[PadelDatasetMetrics]:
        """
        Get padel metrics for a dataset.
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            PadelDatasetMetrics object or None
        """
        return PadelDatasetMetrics.query.filter_by(dataset_id=dataset_id).first()

    @staticmethod
    def get_all_metrics() -> List[PadelDatasetMetrics]:
        """Get all padel dataset metrics."""
        return PadelDatasetMetrics.query.all()
