"""
Enhanced logging with Rich for beautiful console output.
"""

from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn
)
from rich.panel import Panel
from rich.tree import Tree
from rich.live import Live
from rich.layout import Layout
from rich import box
from datetime import datetime
import time
from typing import Dict, List, Any

console = Console()


class PipelineLogger:
    """Enhanced logger for the document intelligence pipeline"""

    def __init__(self):
        self.start_time = None
        self.step_times = {}
        self.current_step = None

    def print_header(self):
        """Print beautiful header"""
        console.print()
        console.print(
            Panel.fit(
                "[bold cyan]🤖 DOCUMENT INTELLIGENCE PIPELINE[/bold cyan]\n"
                "[dim]Powered by Google Gemini 2.0 + pdfplumber[/dim]",
                border_style="cyan",
                box=box.DOUBLE
            )
        )
        console.print()
        self.start_time = time.time()

    def step(self, step_num: int, title: str, emoji: str = "⚙️"):
        """Start a new step"""
        if self.current_step:
            self.step_times[self.current_step] = time.time() - self.step_start_time

        self.current_step = title
        self.step_start_time = time.time()

        timestamp = datetime.now().strftime("%H:%M:%S")
        console.print(
            f"[bold blue]{timestamp}[/bold blue] "
            f"[bold white]│[/bold white] "
            f"{emoji} [bold cyan]Step {step_num}:[/bold cyan] [bold]{title}[/bold]"
        )

    def success(self, message: str, details: str = None):
        """Print success message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        console.print(
            f"[dim]{timestamp}[/dim] "
            f"[bold white]│[/bold white] "
            f"[bold green]✓[/bold green] {message}"
        )
        if details:
            console.print(f"         [dim]{details}[/dim]")

    def info(self, message: str, indent: int = 1):
        """Print info message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        indent_str = "  " * indent
        console.print(
            f"[dim]{timestamp}[/dim] "
            f"[bold white]│[/bold white] "
            f"{indent_str}[blue]→[/blue] {message}"
        )

    def warning(self, message: str):
        """Print warning message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        console.print(
            f"[dim]{timestamp}[/dim] "
            f"[bold white]│[/bold white] "
            f"[bold yellow]⚠[/bold yellow]  {message}"
        )

    def error(self, message: str):
        """Print error message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        console.print(
            f"[dim]{timestamp}[/dim] "
            f"[bold white]│[/bold white] "
            f"[bold red]✗[/bold red] {message}"
        )

    def progress_bar(self, description: str, total: int):
        """Create a progress bar"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="cyan", finished_style="green"),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console
        )

    def classification_result(self, filename: str, doc_type: str, confidence: float, duration: float):
        """Display classification result"""
        confidence_color = "green" if confidence > 0.8 else "yellow" if confidence > 0.6 else "red"
        console.print(
            f"         [dim]→[/dim] [cyan]{filename}[/cyan] "
            f"[bold white]→[/bold white] "
            f"[bold magenta]{doc_type.upper()}[/bold magenta] "
            f"[dim]([{confidence_color}]{confidence:.1%}[/{confidence_color}])[/dim] "
            f"[dim]in {duration:.1f}s[/dim]"
        )

    def extraction_result(self, filename: str, num_fields: int, duration: float):
        """Display extraction result"""
        console.print(
            f"         [dim]→[/dim] [cyan]{filename}[/cyan] "
            f"[bold white]→[/bold white] "
            f"[green]{num_fields} fields[/green] "
            f"[dim]in {duration:.1f}s[/dim]"
        )

    def print_summary_table(self, documents: List[Any]):
        """Print beautiful summary table"""
        table = Table(
            title="📊 Processing Summary",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )

        table.add_column("File", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Confidence", justify="right")
        table.add_column("Key Info", style="dim")

        for doc in documents:
            doc_dict = doc.dict() if hasattr(doc, 'dict') else doc

            # Get confidence with color
            confidence = doc_dict.get('confidence_score', 0)
            confidence_color = "green" if confidence > 0.8 else "yellow" if confidence > 0.6 else "red"
            confidence_str = f"[{confidence_color}]{confidence:.1%}[/{confidence_color}]"

            # Get type-specific key info
            doc_type = doc_dict.get('document_type', 'unknown')
            key_info = ""

            if doc_type == 'invoice':
                client = doc_dict.get('client_name', 'N/A')
                amount = doc_dict.get('total_amount', 0)
                key_info = f"{client} - ${amount:.2f}" if amount else client
            elif doc_type == 'contract':
                parties = doc_dict.get('parties', [])
                key_info = ', '.join(parties[:2]) if parties else 'N/A'
            elif doc_type == 'email':
                sender = doc_dict.get('sender', 'N/A')
                key_info = sender

            table.add_row(
                doc_dict.get('file_name', 'unknown'),
                doc_type.upper(),
                confidence_str,
                key_info
            )

        console.print()
        console.print(table)
        console.print()

    def print_extracted_data(self, documents: List[Any]):
        """Print extracted data in beautiful format"""
        console.print()
        console.print("[bold cyan]📄 Extracted Data Details[/bold cyan]")
        console.print()

        for i, doc in enumerate(documents, 1):
            doc_dict = doc.dict() if hasattr(doc, 'dict') else doc

            # Create a tree for each document
            tree = Tree(
                f"[bold cyan]{doc_dict.get('file_name', 'Unknown')}[/bold cyan] "
                f"[dim]({doc_dict.get('document_type', 'unknown').upper()})[/dim]"
            )

            # Add fields based on document type
            doc_type = doc_dict.get('document_type')

            if doc_type == 'invoice':
                tree.add(f"[yellow]Invoice #:[/yellow] {doc_dict.get('invoice_number', 'N/A')}")
                tree.add(f"[yellow]Date:[/yellow] {doc_dict.get('invoice_date', 'N/A')}")
                tree.add(f"[yellow]Client:[/yellow] {doc_dict.get('client_name', 'N/A')}")
                tree.add(f"[yellow]Vendor:[/yellow] {doc_dict.get('vendor_name', 'N/A')}")
                amount = doc_dict.get('total_amount', 0) or 0
                tree.add(f"[yellow]Amount:[/yellow] ${amount:.2f} {doc_dict.get('currency', '')}")
                parties = doc_dict.get('involved_parties', [])
                if parties:
                    parties_node = tree.add("[yellow]Parties:[/yellow]")
                    for party in parties:
                        parties_node.add(f"[dim]• {party}[/dim]")

            elif doc_type == 'contract':
                tree.add(f"[yellow]Contract ID:[/yellow] {doc_dict.get('contract_id', 'N/A')}")
                tree.add(f"[yellow]Date:[/yellow] {doc_dict.get('contract_date', 'N/A')}")
                parties = doc_dict.get('parties', [])
                if parties:
                    parties_node = tree.add("[yellow]Parties:[/yellow]")
                    for party in parties:
                        parties_node.add(f"[dim]• {party}[/dim]")
                tree.add(f"[yellow]Value:[/yellow] ${doc_dict.get('contract_value', 0):.2f}")

            elif doc_type == 'email':
                tree.add(f"[yellow]From:[/yellow] {doc_dict.get('sender', 'N/A')}")
                recipients = doc_dict.get('recipients', [])
                tree.add(f"[yellow]To:[/yellow] {', '.join(recipients) if recipients else 'N/A'}")
                tree.add(f"[yellow]Date:[/yellow] {doc_dict.get('email_date', 'N/A')}")
                tree.add(f"[yellow]Subject:[/yellow] {doc_dict.get('subject', 'N/A')}")

            console.print(tree)
            console.print()

    def print_analytics(self, documents: List[Any]):
        """Print analytics summary"""
        doc_list = [doc.dict() if hasattr(doc, 'dict') else doc for doc in documents]

        # Calculate statistics
        total_docs = len(doc_list)
        avg_confidence = sum(d.get('confidence_score', 0) for d in doc_list) / total_docs if total_docs > 0 else 0

        # Count by type
        type_counts = {}
        for doc in doc_list:
            doc_type = doc.get('document_type', 'unknown')
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

        # Financial summary
        total_invoice_amount = sum(
            doc.get('total_amount', 0)
            for doc in doc_list
            if doc.get('document_type') == 'invoice' and doc.get('total_amount')
        )

        # Create analytics table
        table = Table(
            title="📈 Analytics Summary",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )

        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="bold white")

        table.add_row("Total Documents", str(total_docs))
        table.add_row("Average Confidence", f"{avg_confidence:.1%}")

        for doc_type, count in type_counts.items():
            table.add_row(f"{doc_type.title()}s", str(count))

        if total_invoice_amount > 0:
            table.add_row("Total Invoice Amount", f"${total_invoice_amount:.2f}")

        console.print()
        console.print(table)
        console.print()

    def print_footer(self):
        """Print beautiful footer with timing"""
        total_time = time.time() - self.start_time

        console.print()
        console.print("─" * 80)

        # Create timing breakdown
        timing_table = Table(
            title="⏱️  Performance Metrics",
            box=box.SIMPLE,
            show_header=True,
            header_style="bold cyan"
        )

        timing_table.add_column("Operation", style="cyan")
        timing_table.add_column("Duration", justify="right", style="bold white")
        timing_table.add_column("% of Total", justify="right", style="dim")

        for step, duration in self.step_times.items():
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            timing_table.add_row(
                step,
                f"{duration:.2f}s",
                f"{percentage:.1f}%"
            )

        timing_table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]{total_time:.2f}s[/bold]",
            "[bold]100%[/bold]"
        )

        console.print(timing_table)
        console.print()

        console.print(
            Panel.fit(
                "[bold green]✅ PIPELINE COMPLETED SUCCESSFULLY![/bold green]\n"
                f"[dim]Processed in {total_time:.2f} seconds[/dim]",
                border_style="green",
                box=box.DOUBLE
            )
        )
        console.print()


# Global logger instance
logger = PipelineLogger()
