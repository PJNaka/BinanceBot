import json
from typing import List, Dict, Any # For type hinting

ELEMENTS_FILE_PATH = "data/elements.json"

# Sample data for initial creation if elements.json is missing or empty
# This list should ideally match the one used in the previous step to populate the file.
DEFAULT_ELEMENTS_DATA = [
  { "name": "Hydrogen", "symbol": "H", "atomic_number": 1, "mass": 1.008 },
  { "name": "Helium", "symbol": "He", "atomic_number": 2, "mass": 4.002602 },
  { "name": "Lithium", "symbol": "Li", "atomic_number": 3, "mass": 6.94 },
  { "name": "Beryllium", "symbol": "Be", "atomic_number": 4, "mass": 9.0121831 },
  { "name": "Boron", "symbol": "B", "atomic_number": 5, "mass": 10.81 },
  { "name": "Carbon", "symbol": "C", "atomic_number": 6, "mass": 12.011 },
  { "name": "Nitrogen", "symbol": "N", "atomic_number": 7, "mass": 14.007 },
  { "name": "Oxygen", "symbol": "O", "atomic_number": 8, "mass": 15.999 },
  { "name": "Fluorine", "symbol": "F", "atomic_number": 9, "mass": 18.998403163 },
  { "name": "Neon", "symbol": "Ne", "atomic_number": 10, "mass": 20.1797 },
  { "name": "Sodium", "symbol": "Na", "atomic_number": 11, "mass": 22.98976928 },
  { "name": "Magnesium", "symbol": "Mg", "atomic_number": 12, "mass": 24.305 },
  { "name": "Aluminum", "symbol": "Al", "atomic_number": 13, "mass": 26.9815385 },
  { "name": "Silicon", "symbol": "Si", "atomic_number": 14, "mass": 28.085 },
  { "name": "Phosphorus", "symbol": "P", "atomic_number": 15, "mass": 30.973761998 },
  { "name": "Sulfur", "symbol": "S", "atomic_number": 16, "mass": 32.06 },
  { "name": "Chlorine", "symbol": "Cl", "atomic_number": 17, "mass": 35.45 },
  { "name": "Argon", "symbol": "Ar", "atomic_number": 18, "mass": 39.948 },
  { "name": "Potassium", "symbol": "K", "atomic_number": 19, "mass": 39.0983 },
  { "name": "Calcium", "symbol": "Ca", "atomic_number": 20, "mass": 40.078 },
  { "name": "Scandium", "symbol": "Sc", "atomic_number": 21, "mass": 44.955908 },
  { "name": "Titanium", "symbol": "Ti", "atomic_number": 22, "mass": 47.867 },
  { "name": "Vanadium", "symbol": "V", "atomic_number": 23, "mass": 50.9415 },
  { "name": "Chromium", "symbol": "Cr", "atomic_number": 24, "mass": 51.9961 },
  { "name": "Manganese", "symbol": "Mn", "atomic_number": 25, "mass": 54.938044 },
  { "name": "Iron", "symbol": "Fe", "atomic_number": 26, "mass": 55.845 },
  { "name": "Cobalt", "symbol": "Co", "atomic_number": 27, "mass": 58.933194 },
  { "name": "Nickel", "symbol": "Ni", "atomic_number": 28, "mass": 58.6934 },
  { "name": "Copper", "symbol": "Cu", "atomic_number": 29, "mass": 63.546 },
  { "name": "Zinc", "symbol": "Zn", "atomic_number": 30, "mass": 65.38 }
]

def load_elements() -> List[Dict[str, Any]]:
    """Loads the list of elements from the JSON file."""
    try:
        # Ensure the data directory exists if it's supposed to be created by this script
        # For this project, we assume data/elements.json is either present or created by if __name__ == '__main__'
        with open(ELEMENTS_FILE_PATH, 'r', encoding='utf-8') as f:
            elements_data = json.load(f)
            if not isinstance(elements_data, list): # Basic validation
                print(f"Warning: Data in {ELEMENTS_FILE_PATH} is not a list. Returning empty list.")
                return []
            # Further validation could be added here to check for required keys in each dict
            return elements_data
    except FileNotFoundError:
        print(f"Warning: {ELEMENTS_FILE_PATH} not found. Returning empty list. Consider running this script directly to initialize.")
        return [] 
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from {ELEMENTS_FILE_PATH}. File might be corrupted. Returning empty list.")
        return []
    except Exception as e: # Catch any other unexpected errors during loading
        print(f"An unexpected error occurred while loading {ELEMENTS_FILE_PATH}: {e}. Returning empty list.")
        return []

def get_element_by_symbol(symbol: str, elements_list: List[Dict[str, Any]] = None) -> Dict[str, Any] | None:
    """
    Retrieves an element from the list by its chemical symbol.
    If elements_list is not provided, it calls load_elements() internally.
    """
    elements = elements_list if elements_list is not None else load_elements()
    for element in elements:
        if element.get("symbol") == symbol:
            return element
    return None

