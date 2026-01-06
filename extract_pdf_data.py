import re
from PyPDF2 import PdfReader

def extract_multiple_data_from_pdf(pdf_path):
    try:
        # Read whole text from PDF
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        # Pattern to extract each data block (NR + CVV + EXPIRE)
        pattern = re.compile(
            r"NR:\s*(\d+)[\s\S]*?CVV:\s*(\d{3,4})[\s\S]*?EXPIRE:\s*([\d/]+)", 
            re.IGNORECASE
        )

        results = []
        for match in pattern.finditer(text):
            nr = match.group(1)
            cvv = match.group(2)
            expire = match.group(3)
            results.append(f"{nr}/{expire}/{cvv}")

        if results:
            return "\n".join(results)
        else:
            return "No NR-formatted data blocks found."

    except Exception as e:
        return f"Error reading PDF: {e}"

if __name__ == "__main__":
    pdf_file = input("Enter the path to the PDF file: ").strip()
    extracted_data = extract_multiple_data_from_pdf(pdf_file)

    # Save output to a text file
    output_file = "extracted_output.txt"
    try:
        with open(output_file, "w") as f:
            f.write(extracted_data)
        print(f"Extraction complete! Output saved to '{output_file}'")
    except Exception as e:
        print(f"Failed to save output to file: {e}")

    # Optional: also print extracted data in terminal
    print("\nExtracted Data:\n")
    print(extracted_data)
