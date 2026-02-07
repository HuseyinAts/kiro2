"""
RepoScanner: Kod tabanı analizi ve yapı keşfi.

STABIL Faz - Modül 1/9
Kod tabanını tarar, dosya yapısını analiz eder, bağımlılıkları keşfeder.

Temel Özellikler:
- Dosya yapısı tarama (gitignore respektli)
- Dil ve framework tespiti
- Bağımlılık analizi
- Kod metrikleri (LOC, complexity)
- Hot spot tespiti (sık değişen dosyalar)
"""

import os
import re
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum, auto
from datetime import datetime
from collections import defaultdict
import fnmatch


class FileType(Enum):
    """Dosya tipi kategorileri."""
    PYTHON = auto()
    JAVASCRIPT = auto()
    TYPESCRIPT = auto()
    HTML = auto()
    CSS = auto()
    JSON = auto()
    YAML = auto()
    MARKDOWN = auto()
    SQL = auto()
    SHELL = auto()
    CONFIG = auto()
    TEST = auto()
    UNKNOWN = auto()


class FrameworkHint(Enum):
    """Framework ipuçları."""
    FASTAPI = auto()
    DJANGO = auto()
    FLASK = auto()
    REACT = auto()
    VUE = auto()
    ANGULAR = auto()
    NEXTJS = auto()
    EXPRESS = auto()
    PYTEST = auto()
    JEST = auto()
    UNKNOWN = auto()


@dataclass
class FileInfo:
    """Tek dosya bilgisi."""
    path: str
    relative_path: str
    name: str
    extension: str
    file_type: FileType
    size_bytes: int
    line_count: int
    last_modified: datetime
    hash: str  # Content hash for change detection
    
    # Kod metrikleri
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    # İlişkiler
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "relative_path": self.relative_path,
            "name": self.name,
            "extension": self.extension,
            "file_type": self.file_type.name,
            "size_bytes": self.size_bytes,
            "line_count": self.line_count,
            "code_lines": self.code_lines,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
            "imports": self.imports,
            "exports": self.exports,
        }


@dataclass
class DirectoryInfo:
    """Dizin bilgisi."""
    path: str
    relative_path: str
    name: str
    file_count: int
    subdirectory_count: int
    total_size_bytes: int
    total_lines: int
    file_types: Dict[FileType, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "relative_path": self.relative_path,
            "name": self.name,
            "file_count": self.file_count,
            "subdirectory_count": self.subdirectory_count,
            "total_size_bytes": self.total_size_bytes,
            "total_lines": self.total_lines,
            "file_types": {k.name: v for k, v in self.file_types.items()},
        }


@dataclass
class DependencyInfo:
    """Bağımlılık bilgisi."""
    name: str
    version: Optional[str]
    source: str  # requirements.txt, package.json, etc.
    is_dev: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "source": self.source,
            "is_dev": self.is_dev,
        }


@dataclass
class ScanResult:
    """Tarama sonucu."""
    root_path: str
    scan_time: datetime
    duration_seconds: float
    
    # Dosya ve dizin bilgileri
    files: Dict[str, FileInfo] = field(default_factory=dict)
    directories: Dict[str, DirectoryInfo] = field(default_factory=dict)
    
    # Analiz sonuçları
    total_files: int = 0
    total_lines: int = 0
    total_size_bytes: int = 0
    file_type_counts: Dict[FileType, int] = field(default_factory=dict)
    
    # Framework tespiti
    detected_frameworks: List[FrameworkHint] = field(default_factory=list)
    primary_language: Optional[FileType] = None
    
    # Bağımlılıklar
    dependencies: List[DependencyInfo] = field(default_factory=list)
    
    # Hot spots (sık değişen/büyük dosyalar)
    largest_files: List[str] = field(default_factory=list)
    most_complex_files: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_path": self.root_path,
            "scan_time": self.scan_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "total_size_bytes": self.total_size_bytes,
            "file_type_counts": {k.name: v for k, v in self.file_type_counts.items()},
            "detected_frameworks": [f.name for f in self.detected_frameworks],
            "primary_language": self.primary_language.name if self.primary_language else None,
            "dependencies": [d.to_dict() for d in self.dependencies],
            "largest_files": self.largest_files,
            "most_complex_files": self.most_complex_files,
        }


