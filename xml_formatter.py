#!/usr/bin/env python3
"""
XML Formatter untuk Odoo XML Templates
Memformat semua file XML di gm_web/static/src/xml/ dengan indentasi yang konsisten
"""

import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse
from pathlib import Path

def format_xml_file(file_path, backup=True):
    """
    Format single XML file dengan indentasi yang konsisten
    """
    try:
        # Backup file asli jika diminta
        if backup:
            backup_path = f"{file_path}.backup"
            if not os.path.exists(backup_path):
                with open(file_path, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                print(f"✅ Backup created: {backup_path}")
        
        # Parse XML
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Convert to string dengan formatting
        rough_string = ET.tostring(root, encoding='unicode')
        
        # Parse dengan minidom untuk formatting yang lebih baik
        reparsed = minidom.parseString(rough_string)
        
        # Format dengan indentasi
        formatted = reparsed.toprettyxml(indent="  ", encoding=None)
        
        # Remove empty lines dan extra whitespace
        lines = []
        for line in formatted.split('\n'):
            line = line.rstrip()
            if line:  # Skip empty lines
                lines.append(line)
        
        # Write formatted content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
            f.write('\n')  # Add final newline
        
        print(f"✅ Formatted: {file_path}")
        return True
        
    except ET.ParseError as e:
        print(f"❌ XML Parse Error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error formatting {file_path}: {e}")
        return False

def format_xml_directory(directory_path, backup=True, recursive=True):
    """
    Format semua XML files di directory
    """
    xml_dir = Path(directory_path)
    
    if not xml_dir.exists():
        print(f"❌ Directory tidak ditemukan: {directory_path}")
        return False
    
    # Find all XML files
    if recursive:
        xml_files = list(xml_dir.rglob("*.xml"))
    else:
        xml_files = list(xml_dir.glob("*.xml"))
    
    if not xml_files:
        print(f"❌ Tidak ada file XML ditemukan di: {directory_path}")
        return False
    
    print(f"📁 Found {len(xml_files)} XML files in {directory_path}")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for xml_file in xml_files:
        if format_xml_file(str(xml_file), backup):
            success_count += 1
        else:
            error_count += 1
    
    print("=" * 60)
    print(f"📊 SUMMARY:")
    print(f"✅ Successfully formatted: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📁 Total files processed: {len(xml_files)}")
    
    return error_count == 0

def main():
    parser = argparse.ArgumentParser(description='Format XML files in Odoo templates')
    parser.add_argument('path', nargs='?', 
                       default='gm_web/static/src/xml',
                       help='Path to XML directory (default: gm_web/static/src/xml)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip creating backup files')
    parser.add_argument('--no-recursive', action='store_true',
                       help='Only format files in root directory, not subdirectories')
    
    args = parser.parse_args()
    
    # Convert relative path to absolute
    if not os.path.isabs(args.path):
        args.path = os.path.join(os.getcwd(), args.path)
    
    print("🔧 XML Formatter untuk Odoo Templates")
    print("=" * 60)
    print(f"📁 Target directory: {args.path}")
    print(f"💾 Create backup: {not args.no_backup}")
    print(f"🔄 Recursive: {not args.no_recursive}")
    print("=" * 60)
    
    # Confirm before proceeding
    if not args.no_backup:
        response = input("⚠️  Ini akan membuat backup file. Lanjutkan? (y/N): ")
        if response.lower() != 'y':
            print("❌ Dibatalkan oleh user")
            return 1
    
    # Format files
    success = format_xml_directory(args.path, backup=not args.no_backup, 
                                 recursive=not args.no_recursive)
    
    if success:
        print("\n🎉 Semua file XML berhasil diformat!")
        return 0
    else:
        print("\n⚠️  Beberapa file mengalami error. Cek output di atas.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
