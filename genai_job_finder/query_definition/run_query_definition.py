import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from .service import ResumeQueryService
from .config import QueryDefinitionConfig, get_openai_config, get_ollama_config


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_config_from_args(args) -> QueryDefinitionConfig:
    """Create configuration from command line arguments."""
    if args.provider == "openai":
        config = get_openai_config()
        if args.model:
            config.llm_model = args.model
    elif args.provider == "ollama":
        config = get_ollama_config()
        if args.model:
            config.llm_model = args.model
        if args.ollama_url:
            config.ollama_base_url = args.ollama_url
    else:
        raise ValueError(f"Unsupported provider: {args.provider}")
    
    if args.temperature is not None:
        config.temperature = args.temperature
    
    return config


def display_results(queries, output_file: Optional[str] = None):
    """Display or save results."""
    output = queries.display_summary()
    
    print(output)
    
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        import json
        with open(output_file, 'w') as f:
            json.dump(queries.to_dict(), f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Generate LinkedIn job search queries from resume analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s resume.pdf
  %(prog)s resume.pdf --provider ollama --model llama3.2
  %(prog)s resume.pdf --output queries.json --verbose
  %(prog)s resume.pdf --provider openai --model gpt-4
        """
    )
    
    # Required arguments
    parser.add_argument(
        "resume_file",
        help="Path to resume file (PDF, DOC, or DOCX)"
    )
    
    # LLM Configuration
    parser.add_argument(
        "--provider",
        choices=["openai", "ollama"],
        default="openai",
        help="LLM provider to use (default: openai)"
    )
    
    parser.add_argument(
        "--model",
        help="LLM model to use (e.g., gpt-3.5-turbo, llama3.2)"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        help="LLM temperature (0.0-1.0, default: 0.1)"
    )
    
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama base URL (default: http://localhost:11434)"
    )
    
    # Output options
    parser.add_argument(
        "--output",
        help="Output file path for results (JSON format)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    # Health check
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Perform health check and exit"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    try:
        # Create configuration
        config = create_config_from_args(args)
        
        # Initialize service
        service = ResumeQueryService(config)
        
        # Health check mode
        if args.health_check:
            print("🔍 Performing health check...")
            if service.health_check():
                print("✅ Service is healthy!")
                return 0
            else:
                print("❌ Service health check failed!")
                return 1
        
        # Validate resume file
        if not Path(args.resume_file).exists():
            print(f"❌ Error: Resume file not found: {args.resume_file}")
            return 1
        
        print(f"🔍 Analyzing resume: {args.resume_file}")
        print(f"🤖 Using {config.llm_provider} with model {config.llm_model}")
        
        # Process resume
        queries = service.process_resume_file(args.resume_file)
        
        # Display results
        display_results(queries, args.output)
        
        print("\n✅ Analysis complete!")
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Analysis interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())