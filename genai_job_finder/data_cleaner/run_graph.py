#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys
from pathlib import Path

from .graph import JobCleaningGraph
from .config import CleanerConfig


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data_cleaner_graph.log')
        ]
    )
    
    # Disable HTTP logs from httpx/httpcore to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Clean and enhance job data using LangGraph workflow"
    )
    
    parser.add_argument(
        "--db-path",
        type=str,
        default="data/jobs.db",
        help="Path to SQLite database file (default: data/jobs.db)"
    )
    
    parser.add_argument(
        "--source-table",
        type=str,
        default="jobs",
        help="Source table name (default: jobs)"
    )
    
    parser.add_argument(
        "--target-table",
        type=str,
        default="cleaned_jobs",
        help="Target table name (default: cleaned_jobs)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="llama3.2",
        help="Ollama model to use (default: llama3.2)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--ollama-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama server URL (default: http://localhost:11434)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Validate database path
    db_path = Path(args.db_path)
    if not db_path.exists():
        logger.error(f"Database file does not exist: {db_path}")
        sys.exit(1)
    
    # Create configuration
    config = CleanerConfig(
        ollama_model=args.model,
        ollama_base_url=args.ollama_url
    )
    
    logger.info(f"Starting job data cleaning with LangGraph...")
    logger.info(f"Database: {db_path}")
    logger.info(f"Source table: {args.source_table}")
    logger.info(f"Target table: {args.target_table}")
    logger.info(f"Model: {config.ollama_model}")
    
    try:
        # Initialize graph and process data
        graph = JobCleaningGraph(config)
        
        # Generate workflow diagram
        logger.info("Generating workflow diagram...")
        diagram_path = graph.save_workflow_diagram("job_cleaning_workflow.png")
        
        await graph.process_database_table(
            str(db_path), 
            args.source_table, 
            args.target_table
        )
        
        logger.info("Data cleaning completed successfully!")
        if diagram_path:
            logger.info(f"Workflow diagram saved: {diagram_path}")
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
