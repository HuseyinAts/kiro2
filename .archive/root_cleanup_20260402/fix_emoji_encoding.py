#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIRO2 Emoji Encoding Fix Tool
Systematically replaces emojis in Python files with ASCII alternatives
"""

import os
import re
import glob
from typing import Dict, List, Tuple

# Emoji replacement mapping
EMOJI_REPLACEMENTS = {
    # Common emojis in the codebase
    '[TARGET]': '[TARGET]',
    '[CHART]': '[CHART]',
    '[LIGHTNING]': '[LIGHTNING]',
    '[TOOL]': '[TOOL]',
    '[ROCKET]': '[ROCKET]',
    '[BULB]': '[BULB]',
    '[TRENDING_UP]': '[TRENDING_UP]',
    '[TROPHY]': '[TROPHY]',
    '[CHECK]': '[CHECK]',
    '[X]': '[X]',
    '[STAR]': '[STAR]',
    '[GRADUATION_CAP]': '[GRADUATION_CAP]',
    '[BOOKS]': '[BOOKS]',
    '[BRAIN]': '[BRAIN]',
    '[MICROSCOPE]': '[MICROSCOPE]',
    '[COMPUTER]': '[COMPUTER]',
    '[MOBILE]': '[MOBILE]',
    '[GLOWING_STAR]': '[GLOWING_STAR]',
    '[CIRCUS]': '[CIRCUS]',
    '[MEDAL]': '[MEDAL]',
    '[FIRE]': '[FIRE]',
    '[DIAMOND]': '[DIAMOND]',
    '[ALERT]': '[ALERT]',
    '[GEAR]': '[GEAR]',
    '[PALETTE]': '[PALETTE]',
    '[PACKAGE]': '[PACKAGE]',
    '[MAG]': '[MAG]',
    '[MEMO]': '[MEMO]',
    '[DIZZY]': '[DIZZY]',
    '[PARTY]': '[PARTY]',
    '[CONSTRUCTION]': '[CONSTRUCTION]',
    '[HAMMER_WRENCH]': '[HAMMER_WRENCH]',
    '[BALLOON]': '[BALLOON]',
    '[RAINBOW]': '[RAINBOW]',
    '[THEATER]': '[THEATER]',
    '[PAGE]': '[PAGE]',
    '[CLIPBOARD]': '[CLIPBOARD]',
    '[CARD_INDEX]': '[CARD_INDEX]',
    '[FOLDER]': '[FOLDER]',
    '[MAILBOX]': '[MAILBOX]',
    '[EMAIL]': '[EMAIL]',
    '[CALLING]': '[CALLING]',
    '[PHONE]': '[PHONE]',
    '[FLOPPY]': '[FLOPPY]',
    '[CD]': '[CD]',
    '[LOCKED_KEY]': '[LOCKED_KEY]',
    '[LOCKED]': '[LOCKED]',
    '[KEY]': '[KEY]',
    '[GLOBE]': '[GLOBE]',
    '[LINK]': '[LINK]',
    '[SATELLITE]': '[SATELLITE]',
    '[TV]': '[TV]',
    '[DESKTOP]': '[DESKTOP]',
    '[PRINTER]': '[PRINTER]',
    '[KEYBOARD]': '[KEYBOARD]',
    '[MOUSE]': '[MOUSE]',
    '[MINIDISC]': '[MINIDISC]',
    '[DVD]': '[DVD]',
    '[VIDEO_GAME]': '[VIDEO_GAME]',
    '[BATTERY]': '[BATTERY]',
    '[PLUG]': '[PLUG]',
    '[FLASHLIGHT]': '[FLASHLIGHT]',
}

class EmojiFixTool:
    def __init__(self):
        self.fixed_files = []
        self.error_files = []
        self.stats = {
            'total_files': 0,
            'files_with_emojis': 0,
            'total_replacements': 0
        }

    def find_python_files(self, directory: str) -> List[str]:
        """Find all Python files in directory and subdirectories"""
        python_files = []
        for root, dirs, files in os.walk(directory):
            # Skip certain directories
            skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv'}
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files

    def contains_emojis(self, text: str) -> bool:
        """Check if text contains emojis"""
        emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F]|'  # emoticons
            r'[\U0001F300-\U0001F5FF]|'  # symbols & pictographs
            r'[\U0001F680-\U0001F6FF]|'  # transport & map symbols
            r'[\U0001F1E0-\U0001F1FF]|'  # flags (iOS)
            r'[\U00002600-\U000026FF]|'  # miscellaneous symbols
            r'[\U00002700-\U000027BF]'   # dingbats
        )
        return bool(emoji_pattern.search(text))

    def fix_emojis_in_text(self, text: str) -> Tuple[str, int]:
        """Replace emojis in text with ASCII alternatives"""
        replacement_count = 0
        
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            if emoji in text:
                count = text.count(emoji)
                text = text.replace(emoji, replacement)
                replacement_count += count
                
        return text, replacement_count

    def fix_file(self, file_path: str) -> bool:
        """Fix emojis in a single file"""
        try:
            # Read file with different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                print(f"[ERROR] Could not read file: {file_path}")
                self.error_files.append(file_path)
                return False
            
            # Check if file contains emojis
            if not self.contains_emojis(content):
                return True  # No emojis, nothing to fix
            
            # Fix emojis
            fixed_content, replacement_count = self.fix_emojis_in_text(content)
            
            if replacement_count > 0:
                # Write back the fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                print(f"[FIXED] {file_path}: {replacement_count} emoji replacements")
                self.fixed_files.append((file_path, replacement_count))
                self.stats['files_with_emojis'] += 1
                self.stats['total_replacements'] += replacement_count
                return True
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to fix {file_path}: {str(e)}")
            self.error_files.append(file_path)
            return False

    def fix_all_files(self, directory: str = "."):
        """Fix emojis in all Python files"""
        print(f"[START] Scanning for Python files in: {directory}")
        python_files = self.find_python_files(directory)
        self.stats['total_files'] = len(python_files)
        
        print(f"[INFO] Found {len(python_files)} Python files")
        
        for i, file_path in enumerate(python_files, 1):
            print(f"[PROGRESS] {i}/{len(python_files)}: Processing {file_path}")
            self.fix_file(file_path)
        
        self.print_summary()

    def print_summary(self):
        """Print summary of fixes"""
        print("\n" + "="*70)
        print("EMOJI ENCODING FIX SUMMARY")
        print("="*70)
        print(f"Total Python files scanned: {self.stats['total_files']}")
        print(f"Files with emojis fixed: {self.stats['files_with_emojis']}")
        print(f"Total emoji replacements: {self.stats['total_replacements']}")
        print(f"Error files: {len(self.error_files)}")
        
        if self.fixed_files:
            print(f"\n[SUCCESS] Fixed files:")
            for file_path, count in self.fixed_files:
                relative_path = os.path.relpath(file_path)
                print(f"  - {relative_path}: {count} replacements")
        
        if self.error_files:
            print(f"\n[ERROR] Failed files:")
            for file_path in self.error_files:
                relative_path = os.path.relpath(file_path)
                print(f"  - {relative_path}")
        
        print("\n[COMPLETE] Emoji encoding fix completed!")
        print("="*70)

def main():
    """Main function"""
    fixer = EmojiFixTool()
    
    # Fix emojis in current directory and all subdirectories
    fixer.fix_all_files(".")

if __name__ == "__main__":
    main()