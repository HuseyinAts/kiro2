#!/usr/bin/env python3
"""
Database Model Validation Script
Validates SQLAlchemy models for foreign keys and relationships
"""

import os
import sys
import json
import ast
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

class DatabaseModelValidator:
    def __init__(self, backend_root: str = "backend"):
        self.backend_root = Path(backend_root)
        self.models = {}
        self.relationships = defaultdict(list)
        self.foreign_keys = []
        self.results = {
            "models_found": [],
            "foreign_keys": [],
            "relationships": [],
            "cascade_rules": [],
            "missing_back_populates": [],
            "circular_dependencies": []
        }
    
    def find_model_files(self) -> List[Path]:
        """Model dosyalarını bul"""
        print("🔍 Model dosyaları aranıyor...")
        
        model_files = []
        search_patterns = [
            "models.py",
            "models/*.py",
            "app/models/*.py",
            "backend/models/*.py"
        ]
        
        for pattern in search_patterns:
            for model_file in self.backend_root.glob(pattern):
                if "__pycache__" not in str(model_file) and model_file.is_file():
                    model_files.append(model_file)
        
        print(f"✅ {len(model_files)} model dosyası bulundu")
        return model_files
    
    def parse_models(self, model_files: List[Path]):
        """Model dosyalarını parse et"""
        print("\n🔍 Model dosyaları parse ediliyor...")
        
        for model_file in model_files:
            try:
                content = model_file.read_text(encoding='utf-8')
                
                # Class tanımlarını bul
                class_pattern = r'class\s+(\w+)\s*\([^)]*Base[^)]*\):'
                classes = re.findall(class_pattern, content)
                
                for class_name in classes:
                    self.models[class_name] = {
                        "file": str(model_file.relative_to(self.backend_root)),
                        "foreign_keys": [],
                        "relationships": []
                    }
                    self.results['models_found'].append({
                        "model": class_name,
                        "file": str(model_file.relative_to(self.backend_root))
                    })
                
                # Foreign key'leri bul
                fk_pattern = r'(\w+)\s*=\s*Column\([^)]*ForeignKey\(["\']([^"\']+)["\']\)'
                fk_matches = re.findall(fk_pattern, content)
                
                for column_name, fk_reference in fk_matches:
                    # Hangi class'a ait olduğunu bul
                    for class_name in classes:
                        class_start = content.find(f'class {class_name}')
                        if class_start != -1:
                            fk_pos = content.find(f'{column_name} = Column')
                            if fk_pos > class_start:
                                # Next class position
                                next_class = content.find('class ', class_start + 1)
                                if next_class == -1 or fk_pos < next_class:
                                    self.models[class_name]['foreign_keys'].append({
                                        "column": column_name,
                                        "references": fk_reference
                                    })
                                    
                                    # Parse cascade rules
                                    fk_line_start = content.rfind('\n', 0, fk_pos)
                                    fk_line_end = content.find('\n', fk_pos)
                                    fk_line = content[fk_line_start:fk_line_end]
                                    
                                    on_delete = "NO ACTION"
                                    on_update = "NO ACTION"
                                    
                                    if 'ondelete=' in fk_line:
                                        on_delete_match = re.search(r'ondelete=["\']([^"\']+)["\']', fk_line)
                                        if on_delete_match:
                                            on_delete = on_delete_match.group(1)
                                    
                                    if 'onupdate=' in fk_line:
                                        on_update_match = re.search(r'onupdate=["\']([^"\']+)["\']', fk_line)
                                        if on_update_match:
                                            on_update = on_update_match.group(1)
                                    
                                    self.foreign_keys.append({
                                        "model": class_name,
                                        "column": column_name,
                                        "references": fk_reference,
                                        "on_delete": on_delete,
                                        "on_update": on_update,
                                        "file": str(model_file.relative_to(self.backend_root))
                                    })
                                    break
                
                # Relationship'leri bul
                rel_pattern = r'(\w+)\s*=\s*relationship\(["\'](\w+)["\']\s*(?:,\s*back_populates=["\'](\w+)["\'])?'
                rel_matches = re.findall(rel_pattern, content)
                
                for rel_name, target_model, back_populates in rel_matches:
                    for class_name in classes:
                        class_start = content.find(f'class {class_name}')
                        if class_start != -1:
                            rel_pos = content.find(f'{rel_name} = relationship')
                            if rel_pos > class_start:
                                next_class = content.find('class ', class_start + 1)
                                if next_class == -1 or rel_pos < next_class:
                                    self.models[class_name]['relationships'].append({
                                        "name": rel_name,
                                        "target": target_model,
                                        "back_populates": back_populates or None
                                    })
                                    
                                    self.relationships[class_name].append(target_model)
                                    
                                    if not back_populates:
                                        self.results['missing_back_populates'].append({
                                            "model": class_name,
                                            "relationship": rel_name,
                                            "target": target_model,
                                            "status": "⚠️  Missing back_populates"
                                        })
                                    break
                
            except Exception as e:
                print(f"⚠️  {model_file} parse edilemedi: {e}")
        
        print(f"✅ {len(self.models)} model parse edildi")
        print(f"✅ {len(self.foreign_keys)} foreign key bulundu")
        print(f"✅ {sum(len(m['relationships']) for m in self.models.values())} relationship bulundu")
    
    def validate_foreign_keys(self):
        """Foreign key'leri doğrula"""
        print("\n🔍 Foreign key'ler doğrulanıyor...")
        
        valid_fks = 0
        invalid_fks = 0
        
        for fk in self.foreign_keys:
            # Parse reference (table.column format)
            ref_parts = fk['references'].split('.')
            if len(ref_parts) == 2:
                ref_table, ref_column = ref_parts
                
                # Table name'i model name'e çevir (snake_case -> PascalCase)
                ref_model = ''.join(word.capitalize() for word in ref_table.split('_'))
                
                # Model var mı kontrol et
                if ref_model in self.models or ref_table in self.models:
                    valid_fks += 1
                    status = "✅ Valid"
                else:
                    invalid_fks += 1
                    status = f"⚠️  Referenced model '{ref_model}' not found"
                
                self.results['foreign_keys'].append({
                    "model": fk['model'],
                    "column": fk['column'],
                    "references": fk['references'],
                    "on_delete": fk['on_delete'],
                    "on_update": fk['on_update'],
                    "file": fk['file'],
                    "status": status
                })
        
        print(f"✅ {valid_fks}/{len(self.foreign_keys)} foreign key geçerli")
        if invalid_fks > 0:
            print(f"⚠️  {invalid_fks} foreign key'de referenced model bulunamadı")
        
        return valid_fks, invalid_fks
    
    def validate_relationships(self):
        """Relationship'leri doğrula"""
        print("\n🔍 Relationship'ler doğrulanıyor...")
        
        valid_rels = 0
        invalid_rels = 0
        
        for model_name, model_data in self.models.items():
            for rel in model_data['relationships']:
                target_model = rel['target']
                back_populates = rel['back_populates']
                
                # Target model var mı?
                if target_model in self.models:
                    valid_rels += 1
                    status = "✅ Valid"
                    
                    # back_populates kontrolü
                    if back_populates:
                        # Target model'de karşılık var mı?
                        target_rels = self.models[target_model]['relationships']
                        has_back_ref = any(
                            r['name'] == back_populates and r['target'] == model_name
                            for r in target_rels
                        )
                        
                        if not has_back_ref:
                            status = "⚠️  back_populates mismatch"
                else:
                    invalid_rels += 1
                    status = f"❌ Target model '{target_model}' not found"
                
                self.results['relationships'].append({
                    "model": model_name,
                    "relationship": rel['name'],
                    "target": target_model,
                    "back_populates": back_populates,
                    "status": status
                })
        
        total_rels = sum(len(m['relationships']) for m in self.models.values())
        print(f"✅ {valid_rels}/{total_rels} relationship geçerli")
        if invalid_rels > 0:
            print(f"❌ {invalid_rels} relationship'de target model bulunamadı")
        
        return valid_rels, invalid_rels
    
    def check_cascade_rules(self):
        """Cascade kurallarını kontrol et"""
        print("\n🔍 Cascade kuralları kontrol ediliyor...")
        
        cascade_summary = defaultdict(int)
        
        for fk in self.foreign_keys:
            on_delete = fk['on_delete']
            on_update = fk['on_update']
            
            cascade_summary[on_delete] += 1
            
            self.results['cascade_rules'].append({
                "model": fk['model'],
                "column": fk['column'],
                "references": fk['references'],
                "on_delete": on_delete,
                "on_update": on_update,
                "status": "✅ Configured"
            })
        
        print(f"✅ {len(self.foreign_keys)} cascade rule kontrol edildi")
        print("\nCascade Rule Dağılımı:")
        for rule, count in cascade_summary.items():
            print(f"  - {rule}: {count}")
        
        return len(self.foreign_keys)
    
    def find_circular_dependencies(self):
        """Circular dependency'leri bul"""
        print("\n🔍 Circular dependency'ler aranıyor...")
        
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.relationships.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)
            
            rec_stack.remove(node)
        
        for node in self.relationships:
            if node not in visited:
                dfs(node, [])
        
        if cycles:
            print(f"⚠️  {len(cycles)} circular dependency bulundu")
            for cycle in cycles:
                self.results['circular_dependencies'].append({
                    "cycle": ' → '.join(cycle),
                    "models": cycle,
                    "status": "⚠️  Circular dependency"
                })
        else:
            print(f"✅ Circular dependency bulunamadı")
        
        return len(cycles)
    
    def generate_report(self, output_file: str = "database_model_validation_report.json"):
        """Detaylı rapor oluştur"""
        print(f"\n📊 Rapor oluşturuluyor: {output_file}")
        
        report = {
            "summary": {
                "total_models": len(self.models),
                "total_foreign_keys": len(self.foreign_keys),
                "valid_foreign_keys": len([fk for fk in self.results['foreign_keys'] if '✅' in fk['status']]),
                "total_relationships": len(self.results['relationships']),
                "valid_relationships": len([r for r in self.results['relationships'] if '✅' in r['status']]),
                "missing_back_populates": len(self.results['missing_back_populates']),
                "circular_dependencies": len(self.results['circular_dependencies']),
                "cascade_rules": len(self.results['cascade_rules'])
            },
            "details": self.results,
            "health_score": self._calculate_health_score()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Rapor kaydedildi: {output_file}")
        return report
    
    def _calculate_health_score(self) -> float:
        """Sağlık skoru hesapla"""
        total_issues = (
            len([fk for fk in self.results['foreign_keys'] if '❌' in fk['status'] or '⚠️' in fk['status']]) +
            len([r for r in self.results['relationships'] if '❌' in r['status'] or '⚠️' in r['status']]) +
            len(self.results['missing_back_populates']) +
            len(self.results['circular_dependencies'])
        )
        
        total_checks = (
            len(self.results['foreign_keys']) +
            len(self.results['relationships']) +
            1
        )
        
        if total_checks == 0:
            return 100.0
        
        score = max(0, 100 - (total_issues / total_checks * 100))
        return round(score, 2)
    
    def print_summary(self):
        """Özet rapor yazdır"""
        print("\n" + "="*60)
        print("📊 DATABASE MODEL VALIDATION SUMMARY")
        print("="*60)
        
        print(f"\n📦 Toplam Model: {len(self.models)}")
        print(f"🔗 Toplam Foreign Key: {len(self.foreign_keys)}")
        print(f"🔗 Toplam Relationship: {len(self.results['relationships'])}")
        
        print(f"\n✅ Geçerli Foreign Key'ler: {len([fk for fk in self.results['foreign_keys'] if '✅' in fk['status']])}")
        print(f"⚠️  Sorunlu Foreign Key'ler: {len([fk for fk in self.results['foreign_keys'] if '⚠️' in fk['status'] or '❌' in fk['status']])}")
        
        print(f"\n✅ Geçerli Relationship'ler: {len([r for r in self.results['relationships'] if '✅' in r['status']])}")
        print(f"⚠️  Sorunlu Relationship'ler: {len([r for r in self.results['relationships'] if '⚠️' in r['status'] or '❌' in r['status']])}")
        
        print(f"\n⚠️  Missing back_populates: {len(self.results['missing_back_populates'])}")
        print(f"⚠️  Circular Dependencies: {len(self.results['circular_dependencies'])}")
        
        health_score = self._calculate_health_score()
        print(f"\n🏥 Sağlık Skoru: {health_score}%")
        
        if health_score >= 90:
            print("✅ Mükemmel! Model tanımlamaları sağlıklı.")
        elif health_score >= 70:
            print("⚠️  İyi, ancak bazı iyileştirmeler gerekli.")
        else:
            print("❌ Dikkat! Ciddi sorunlar var, inceleme gerekli.")
        
        # Detaylı sorunları göster
        if self.results['missing_back_populates']:
            print("\n⚠️  Missing back_populates (İlk 5):")
            for item in self.results['missing_back_populates'][:5]:
                print(f"  - {item['model']}.{item['relationship']} → {item['target']}")
        
        if self.results['circular_dependencies']:
            print("\n⚠️  Circular Dependencies:")
            for item in self.results['circular_dependencies']:
                print(f"  - {item['cycle']}")


def main():
    """Ana fonksiyon"""
    print("🚀 Database Model Validation başlatılıyor...\n")
    
    validator = DatabaseModelValidator()
    
    # Model dosyalarını bul
    model_files = validator.find_model_files()
    
    if not model_files:
        print("❌ Model dosyası bulunamadı!")
        return
    
    # Model'leri parse et
    validator.parse_models(model_files)
    
    # Foreign key'leri doğrula
    validator.validate_foreign_keys()
    
    # Relationship'leri doğrula
    validator.validate_relationships()
    
    # Cascade kurallarını kontrol et
    validator.check_cascade_rules()
    
    # Circular dependency'leri bul
    validator.find_circular_dependencies()
    
    # Rapor oluştur
    validator.generate_report()
    
    # Özet yazdır
    validator.print_summary()
    
    print("\n✅ Validation tamamlandı!")


if __name__ == "__main__":
    main()