def get_element_by_name(name: str, elements_list: List[Dict[str, Any]] = None) -> Dict[str, Any] | None:
    """
    Retrieves an element from the list by its name (case-insensitive).
    If elements_list is not provided, it calls load_elements() internally.
    """
    elements = elements_list if elements_list is not None else load_elements()
    for element in elements:
        if element.get("name", "").lower() == name.lower():
            return element
    return None

if __name__ == '__main__':
    # This block now primarily serves to initialize elements.json if it's missing or empty,
    # and to demonstrate the module's functions.
    
    print(f"Checking {ELEMENTS_FILE_PATH}...")
    elements_data = load_elements()

    if not elements_data: # File not found, empty, or corrupted
        print(f"{ELEMENTS_FILE_PATH} is missing, empty, or invalid. Initializing with default data...")
        try:
            # Create the data directory if it doesn't exist
            import os
            os.makedirs(os.path.dirname(ELEMENTS_FILE_PATH), exist_ok=True)
            
            with open(ELEMENTS_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_ELEMENTS_DATA, f, indent=2)
            print(f"Created {ELEMENTS_FILE_PATH} with {len(DEFAULT_ELEMENTS_DATA)} elements.")
            elements_data = DEFAULT_ELEMENTS_DATA # Use the data we just wrote for tests below
        except Exception as e:
            print(f"Error initializing {ELEMENTS_FILE_PATH}: {e}")
            # If initialization fails, elements_data will remain empty or None, and tests will reflect that.
    else:
        print(f"{ELEMENTS_FILE_PATH} already exists and contains {len(elements_data)} elements.")

    print("\n--- Testing load_elements() ---")
    if elements_data: # Check if elements_data has content (either loaded or from default init)
        print(f"Successfully loaded/initialized {len(elements_data)} elements.")
        print(f"First 3 elements: {elements_data[:3]}")
    else:
        print("No elements data available to test after load/initialization attempt.")

    # Only run utility function tests if elements_data is available
    if elements_data:
        print("\n--- Testing utility functions ---")
        
        # Test get_element_by_symbol
        test_symbol_exists = "O"  # Oxygen
        oxygen = get_element_by_symbol(test_symbol_exists, elements_data)
        if oxygen:
            print(f"Found element by symbol '{test_symbol_exists}': {oxygen.get('name')}, Atomic #: {oxygen.get('atomic_number')}")
        else:
            print(f"Element with symbol '{test_symbol_exists}' not found.")

        test_symbol_not_exists = "Xy"
        non_existent_symbol = get_element_by_symbol(test_symbol_not_exists, elements_data)
        if not non_existent_symbol:
            print(f"Correctly did not find element with symbol '{test_symbol_not_exists}'.")
        else:
            print(f"Error: Found element with symbol '{test_symbol_not_exists}' when it should not exist.")

        # Test get_element_by_name (case-insensitive)
        test_name_exists = "carbon" 
        carbon = get_element_by_name(test_name_exists, elements_data)
        if carbon:
            print(f"Found element by name '{test_name_exists}': Symbol {carbon.get('symbol')}, Mass: {carbon.get('mass')}")
        else:
            print(f"Element with name '{test_name_exists}' not found.")
        
        test_name_exists_cased = "Silicon"
        silicon = get_element_by_name(test_name_exists_cased, elements_data)
        if silicon:
            print(f"Found element by name '{test_name_exists_cased}': Symbol {silicon.get('symbol')}, Mass: {silicon.get('mass')}")
        else:
            print(f"Element with name '{test_name_exists_cased}' not found.")

        test_name_not_exists = "Kryptonite"
        non_existent_name = get_element_by_name(test_name_not_exists, elements_data)
        if not non_existent_name:
            print(f"Correctly did not find element with name '{test_name_not_exists}'.")
        else:
            print(f"Error: Found element with name '{test_name_not_exists}' when it should not exist.")
        
        # Test with internally loaded data (if elements_list is None)
        print("\n--- Testing utility functions with internal load_elements() ---")
        # Assuming elements.json is correctly populated by now
        helium_by_symbol = get_element_by_symbol("He")
        if helium_by_symbol and helium_by_symbol['name'] == "Helium":
            print(f"Successfully fetched Helium by symbol using internal load: {helium_by_symbol}")
        else:
            print(f"Failed to fetch Helium by symbol using internal load. Got: {helium_by_symbol}")

        iron_by_name = get_element_by_name("Iron")
        if iron_by_name and iron_by_name['symbol'] == "Fe":
            print(f"Successfully fetched Iron by name using internal load: {iron_by_name}")
        else:
            print(f"Failed to fetch Iron by name using internal load. Got: {iron_by_name}")
    else:
        print("\nSkipping utility function tests as no element data is available.")

    print("\n--- End of data.py tests ---")
