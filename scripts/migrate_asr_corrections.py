"""Database migration script to add ASR-specific columns and migrate ASR corrections."""

import sqlite3
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ASRDatabaseMigrator:
    """Handles database schema updates and ASR correction migrations."""
    
    def __init__(self, db_path: Path, lexicons_dir: Path):
        self.db_path = db_path
        self.lexicons_dir = lexicons_dir
        self.connection: Optional[sqlite3.Connection] = None
        
    def connect(self) -> bool:
        """Connect to the database."""
        try:
            # Create database if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            return True
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def check_schema_version(self) -> int:
        """Check current schema version."""
        if not self.connection:
            return 0
            
        try:
            cursor = self.connection.cursor()
            # Check if version table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_version'
            """)
            
            if not cursor.fetchone():
                return 0  # No version table = version 0
                
            cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            row = cursor.fetchone()
            return row['version'] if row else 0
            
        except sqlite3.Error:
            return 0
    
    def create_initial_schema(self):
        """Create initial database schema if it doesn't exist."""
        if not self.connection:
            raise RuntimeError("Database not connected")
            
        cursor = self.connection.cursor()
        
        # Create version tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
        
        # Create main terms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_term TEXT NOT NULL,
                variations TEXT,  -- JSON array
                transliteration TEXT NOT NULL,
                category TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 1.0,
                context_clues TEXT,  -- JSON array
                is_compound BOOLEAN DEFAULT FALSE,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_original_term ON terms(original_term)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON terms(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_confidence ON terms(confidence)")
        
        self.connection.commit()
        
        # Mark schema as version 1
        cursor.execute("""
            INSERT OR REPLACE INTO schema_version (version, description) 
            VALUES (1, 'Initial schema with basic terms table')
        """)
        self.connection.commit()
        
        logger.info("Initial database schema created")
    
    def migrate_to_asr_schema(self):
        """Add ASR-specific columns to existing schema (Version 2)."""
        if not self.connection:
            raise RuntimeError("Database not connected")
            
        cursor = self.connection.cursor()
        
        # Add ASR-specific columns
        asr_columns = [
            ("asr_common_error", "BOOLEAN DEFAULT FALSE"),
            ("error_type", "TEXT"),
            ("frequency_rating", "TEXT CHECK (frequency_rating IN ('high', 'medium', 'low'))"),
            ("source_authority", "TEXT"),
            ("difficulty_level", "TEXT CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced'))")
        ]
        
        for column_name, column_def in asr_columns:
            try:
                cursor.execute(f"ALTER TABLE terms ADD COLUMN {column_name} {column_def}")
                logger.info(f"Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    logger.info(f"Column {column_name} already exists")
                else:
                    raise
        
        # Create ASR-specific indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_asr_errors 
            ON terms (asr_common_error, frequency_rating) 
            WHERE asr_common_error = TRUE
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_type ON terms(error_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_authority ON terms(source_authority)")
        
        self.connection.commit()
        
        # Update schema version
        cursor.execute("""
            INSERT INTO schema_version (version, description) 
            VALUES (2, 'Added ASR-specific columns and indexes')
        """)
        self.connection.commit()
        
        logger.info("Database migrated to ASR schema (version 2)")
    
    def load_yaml_corrections(self, yaml_file: Path) -> List[Dict]:
        """Load corrections from YAML file."""
        if not yaml_file.exists():
            logger.warning(f"YAML file not found: {yaml_file}")
            return []
            
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            entries = []
            if 'entries' in data:
                entries.extend(data['entries'])
            if 'asr_corrections' in data:
                entries.extend(data['asr_corrections'])
                
            return entries
            
        except Exception as e:
            logger.error(f"Error loading YAML file {yaml_file}: {e}")
            return []
    
    def insert_or_update_term(self, entry: Dict) -> bool:
        """Insert or update a term in the database."""
        if not self.connection:
            return False
            
        try:
            cursor = self.connection.cursor()
            
            # Extract data from entry
            original_term = entry.get('original_term') or entry.get('term', '')
            if not original_term:
                logger.warning("Entry missing original_term/term")
                return False
                
            variations = json.dumps(entry.get('variations', []))
            transliteration = entry.get('transliteration', original_term)
            category = entry.get('category', 'concept')
            confidence = float(entry.get('confidence', 1.0))
            context_clues = json.dumps(entry.get('context_clues', []))
            is_compound = bool(entry.get('is_compound', False))
            
            # ASR-specific fields
            asr_common_error = bool(entry.get('asr_common_error', False))
            error_type = entry.get('error_type')
            frequency_rating = entry.get('frequency', entry.get('frequency_rating'))
            source_authority = entry.get('source_authority', 'YAML_Import')
            difficulty_level = entry.get('difficulty_level', 'beginner')
            
            # Check if term already exists
            cursor.execute("SELECT id FROM terms WHERE LOWER(original_term) = ?", (original_term.lower(),))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing term
                cursor.execute("""
                    UPDATE terms SET 
                        variations = ?, transliteration = ?, category = ?, 
                        confidence = ?, context_clues = ?, is_compound = ?,
                        asr_common_error = ?, error_type = ?, frequency_rating = ?,
                        source_authority = ?, difficulty_level = ?,
                        updated_date = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (variations, transliteration, category, confidence, context_clues, 
                     is_compound, asr_common_error, error_type, frequency_rating,
                     source_authority, difficulty_level, existing['id']))
                
                logger.debug(f"Updated term: {original_term}")
            else:
                # Insert new term
                cursor.execute("""
                    INSERT INTO terms (
                        original_term, variations, transliteration, category, 
                        confidence, context_clues, is_compound,
                        asr_common_error, error_type, frequency_rating,
                        source_authority, difficulty_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (original_term, variations, transliteration, category, confidence, 
                     context_clues, is_compound, asr_common_error, error_type, 
                     frequency_rating, source_authority, difficulty_level))
                
                logger.debug(f"Inserted term: {original_term}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error inserting/updating term {original_term}: {e}")
            return False
    
    def migrate_lexicon_files(self):
        """Migrate all lexicon YAML files to database."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        # Files to migrate
        lexicon_files = [
            'corrections.yaml',
            'proper_nouns.yaml', 
            'asr_corrections.yaml'
        ]
        
        total_migrated = 0
        
        for filename in lexicon_files:
            filepath = self.lexicons_dir / filename
            if not filepath.exists():
                logger.warning(f"Lexicon file not found: {filepath}")
                continue
                
            logger.info(f"Migrating {filename}...")
            entries = self.load_yaml_corrections(filepath)
            
            migrated_count = 0
            for entry in entries:
                if self.insert_or_update_term(entry):
                    migrated_count += 1
            
            self.connection.commit()
            logger.info(f"Migrated {migrated_count} entries from {filename}")
            total_migrated += migrated_count
        
        logger.info(f"Total migrated: {total_migrated} terms")
        return total_migrated
    
    def optimize_database(self):
        """Optimize database performance."""
        if not self.connection:
            return
            
        cursor = self.connection.cursor()
        
        # Update statistics for query optimizer
        cursor.execute("ANALYZE")
        
        # Vacuum to reclaim space and optimize
        cursor.execute("VACUUM")
        
        self.connection.commit()
        logger.info("Database optimized")
    
    def get_migration_stats(self) -> Dict:
        """Get statistics about the migration."""
        if not self.connection:
            return {}
        
        cursor = self.connection.cursor()
        
        stats = {}
        
        # Total terms
        cursor.execute("SELECT COUNT(*) as total FROM terms")
        stats['total_terms'] = cursor.fetchone()['total']
        
        # ASR terms
        cursor.execute("SELECT COUNT(*) as asr_terms FROM terms WHERE asr_common_error = TRUE")
        stats['asr_terms'] = cursor.fetchone()['asr_terms']
        
        # Terms by category
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM terms GROUP BY category ORDER BY count DESC
        """)
        stats['by_category'] = {row['category']: row['count'] for row in cursor.fetchall()}
        
        # ASR error types
        cursor.execute("""
            SELECT error_type, COUNT(*) as count 
            FROM terms WHERE error_type IS NOT NULL 
            GROUP BY error_type ORDER BY count DESC
        """)
        stats['asr_error_types'] = {row['error_type']: row['count'] for row in cursor.fetchall()}
        
        return stats
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

def main():
    """Run database migration."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate ASR corrections to database')
    parser.add_argument('--db-path', type=Path, default='data/sanskrit_terms.db',
                       help='Database file path')
    parser.add_argument('--lexicons-dir', type=Path, default='lexicons',
                       help='Lexicons directory path')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    migrator = ASRDatabaseMigrator(args.db_path, args.lexicons_dir)
    
    try:
        if not migrator.connect():
            print("Failed to connect to database")
            return 1
        
        schema_version = migrator.check_schema_version()
        print(f"Current schema version: {schema_version}")
        
        if schema_version == 0:
            print("Creating initial schema...")
            migrator.create_initial_schema()
        
        if schema_version <= 1:
            print("Migrating to ASR schema...")
            migrator.migrate_to_asr_schema()
        
        print("Migrating lexicon files...")
        total_migrated = migrator.migrate_lexicon_files()
        
        print("Optimizing database...")
        migrator.optimize_database()
        
        print("\nMigration complete!")
        stats = migrator.get_migration_stats()
        print(f"Total terms: {stats['total_terms']}")
        print(f"ASR-specific terms: {stats['asr_terms']}")
        print(f"Categories: {list(stats['by_category'].keys())}")
        if stats['asr_error_types']:
            print(f"ASR error types: {list(stats['asr_error_types'].keys())}")
        
        return 0
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return 1
        
    finally:
        migrator.close()

if __name__ == "__main__":
    exit(main())