class RepoScanner:
    """
    Kod tabanı tarayıcı.
    
    Kullanım:
        scanner = RepoScanner("C:/Users/husey/kiro2")
        result = scanner.scan()
        print(f"Toplam: {result.total_files} dosya, {result.total_lines} satır")
    """
    
    # Dosya uzantısı -> FileType mapping
    EXTENSION_MAP: Dict[str, FileType] = {
        ".py": FileType.PYTHON,
        ".js": FileType.JAVASCRIPT,
        ".jsx": FileType.JAVASCRIPT,
        ".ts": FileType.TYPESCRIPT,
        ".tsx": FileType.TYPESCRIPT,
        ".html": FileType.HTML,
        ".htm": FileType.HTML,
        ".css": FileType.CSS,
        ".scss": FileType.CSS,
        ".sass": FileType.CSS,
        ".less": FileType.CSS,
        ".json": FileType.JSON,
        ".yaml": FileType.YAML,
        ".yml": FileType.YAML,
        ".md": FileType.MARKDOWN,
        ".markdown": FileType.MARKDOWN,
        ".sql": FileType.SQL,
        ".sh": FileType.SHELL,
        ".bash": FileType.SHELL,
        ".zsh": FileType.SHELL,
        ".ps1": FileType.SHELL,
        ".bat": FileType.SHELL,
        ".cmd": FileType.SHELL,
    }
    
    # Config dosyaları
    CONFIG_FILES: Set[str] = {
        ".env", ".env.example", ".env.local",
        "pyproject.toml", "setup.py", "setup.cfg",
        "package.json", "tsconfig.json", "webpack.config.js",
        ".eslintrc", ".prettierrc", ".babelrc",
        "docker-compose.yml", "Dockerfile",
        ".gitignore", ".dockerignore",
        "requirements.txt", "Pipfile", "poetry.lock",
    }
    
    # Varsayılan ignore patterns
    DEFAULT_IGNORE: Set[str] = {
        ".git", ".svn", ".hg",
        "node_modules", "__pycache__", ".pytest_cache",
        "venv", ".venv", "env", ".env",
        "dist", "build", ".next", ".nuxt",
        "*.pyc", "*.pyo", "*.egg-info",
        ".idea", ".vscode",
        "*.log", "*.tmp",
    }
    
    def __init__(
        self,
        root_path: str,
        ignore_patterns: Optional[Set[str]] = None,
        max_file_size_mb: float = 10.0,
        include_hidden: bool = False,
    ):
        self.root_path = Path(root_path).resolve()
        self.ignore_patterns = ignore_patterns or self.DEFAULT_IGNORE.copy()
        self.max_file_size = int(max_file_size_mb * 1024 * 1024)
        self.include_hidden = include_hidden
        
        # Gitignore patterns yükle
        self._load_gitignore()
    
    def _load_gitignore(self) -> None:
        """Gitignore dosyasını oku ve pattern'lere ekle."""
        gitignore_path = self.root_path / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            self.ignore_patterns.add(line)
            except Exception:
                pass  # Gitignore okunamazsa varsayılanlarla devam
    
    def _should_ignore(self, path: Path) -> bool:
        """Dosya/dizin ignore edilmeli mi?"""
        name = path.name
        relative = str(path.relative_to(self.root_path))
        
        # Hidden dosyalar
        if not self.include_hidden and name.startswith("."):
            # Bazı config dosyalarına izin ver
            if name not in {".env.example", ".gitignore"}:
                return True
        
        # Pattern matching
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
            if fnmatch.fnmatch(relative, pattern):
                return True
            if fnmatch.fnmatch(relative, f"*/{pattern}"):
                return True
        
        return False
    
    def _get_file_type(self, path: Path) -> FileType:
        """Dosya tipini belirle."""
        name = path.name.lower()
        ext = path.suffix.lower()
        
        # Config dosyaları
        if name in self.CONFIG_FILES:
            return FileType.CONFIG
        
        # Test dosyaları
        if "test" in name or "spec" in name:
            return FileType.TEST
        
        # Uzantıya göre
        return self.EXTENSION_MAP.get(ext, FileType.UNKNOWN)
    
    def _calculate_hash(self, content: bytes) -> str:
        """İçerik hash'i hesapla."""
        return hashlib.md5(content).hexdigest()[:12]
    
    def _count_lines(self, content: str, file_type: FileType) -> Tuple[int, int, int, int]:
        """
        Satır sayılarını hesapla.
        Returns: (total, code, comment, blank)
        """
        lines = content.split("\n")
        total = len(lines)
        blank = 0
        comment = 0
        code = 0
        
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                blank += 1
                continue
            
            # Python/JS/TS yorum kontrolü
            if file_type in {FileType.PYTHON}:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    if in_multiline_comment:
                        in_multiline_comment = False
                        comment += 1
                    elif stripped.count('"""') == 2 or stripped.count("'''") == 2:
                        comment += 1
                    else:
                        in_multiline_comment = True
                        comment += 1
                    continue
                if in_multiline_comment:
                    comment += 1
                    continue
                if stripped.startswith("#"):
                    comment += 1
                    continue
            
            elif file_type in {FileType.JAVASCRIPT, FileType.TYPESCRIPT}:
                if stripped.startswith("/*"):
                    in_multiline_comment = True
                    comment += 1
                    if "*/" in stripped:
                        in_multiline_comment = False
                    continue
                if in_multiline_comment:
                    comment += 1
                    if "*/" in stripped:
                        in_multiline_comment = False
                    continue
                if stripped.startswith("//"):
                    comment += 1
                    continue
            
            code += 1
        
        return total, code, comment, blank
    
    def _extract_imports(self, content: str, file_type: FileType) -> List[str]:
        """Import'ları çıkar."""
        imports = []
        
        if file_type == FileType.PYTHON:
            # import x, from x import y
            patterns = [
                r"^import\s+([\w\.]+)",
                r"^from\s+([\w\.]+)\s+import",
            ]
            for pattern in patterns:
                imports.extend(re.findall(pattern, content, re.MULTILINE))
        
        elif file_type in {FileType.JAVASCRIPT, FileType.TYPESCRIPT}:
            # import x from 'y', require('y')
            patterns = [
                r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]",
                r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
            ]
            for pattern in patterns:
                imports.extend(re.findall(pattern, content))
        
        return list(set(imports))
    
    def _extract_exports(self, content: str, file_type: FileType) -> List[str]:
        """Export'ları çıkar."""
        exports = []
        
        if file_type == FileType.PYTHON:
            # class X, def x, __all__
            exports.extend(re.findall(r"^class\s+(\w+)", content, re.MULTILINE))
            exports.extend(re.findall(r"^def\s+(\w+)", content, re.MULTILINE))
            
            # __all__ listesi
            all_match = re.search(r"__all__\s*=\s*\[(.*?)\]", content, re.DOTALL)
            if all_match:
                all_items = re.findall(r"['\"](\w+)['\"]", all_match.group(1))
                exports.extend(all_items)
        
        elif file_type in {FileType.JAVASCRIPT, FileType.TYPESCRIPT}:
            # export const/function/class, export default
            exports.extend(re.findall(r"export\s+(?:const|let|var|function|class)\s+(\w+)", content))
            exports.extend(re.findall(r"export\s+default\s+(?:class|function)?\s*(\w+)?", content))
        
        return list(set(filter(None, exports)))
    
    def _scan_file(self, path: Path) -> Optional[FileInfo]:
        """Tek dosyayı tara."""
        try:
            stat = path.stat()
            
            # Boyut kontrolü
            if stat.st_size > self.max_file_size:
                return None
            
            # İçeriği oku
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Binary dosya
                return None
            
            file_type = self._get_file_type(path)
            total, code, comment, blank = self._count_lines(content, file_type)
            
            return FileInfo(
                path=str(path),
                relative_path=str(path.relative_to(self.root_path)),
                name=path.name,
                extension=path.suffix,
                file_type=file_type,
                size_bytes=stat.st_size,
                line_count=total,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                hash=self._calculate_hash(content.encode("utf-8")),
                code_lines=code,
                comment_lines=comment,
                blank_lines=blank,
                imports=self._extract_imports(content, file_type),
                exports=self._extract_exports(content, file_type),
            )
        except Exception:
            return None
    
    def _detect_frameworks(self, files: Dict[str, FileInfo]) -> List[FrameworkHint]:
        """Framework'leri tespit et."""
        frameworks = []
        file_names = {Path(f).name for f in files.keys()}
        all_imports = set()
        
        for file_info in files.values():
            all_imports.update(file_info.imports)
        
        # Python frameworks
        if "fastapi" in all_imports:
            frameworks.append(FrameworkHint.FASTAPI)
        if "django" in all_imports or "manage.py" in file_names:
            frameworks.append(FrameworkHint.DJANGO)
        if "flask" in all_imports:
            frameworks.append(FrameworkHint.FLASK)
        if "pytest" in all_imports:
            frameworks.append(FrameworkHint.PYTEST)
        
        # JavaScript frameworks
        if "react" in all_imports or "next" in all_imports:
            frameworks.append(FrameworkHint.REACT)
        if "next.config.js" in file_names or "next.config.mjs" in file_names:
            frameworks.append(FrameworkHint.NEXTJS)
        if "vue" in all_imports:
            frameworks.append(FrameworkHint.VUE)
        if "@angular" in str(all_imports):
            frameworks.append(FrameworkHint.ANGULAR)
        if "express" in all_imports:
            frameworks.append(FrameworkHint.EXPRESS)
        if "jest" in all_imports or "jest.config.js" in file_names:
            frameworks.append(FrameworkHint.JEST)
        
        return list(set(frameworks))
    
    def _parse_dependencies(self, files: Dict[str, FileInfo]) -> List[DependencyInfo]:
        """Bağımlılıkları parse et."""
        dependencies = []
        
        for file_path, file_info in files.items():
            name = file_info.name
            
            # requirements.txt
            if name == "requirements.txt" or name.endswith("-requirements.txt"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                # package==version veya package>=version
                                match = re.match(r"([a-zA-Z0-9_-]+)([<>=!]+.+)?", line)
                                if match:
                                    dependencies.append(DependencyInfo(
                                        name=match.group(1),
                                        version=match.group(2) if match.group(2) else None,
                                        source=name,
                                    ))
                except Exception:
                    pass
            
            # package.json
            elif name == "package.json":
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        pkg = json.load(f)
                        
                        for dep_name, version in pkg.get("dependencies", {}).items():
                            dependencies.append(DependencyInfo(
                                name=dep_name,
                                version=version,
                                source="package.json",
                                is_dev=False,
                            ))
                        
                        for dep_name, version in pkg.get("devDependencies", {}).items():
                            dependencies.append(DependencyInfo(
                                name=dep_name,
                                version=version,
                                source="package.json",
                                is_dev=True,
                            ))
                except Exception:
                    pass
        
        return dependencies
    
    def scan(self) -> ScanResult:
        """
        Kod tabanını tara.
        
        Returns:
            ScanResult: Tarama sonuçları
        """
        start_time = datetime.now()
        
        files: Dict[str, FileInfo] = {}
        directories: Dict[str, DirectoryInfo] = {}
        file_type_counts: Dict[FileType, int] = defaultdict(int)
        total_lines = 0
        total_size = 0
        
        # Recursive tarama
        for root, dirs, filenames in os.walk(self.root_path):
            root_path = Path(root)
            
            # Ignore edilecek dizinleri filtrele
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]
            
            dir_files = 0
            dir_lines = 0
            dir_size = 0
            dir_types: Dict[FileType, int] = defaultdict(int)
            
            for filename in filenames:
                file_path = root_path / filename
                
                if self._should_ignore(file_path):
                    continue
                
                file_info = self._scan_file(file_path)
                if file_info:
                    files[str(file_path)] = file_info
                    file_type_counts[file_info.file_type] += 1
                    dir_types[file_info.file_type] += 1
                    total_lines += file_info.line_count
                    total_size += file_info.size_bytes
                    dir_files += 1
                    dir_lines += file_info.line_count
                    dir_size += file_info.size_bytes
            
            # Dizin bilgisi
            if dir_files > 0:
                directories[str(root_path)] = DirectoryInfo(
                    path=str(root_path),
                    relative_path=str(root_path.relative_to(self.root_path)),
                    name=root_path.name,
                    file_count=dir_files,
                    subdirectory_count=len(dirs),
                    total_size_bytes=dir_size,
                    total_lines=dir_lines,
                    file_types=dict(dir_types),
                )
        
        # Framework tespiti
        detected_frameworks = self._detect_frameworks(files)
        
        # Primary language
        primary_language = None
        if file_type_counts:
            # Test ve config hariç en çok kullanılan
            code_types = {k: v for k, v in file_type_counts.items() 
                         if k not in {FileType.TEST, FileType.CONFIG, FileType.UNKNOWN}}
            if code_types:
                primary_language = max(code_types, key=code_types.get)
        
        # Bağımlılıklar
        dependencies = self._parse_dependencies(files)
        
        # Hot spots
        sorted_by_size = sorted(files.values(), key=lambda f: f.size_bytes, reverse=True)
        largest_files = [f.relative_path for f in sorted_by_size[:10]]
        
        sorted_by_lines = sorted(files.values(), key=lambda f: f.code_lines, reverse=True)
        most_complex_files = [f.relative_path for f in sorted_by_lines[:10]]
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return ScanResult(
            root_path=str(self.root_path),
            scan_time=start_time,
            duration_seconds=duration,
            files=files,
            directories=directories,
            total_files=len(files),
            total_lines=total_lines,
            total_size_bytes=total_size,
            file_type_counts=dict(file_type_counts),
            detected_frameworks=detected_frameworks,
            primary_language=primary_language,
            dependencies=dependencies,
            largest_files=largest_files,
            most_complex_files=most_complex_files,
        )
    
    def scan_quick(self) -> Dict[str, Any]:
        """
        Hızlı tarama - sadece temel metrikler.
        """
        start_time = datetime.now()
        
        file_count = 0
        total_size = 0
        extensions: Dict[str, int] = defaultdict(int)
        
        for root, dirs, filenames in os.walk(self.root_path):
            root_path = Path(root)
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]
            
            for filename in filenames:
                file_path = root_path / filename
                if self._should_ignore(file_path):
                    continue
                
                try:
                    stat = file_path.stat()
                    if stat.st_size <= self.max_file_size:
                        file_count += 1
                        total_size += stat.st_size
                        ext = file_path.suffix.lower() or "(no ext)"
                        extensions[ext] += 1
                except Exception:
                    pass
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "root_path": str(self.root_path),
            "scan_time": start_time.isoformat(),
            "duration_seconds": duration,
            "file_count": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "extensions": dict(sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:20]),
        }


# Singleton instance
_scanner: Optional[RepoScanner] = None


def get_repo_scanner(root_path: Optional[str] = None) -> RepoScanner:
    """
    RepoScanner singleton instance'ı al.
    
    Args:
        root_path: Proje kök dizini (ilk çağrıda gerekli)
    
    Returns:
        RepoScanner instance
    """
    global _scanner
    
    if _scanner is None:
        if root_path is None:
            raise ValueError("İlk çağrıda root_path gerekli")
        _scanner = RepoScanner(root_path)
    
    return _scanner


def reset_scanner() -> None:
    """Scanner'ı sıfırla."""
    global _scanner
    _scanner = None


# Convenience function
def quick_scan(root_path: str) -> Dict[str, Any]:
    """
    Belirtilen dizini hızlıca tara.
    
    Args:
        root_path: Taranacak dizin
    
    Returns:
        Temel metrikler dict'i
    """
    scanner = RepoScanner(root_path)
    return scanner.scan_quick()
