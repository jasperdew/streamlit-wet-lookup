def extract_article_text(xml_content, article_number):
    """
    Extract article text from XML content with improved text formatting
    """
    tree = ET.parse(StringIO(xml_content))
    root = tree.getroot()
    
    for artikel in root.findall('.//artikel'):
        nr_element = artikel.find('./kop/nr')
        if nr_element is not None and nr_element.text.strip() == article_number:
            output_lines = [f"Artikel {article_number}"]
            
            # Process each lid
            for lid in artikel.findall('./lid'):
                # Get lid number
                lidnr_el = lid.find('lidnr')
                if lidnr_el is not None and lidnr_el.text:
                    output_lines.append(f"\n{lidnr_el.text.strip()}. ")
                
                # Process direct al elements
                for al in lid.findall('al'):
                    text_parts = []
                    
                    # Handle mixed content (text and elements)
                    if al.text:
                        text_parts.append(al.text.strip())
                    
                    # Handle extref elements within al
                    for elem in al:
                        if elem.tag == 'extref':
                            if elem.text:
                                text_parts.append(elem.text.strip())
                        if elem.tail:
                            text_parts.append(elem.tail.strip())
                    
                    # Join all text parts and add to output
                    if text_parts:
                        output_lines.append(" ".join(text_parts))
                
                # Process lists if present
                for lijst in lid.findall('lijst'):
                    for li in lijst.findall('li'):
                        li_nr_el = li.find('li.nr')
                        li_nr = li_nr_el.text.strip() if li_nr_el is not None else ''
                        
                        # Process al elements within li
                        for al in li.findall('al'):
                            if al.text and al.text.strip():
                                if li_nr:
                                    output_lines.append(f"{li_nr} {al.text.strip()}")
                                    li_nr = ''  # Only show number for first line
                                else:
                                    output_lines.append(f"   {al.text.strip()}")
            
            # Join all lines with proper spacing
            return "\n".join(line for line in output_lines if line.strip())
    
    return f"Artikel {article_number} niet gevonden."
