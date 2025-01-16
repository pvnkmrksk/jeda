#!/usr/bin/env python3

"""
SVG Text Size Adjuster for Transit Maps
=====================================

A utility for adjusting text sizes in SVG transit maps to improve readability
and visual consistency. Part of the extended LOOM transit map toolkit.

MIT License

Copyright (c) 2024 Pavan Kumar (@pvnkmrksk)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This work builds upon the LOOM project (https://github.com/ad-freiburg/loom)
and is distributed under compatible terms.

Author: ಪವನ ಕುಮಾರ ​| Pavan Kumar, PhD (@pvnkmrksk)
"""

import sys
import logging
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Union

# Configure logging
logging.basicConfig(
    format='%(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def adjust_svg_text_sizes(
    input_file: Union[str, Path], 
    output_file: Union[str, Path], 
    scale_factor: float
) -> None:
    """
    Adjust text sizes in an SVG file using standard library XML parsing.
    
    Args:
        input_file: Path to input SVG file
        output_file: Path to output SVG file
        scale_factor: Factor to scale text sizes by (e.g., 0.85 for 85%)
    """
    try:
        # Load and parse SVG file
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logger.info(f"Loading SVG file: {input_file}")
        tree = ET.parse(input_file)
        root = tree.getroot()
        
        # SVG namespace
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        
        # Find all elements with font-size attribute
        adjustment_count = 0
        for elem in root.findall('.//svg:text', ns):
            try:
                if 'font-size' in elem.attrib:
                    current_size = float(elem.attrib['font-size'])
                    new_size = current_size * scale_factor
                    elem.attrib['font-size'] = str(new_size)
                    adjustment_count += 1
            except (ValueError, KeyError) as e:
                logger.warning(f"Couldn't process text element: {e}")
                continue
            
            # Also check style attribute for font-size
            if 'style' in elem.attrib:
                style = elem.attrib['style']
                style_dict = dict(s.split(':') for s in style.split(';') if ':' in s)
                if 'font-size' in style_dict:
                    try:
                        current_size = float(style_dict['font-size'].rstrip('px'))
                        new_size = current_size * scale_factor
                        style_dict['font-size'] = f"{new_size}px"
                        elem.attrib['style'] = ';'.join(f"{k}:{v}" for k, v in style_dict.items())
                        adjustment_count += 1
                    except ValueError as e:
                        logger.warning(f"Couldn't process style font-size: {e}")
        
        # Save the modified SVG
        logger.info(f"Adjusted {adjustment_count} text elements in {Path(output_file).name}")
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
    except Exception as e:
        logger.error(f"Error processing SVG file: {e}")
        raise

def main():
    """
    Main function to handle command line usage.
    """
    if len(sys.argv) != 4:
        print("Usage: python adjust_svg.py <input_svg> <output_svg> <scale_factor>")
        sys.exit(1)
    
    try:
        input_file = Path(sys.argv[1])
        output_file = Path(sys.argv[2])
        scale_factor = float(sys.argv[3])
        
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Create output directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        adjust_svg_text_sizes(input_file, output_file, scale_factor)
        
    except Exception as e:
        logger.error(f"Failed to process SVG: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 