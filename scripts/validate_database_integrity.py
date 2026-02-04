#!/usr/bin/env python3
"""
Database Integrity Validation Script
Validates foreign keys, relationships, and referential integrity
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import re

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    from sqlalchemy import create_engine, inspect, MetaData, Table
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.exc import OperationalError
except ImportError:
    print("❌ SQLAlchemy bulunamadı. Lütfen yükleyin: pip install sqlalchemy")
    sys.exit(1)


class DatabaseIntegrityValidator:
    def __init__(self, database_url: str = None):
        """
        Database integrity validator
        
        Args:
            database_url: PostgreSQL connection string
        """
        if database_url is None:
            # Default to local development database
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:postgres@localhost:5432/turkiye_sinav"
            )
        
        self.database_url = database_url
        self.engine = None
        self.inspector = None
        self.metadata = None
        self.results = {
            "foreign_keys": [],
            "orphaned_records": [],
            "missing_indexes": [],
            "cascade_rules": [],
            "relationship_issues": []
        }
    
    def connect(self) -> bool:
        """Veritabanına bağlan"""
        try:
            print(f"🔌 Veritabanına bağlanılıyor...")
            self.engine = create_engine(self.database_url)
            self.inspector = inspect(self.engine)
            self.metadata = MetaData()
            self.metadata.reflect(bind=self.engine)
            print(f"✅ Bağlantı başarılı")
            return True
        except OperationalError as e:
            print(f"❌ Veritabanı bağlantı hatası: {e}")
            print(f"⚠️  Veritabanı çalışmıyor olabilir veya connection string yanlış")
            return False
        except Exception as e:
            print(f"❌ Beklenmeyen hata: {e}")
            return False
    
    def validate_foreign_keys(self):
        """Tüm foreign key constraint'lerini doğrula"""
        print("\n🔍 Foreign key constraint'leri kontrol ediliyor...")
        
        tables = self.inspector.get_table_names()
        total_fks = 0
        valid_fks = 0
        invalid_fks = 0
        
        for table_name in tables:
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            
            for fk in foreign_keys:
                total_fks += 1
                fk_name = fk.get('name', 'unnamed')
                constrained_columns = fk.get('constrained_columns', [])
                referred_table = fk.get('referred_table')
                referred_columns = fk.get('referred_columns', [])
                
                # Foreign key'in geçerli olup olmadığını kontrol et
                if referred_table in tables:
                    valid_fks += 1
                    self.results['foreign_keys'].append({
                        "table": table_name,
                        "fk_name": fk_name,
                        "columns": constrained_columns,
                        "referred_table": referred_table,
                        "referred_columns": referred_columns,
                        "status": "✅ Valid"
                    })
                else:
                    invalid_fks += 1
                    self.results['foreign_keys'].append({
                        "table": table_name,
                        "fk_name": fk_name,
                        "columns": constrained_columns,
                        "referred_table": referred_table,
                        "referred_columns": referred_columns,
                        "status": "❌ Invalid - Referred table not found"
                    })
        
        print(f"✅ {valid_fks}/{total_fks} foreign key geçerli")
        if invalid_fks > 0:
            print(f"❌ {invalid_fks} geçersiz foreign key bulundu")
        
        return total_fks, valid_fks, invalid_fks
    
    def check_orphaned_records(self):
        """Yetim kayıtları (orphaned records) kontrol et"""
        print("\n🔍 Yetim kayıtlar kontrol ediliyor...")
        
        if not self.engine:
            print("⚠️  Veritabanı bağlantısı yok, yetim kayıt kontrolü atlanıyor")
            return 0
        
        tables = self.inspector.get_table_names()
        total_orphans = 0
        
        for table_name in tables:
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            
            for fk in foreign_keys:
                constrained_columns = fk.get('constrained_columns', [])
                referred_table = fk.get('referred_table')
                referred_columns = fk.get('referred_columns', [])
                
                if not constrained_columns or not referred_columns:
                    continue
                
                # SQL query to find orphaned records
                query = f"""
                    SELECT COUNT(*) as orphan_count
                    FROM {table_name} t
                    WHERE t.{constrained_columns[0]} IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1 FROM {referred_table} r
                        WHERE r.{referred_columns[0]} = t.{constrained_columns[0]}
                    )
                """
                
                try:
                    with self.engine.connect() as conn:
                        result = conn.execute(query)
                        row = result.fetchone()
                        orphan_count = row[0] if row else 0
                        
                        if orphan_count > 0:
                            total_orphans += orphan_count
                            self.results['orphaned_records'].append({
                                "table": table_name,
                                "column": constrained_columns[0],
                                "referred_table": referred_table,
                                "referred_column": referred_columns[0],
                                "orphan_count": orphan_count,
                                "status": "❌ Orphaned records found"
                            })
                except Exception as e:
                    print(f"⚠️  {table_name} tablosunda yetim kayıt kontrolü başarısız: {e}")
        
        if total_orphans > 0:
            print(f"❌ {total_orphans} yetim kayıt bulundu")
        else:
            print(f"✅ Yetim kayıt bulunamadı")
        
        return total_orphans
    
    def check_cascade_rules(self):
        """Cascade delete/update kurallarını kontrol et"""
        print("\n🔍 Cascade kuralları kontrol ediliyor...")
        
        tables = self.inspector.get_table_names()
        total_cascades = 0
        
        for table_name in tables:
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            
            for fk in foreign_keys:
                fk_name = fk.get('name', 'unnamed')
                on_delete = fk.get('ondelete', 'NO ACTION')
                on_update = fk.get('onupdate', 'NO ACTION')
                
                self.results['cascade_rules'].append({
                    "table": table_name,
                    "fk_name": fk_name,
                    "on_delete": on_delete,
                    "on_update": on_update,
                    "status": "✅ Configured"
                })
                
                total_cascades += 1
        
        print(f"✅ {total_cascades} cascade rule kontrol edildi")
        return total_cascades
    
    def check_missing_indexes(self):
        """Eksik index'leri tespit et (foreign key column'ları için)"""
        print("\n🔍 Eksik index'ler kontrol ediliyor...")
        
        tables = self.inspector.get_table_names()
        missing_indexes = 0
        
        for table_name in tables:
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            indexes = self.inspector.get_indexes(table_name)
            
            # Index'lenmiş column'ları topla
            indexed_columns = set()
            for idx in indexes:
                for col in idx.get('column_names', []):
                    indexed_columns.add(col)
            
            # Foreign key column'larını kontrol et
            for fk in foreign_keys:
                constrained_columns = fk.get('constrained_columns', [])
                
                for col in constrained_columns:
                    if col not in indexed_columns:
                        missing_indexes += 1
                        self.results['missing_indexes'].append({
                            "table": table_name,
                            "column": col,
                            "fk_name": fk.get('name', 'unnamed'),
                            "status": "⚠️  Missing index",
                            "recommendation": f"CREATE INDEX idx_{table_name}_{col} ON {table_name}({col});"
                        })
        
        if missing_indexes > 0:
            print(f"⚠️  {missing_indexes} foreign key column'unda index eksik")
        else:
            print(f"✅ Tüm foreign key column'ları index'li")
        
        return missing_indexes
    
    def analyze_relationships(self):
        """Tablo ilişkilerini analiz et"""
        print("\n🔍 Tablo ilişkileri analiz ediliyor...")
        
        tables = self.inspector.get_table_names()
        relationships = defaultdict(list)
        
        for table_name in tables:
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            
            for fk in foreign_keys:
                referred_table = fk.get('referred_table')
                relationships[table_name].append(referred_table)
        
        # İlişki grafiğini oluştur
        print(f"✅ {len(relationships)} tablo ilişkisi bulundu")
        
        # Circular dependency kontrolü
        circular_deps = self._find_circular_dependencies(relationships)
        if circular_deps:
            print(f"⚠️  {len(circular_deps)} circular dependency bulundu")
            for cycle in circular_deps:
                self.results['relationship_issues'].append({
                    "type": "circular_dependency",
                    "tables": cycle,
                    "status": "⚠️  Circular dependency",
                    "recommendation": "Consider breaking the cycle or using deferred constraints"
                })
        
        return len(relationships)
    
    def _find_circular_dependencies(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Circular dependency'leri bul (DFS ile)"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Cycle bulundu
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def generate_report(self, output_file: str = "database_integrity_report.json"):
        """Detaylı rapor oluştur"""
        print(f"\n📊 Rapor oluşturuluyor: {output_file}")
        
        report = {
            "summary": {
                "total_foreign_keys": len(self.results['foreign_keys']),
                "valid_foreign_keys": len([fk for fk in self.results['foreign_keys'] if '✅' in fk['status']]),
                "orphaned_records": sum(r.get('orphan_count', 0) for r in self.results['orphaned_records']),
                "missing_indexes": len(self.results['missing_indexes']),
                "cascade_rules": len(self.results['cascade_rules']),
                "relationship_issues": len(self.results['relationship_issues'])
            },
            "details": self.results,
            "health_score": self._calculate_health_score()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Rapor kaydedildi: {output_file}")
        return report
    
    def _calculate_health_score(self) -> float:
        """Sağlık skoru hesapla (0-100)"""
        total_issues = (
            len([fk for fk in self.results['foreign_keys'] if '❌' in fk['status']]) +
            len(self.results['orphaned_records']) +
            len(self.results['missing_indexes']) +
            len(self.results['relationship_issues'])
        )
        
        total_checks = (
            len(self.results['foreign_keys']) +
            len(self.results['cascade_rules']) +
            1  # Orphaned records check
        )
        
        if total_checks == 0:
            return 100.0
        
        score = max(0, 100 - (total_issues / total_checks * 100))
        return round(score, 2)
    
    def print_summary(self):
        """Özet rapor yazdır"""
        print("\n" + "="*60)
        print("📊 DATABASE INTEGRITY VALIDATION SUMMARY")
        print("="*60)
        
        print(f"\n✅ Geçerli foreign key'ler: {len([fk for fk in self.results['foreign_keys'] if '✅' in fk['status']])}")
        print(f"❌ Geçersiz foreign key'ler: {len([fk for fk in self.results['foreign_keys'] if '❌' in fk['status']])}")
        print(f"❌ Yetim kayıtlar: {sum(r.get('orphan_count', 0) for r in self.results['orphaned_records'])}")
        print(f"⚠️  Eksik index'ler: {len(self.results['missing_indexes'])}")
        print(f"⚠️  İlişki sorunları: {len(self.results['relationship_issues'])}")
        
        health_score = self._calculate_health_score()
        print(f"\n🏥 Sağlık Skoru: {health_score}%")
        
        if health_score >= 90:
            print("✅ Mükemmel! Veritabanı bütünlüğü sağlıklı.")
        elif health_score >= 70:
            print("⚠️  İyi, ancak bazı iyileştirmeler gerekli.")
        else:
            print("❌ Dikkat! Ciddi sorunlar var, inceleme gerekli.")
        
        # Detaylı sorunları göster
        if self.results['orphaned_records']:
            print("\n❌ Yetim Kayıtlar (İlk 5):")
            for item in self.results['orphaned_records'][:5]:
                print(f"  - {item['table']}.{item['column']} → {item['referred_table']}")
                print(f"    {item['orphan_count']} yetim kayıt")
        
        if self.results['missing_indexes']:
            print("\n⚠️  Eksik Index'ler (İlk 5):")
            for item in self.results['missing_indexes'][:5]:
                print(f"  - {item['table']}.{item['column']}")
                print(f"    Öneri: {item['recommendation']}")


def main():
    """Ana fonksiyon"""
    print("🚀 Database Integrity Validation başlatılıyor...\n")
    
    validator = DatabaseIntegrityValidator()
    
    # Veritabanına bağlan
    if not validator.connect():
        print("\n⚠️  Veritabanı bağlantısı kurulamadı.")
        print("⚠️  Offline mode: Sadece model dosyalarından analiz yapılacak")
        print("\n💡 Veritabanını başlatmak için:")
        print("   docker-compose up -d postgres")
        print("   veya")
        print("   python backend/init_db.py")
        return
    
    # Foreign key'leri doğrula
    validator.validate_foreign_keys()
    
    # Yetim kayıtları kontrol et
    validator.check_orphaned_records()
    
    # Cascade kurallarını kontrol et
    validator.check_cascade_rules()
    
    # Eksik index'leri tespit et
    validator.check_missing_indexes()
    
    # İlişkileri analiz et
    validator.analyze_relationships()
    
    # Rapor oluştur
    validator.generate_report()
    
    # Özet yazdır
    validator.print_summary()
    
    print("\n✅ Validation tamamlandı!")


if __name__ == "__main__":
    main()
