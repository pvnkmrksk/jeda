#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import sys

def adjust_svg_text(input_file, output_file, scale_factor=1.3):
    # Register the SVG namespace
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    
    # Parse the SVG file
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    # Find all text elements
    for text in root.findall(".//*{http://www.w3.org/2000/svg}text"):
        # Get current font size
        font_size = text.get('font-size', '10')
        
        # Remove 'px' or 'pt' if present and convert to float
        font_size = float(''.join(c for c in font_size if c.isdigit() or c == '.'))
        
        # Scale the font size
        new_font_size = font_size * scale_factor
        
        # Set the new font size
        text.set('font-size', str(new_font_size))

    # Save the modified SVG
    tree.write(output_file, encoding='utf-8', xml_declaration=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: ./adjust_svg.py input.svg [output.svg] [scale_factor]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'output.svg'
    scale_factor = float(sys.argv[3]) if len(sys.argv) > 3 else 1.3  # 30% increase by default
    
    try:
        adjust_svg_text(input_file, output_file, scale_factor)
        print(f"Successfully modified SVG. Output saved to {output_file}")
    except Exception as e:
        print(f"Error processing SVG: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()