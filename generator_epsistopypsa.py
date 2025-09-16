from libs.epsistopypsa import generator_converter
from pathlib import Path

# Set input and output paths
input_path = "data/raw/generators.xlsx"  # Path to input Excel file
output_path = "data/pypsa"  # Path to output directory

# Create the output directory if it doesn't exist
Path(output_path).mkdir(parents=True, exist_ok=True)

# Call the generator_converter function
if __name__ == "__main__":
    print("Starting generator conversion...")
    print(f"Input file: {input_path}")
    print(f"Output directory: {output_path}")
    
    try:
        result = generator_converter(input_path, output_path)
        print("Generator conversion completed successfully!")
    except Exception as e:
        print(f"Error during conversion: {e}")


