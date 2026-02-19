"""Cost report generation service.

Requirements:
- 16.1: Generate monthly reports by team, project, cost center
- 16.2: Include total costs, breakdown by bundle type, storage, data transfer
- 16.3: Support CSV and PDF export formats
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import csv
import io

logger = logging.getLogger(__name__)


class CostReportGenerator:
    """
    Generates cost reports in various formats.
    
    Validates:
    - Requirements 16.1: Monthly reports by team, project, cost center
    - Requirements 16.2: Cost breakdown by bundle type, storage, data transfer
    - Requirements 16.3: CSV and PDF export formats
    """
    
    def __init__(self):
        """Initialize cost report generator."""
        logger.info("cost_report_generator_initialized")
    
    def generate_monthly_report(
        self,
        start_date: datetime,
        end_date: datetime,
        cost_records: List[Any],
        group_by: str = "team"
    ) -> Dict[str, Any]:
        """Generate monthly cost report.
        
        Validates: Requirements 16.1, 16.2
        
        Args:
            start_date: Report start date
            end_date: Report end date
            cost_records: List of cost record objects
            group_by: Grouping dimension (team, project, cost_center, user)
            
        Returns:
            Report data dictionary
        """
        # Calculate totals
        total_compute = sum(r.compute_cost for r in cost_records)
        total_storage = sum(r.storage_cost for r in cost_records)
        total_transfer = sum(r.data_transfer_cost for r in cost_records)
        total_cost = sum(r.total_cost for r in cost_records)
        
        # Group by dimension
        grouped_costs = self._group_costs(cost_records, group_by)
        
        # Breakdown by bundle type
        bundle_breakdown = self._breakdown_by_bundle(cost_records)
        
        report = {
            "report_id": f"report-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "report_type": "monthly_cost_report",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_cost": round(total_cost, 2),
                "compute_cost": round(total_compute, 2),
                "storage_cost": round(total_storage, 2),
                "data_transfer_cost": round(total_transfer, 2),
                "record_count": len(cost_records)
            },
            "grouped_by": group_by,
            "groups": grouped_costs,
            "bundle_breakdown": bundle_breakdown
        }
        
        logger.info(
            f"monthly_report_generated period={start_date.date()}_to_{end_date.date()} "
            f"total_cost=${total_cost:.2f} records={len(cost_records)}"
        )
        
        return report
    
    def _group_costs(
        self,
        cost_records: List[Any],
        group_by: str
    ) -> List[Dict[str, Any]]:
        """Group costs by specified dimension.
        
        Validates: Requirements 16.4, 16.5
        
        Args:
            cost_records: List of cost records
            group_by: Grouping dimension
            
        Returns:
            List of grouped cost summaries
        """
        groups: Dict[str, Dict[str, Any]] = {}
        
        for record in cost_records:
            # Get group key based on dimension
            if group_by == "team":
                key = record.team_id
            elif group_by == "project":
                # Use project tag for grouping (Requirement 16.5)
                key = record.tags.get("project", "untagged") if record.tags else "untagged"
            elif group_by == "cost_center":
                # Use cost_center tag for grouping (Requirement 16.5)
                key = record.tags.get("cost_center", "untagged") if record.tags else "untagged"
            elif group_by == "user":
                key = record.user_id
            else:
                key = "unknown"
            
            # Initialize group if not exists
            if key not in groups:
                groups[key] = {
                    "compute_cost": 0.0,
                    "storage_cost": 0.0,
                    "data_transfer_cost": 0.0,
                    "total_cost": 0.0,
                    "workspace_count": 0,
                    "tags": {}  # Collect unique tags
                }
            
            # Accumulate costs
            groups[key]["compute_cost"] += record.compute_cost
            groups[key]["storage_cost"] += record.storage_cost
            groups[key]["data_transfer_cost"] += record.data_transfer_cost
            groups[key]["total_cost"] += record.total_cost
            groups[key]["workspace_count"] += 1
            
            # Collect tags (Requirement 16.5)
            if record.tags:
                for tag_key, tag_value in record.tags.items():
                    if tag_key not in groups[key]["tags"]:
                        groups[key]["tags"][tag_key] = set()
                    groups[key]["tags"][tag_key].add(str(tag_value))
        
        # Convert to list format
        result = []
        for group_id, costs in groups.items():
            # Convert tag sets to lists for JSON serialization
            tags_dict = {k: list(v) for k, v in costs["tags"].items()}
            
            result.append({
                f"{group_by}_id": group_id,
                "compute_cost": round(costs["compute_cost"], 2),
                "storage_cost": round(costs["storage_cost"], 2),
                "data_transfer_cost": round(costs["data_transfer_cost"], 2),
                "total_cost": round(costs["total_cost"], 2),
                "workspace_count": costs["workspace_count"],
                "tags": tags_dict
            })
        
        # Sort by total cost descending
        result.sort(key=lambda x: x["total_cost"], reverse=True)
        
        return result
    
    def _breakdown_by_bundle(
        self,
        cost_records: List[Any]
    ) -> List[Dict[str, Any]]:
        """Break down costs by bundle type.
        
        Validates: Requirements 16.2
        
        Args:
            cost_records: List of cost records
            
        Returns:
            List of bundle type cost summaries
        """
        bundles: Dict[str, Dict[str, float]] = {}
        
        for record in cost_records:
            bundle = record.bundle_type
            
            if bundle not in bundles:
                bundles[bundle] = {
                    "compute_cost": 0.0,
                    "storage_cost": 0.0,
                    "data_transfer_cost": 0.0,
                    "total_cost": 0.0,
                    "workspace_count": 0
                }
            
            bundles[bundle]["compute_cost"] += record.compute_cost
            bundles[bundle]["storage_cost"] += record.storage_cost
            bundles[bundle]["data_transfer_cost"] += record.data_transfer_cost
            bundles[bundle]["total_cost"] += record.total_cost
            bundles[bundle]["workspace_count"] += 1
        
        # Convert to list format
        result = []
        for bundle_type, costs in bundles.items():
            result.append({
                "bundle_type": bundle_type,
                "compute_cost": round(costs["compute_cost"], 2),
                "storage_cost": round(costs["storage_cost"], 2),
                "data_transfer_cost": round(costs["data_transfer_cost"], 2),
                "total_cost": round(costs["total_cost"], 2),
                "workspace_count": costs["workspace_count"]
            })
        
        # Sort by total cost descending
        result.sort(key=lambda x: x["total_cost"], reverse=True)
        
        return result
    
    def export_to_csv(self, report_data: Dict[str, Any]) -> str:
        """Export report to CSV format.
        
        Validates: Requirements 16.3
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        
        # Write summary section
        output.write("# Cost Report Summary\n")
        output.write(f"Report ID,{report_data['report_id']}\n")
        output.write(f"Period Start,{report_data['period']['start']}\n")
        output.write(f"Period End,{report_data['period']['end']}\n")
        output.write(f"Generated At,{report_data['generated_at']}\n")
        output.write("\n")
        
        output.write("# Total Costs\n")
        summary = report_data['summary']
        output.write(f"Total Cost,${summary['total_cost']:.2f}\n")
        output.write(f"Compute Cost,${summary['compute_cost']:.2f}\n")
        output.write(f"Storage Cost,${summary['storage_cost']:.2f}\n")
        output.write(f"Data Transfer Cost,${summary['data_transfer_cost']:.2f}\n")
        output.write(f"Record Count,{summary['record_count']}\n")
        output.write("\n")
        
        # Write grouped costs
        output.write(f"# Costs by {report_data['grouped_by'].title()}\n")
        if report_data['groups']:
            # Get headers from first group
            headers = list(report_data['groups'][0].keys())
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            writer.writerows(report_data['groups'])
        output.write("\n")
        
        # Write bundle breakdown
        output.write("# Costs by Bundle Type\n")
        if report_data['bundle_breakdown']:
            headers = list(report_data['bundle_breakdown'][0].keys())
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            writer.writerows(report_data['bundle_breakdown'])
        
        csv_content = output.getvalue()
        output.close()
        
        logger.info(
            f"report_exported_to_csv report_id={report_data['report_id']} "
            f"size={len(csv_content)} bytes"
        )
        
        return csv_content
    
    def export_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        """Export report to PDF format.
        
        Validates: Requirements 16.3
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            PDF bytes
            
        Note:
            This is a placeholder. Full PDF generation would require
            a library like ReportLab or WeasyPrint.
        """
        # TODO: Implement actual PDF generation
        # Would use ReportLab or similar library to create formatted PDF
        
        logger.warning(
            f"pdf_export_not_implemented report_id={report_data['report_id']} "
            "returning placeholder"
        )
        
        # Return placeholder PDF content
        pdf_content = b"%PDF-1.4\n% Placeholder PDF\n"
        pdf_content += f"% Report ID: {report_data['report_id']}\n".encode()
        pdf_content += f"% Total Cost: ${report_data['summary']['total_cost']:.2f}\n".encode()
        pdf_content += b"%%EOF\n"
        
        return pdf_content
    
    def generate_and_export(
        self,
        start_date: datetime,
        end_date: datetime,
        cost_records: List[Any],
        group_by: str = "team",
        export_format: str = "json"
    ) -> tuple[Dict[str, Any], Optional[str], Optional[bytes]]:
        """Generate report and export to specified format.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            cost_records: List of cost records
            group_by: Grouping dimension
            export_format: Export format (json, csv, pdf)
            
        Returns:
            Tuple of (report_data, csv_content, pdf_content)
        """
        # Generate report
        report_data = self.generate_monthly_report(
            start_date=start_date,
            end_date=end_date,
            cost_records=cost_records,
            group_by=group_by
        )
        
        csv_content = None
        pdf_content = None
        
        # Export to requested format
        if export_format == "csv":
            csv_content = self.export_to_csv(report_data)
        elif export_format == "pdf":
            pdf_content = self.export_to_pdf(report_data)
        
        return report_data, csv_content, pdf_content
