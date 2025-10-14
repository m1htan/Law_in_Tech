#!/usr/bin/env python3
"""
Main script to run the Metadata Discovery Agent

Usage:
    python run_metadata_discovery.py
    
Or with custom keywords:
    python run_metadata_discovery.py --keywords "AI" "blockchain" "dữ liệu cá nhân"
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.metadata_agent import MetadataDiscoveryAgent
from src.config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.logs_dir / 'metadata_discovery.log')
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main function"""
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Metadata Discovery Agent for Legal Documents')
    parser.add_argument(
        '--keywords',
        nargs='+',
        help='Keywords to search for (e.g., "AI" "blockchain")',
        default=None
    )
    parser.add_argument(
        '--max-documents',
        type=int,
        default=50,
        help='Maximum number of documents to process (default: 50)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help='Google API key (optional, uses .env if not provided)',
        default=None
    )
    
    args = parser.parse_args()
    
    # Create logs directory
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Check API key
        api_key = args.api_key or config.google_api_key
        if not api_key or api_key == "your_google_api_key_here":
            logger.error("=" * 60)
            logger.error("ERROR: Google API key not configured!")
            logger.error("Please set GOOGLE_API_KEY in .env file")
            logger.error("Or provide it with --api-key argument")
            logger.error("=" * 60)
            return 1
        
        # Initialize agent
        logger.info("Initializing Metadata Discovery Agent...")
        agent = MetadataDiscoveryAgent(google_api_key=api_key)
        
        # Prepare keywords
        keywords = args.keywords
        if keywords:
            logger.info(f"Using custom keywords: {keywords}")
        else:
            keywords = config.get_all_keywords()[:15]  # Use top 15 default keywords
            logger.info(f"Using default keywords: {keywords[:5]}... (total: {len(keywords)})")
        
        # Run agent
        logger.info(f"Starting discovery with max {args.max_documents} documents...")
        result = agent.run(
            keywords=keywords,
            max_documents=args.max_documents
        )
        
        # Print results
        print("\n" + "=" * 60)
        print("METADATA DISCOVERY RESULTS")
        print("=" * 60)
        
        if result["success"]:
            print(f"✓ Success!")
            print(f"  - Total discovered: {result['total_discovered']}")
            print(f"  - Total relevant: {result['total_relevant']}")
            print(f"  - Saved to: {result['metadata_path']}")
            
            if result.get('error'):
                print(f"\n⚠ Warning: {result['error']}")
        else:
            print(f"✗ Failed!")
            print(f"  Error: {result['error']}")
            return 1
        
        print("=" * 60)
        print("\nNext steps:")
        print("1. Review the metadata files in: data/metadata/")
        print("2. Check the logs in: logs/metadata_discovery.log")
        print("3. Proceed to the next pipeline step (PDF crawling)")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.exception("Fatal error running agent")
        print(f"\n✗ Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
