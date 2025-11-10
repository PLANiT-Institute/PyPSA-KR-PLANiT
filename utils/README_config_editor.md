# PyPSA Configuration Editor

A standalone Streamlit-based GUI tool for viewing and editing PyPSA configuration Excel files.

## Installation

Make sure you have streamlit installed:

```bash
pip install streamlit openpyxl
```

## Usage

Run the configuration editor:

```bash
streamlit run utils/config_editor.py
```

Or from the project root:

```bash
cd /Users/sanghyun/github/pypsa_alternative
streamlit run utils/config_editor.py
```

## Features

### 📁 File Operations
- **Load Config**: Select and load any Excel config file from the `config/` directory
- **Save Config**: Save changes back to the current file
- **Export**: Export configuration to a new file with a different name

### 📊 Sheet Categories

The editor organizes configuration sheets into categories:

#### 1. Core Config
- `carrier_mapping`: Map original carrier names to standardized names
- `generator_attributes`: Set p_min_pu, p_max_pu, ramp limits, capacity factors
- `storage_unit_attributes`: Configure storage unit parameters
- `global_constraints`: Set global optimization constraints

#### 2. Regional Aggregation
- `regional_aggregation`: Main regional settings
- `lines_config`: Line aggregation rules
- `links_config`: Link aggregation rules
- `generator_region_aggregator_rules`: How to aggregate static generator attributes
- `generator_t_aggregator_rules`: How to aggregate time-series data

#### 3. Data Tables
- `province_mapping`: Short ↔ Official province name mapping
- `province_demand`: Regional demand data

#### 4. Other
- All other configuration sheets in the file

### ✏️ Editing Features

- **Add Row**: Add a new row to any table
- **Delete Row**: Remove the last row from any table
- **Inline Editing**: Click any cell to edit values directly
- **Dynamic Rows**: Add/remove rows as needed
- **Real-time Validation**: See changes immediately

### 💡 Quick Add Buttons

For missing data sheets, use the quick add buttons:
- "➕ Add Province Mapping Sheet" - Creates province mapping template
- "➕ Add Province Demand Sheet" - Creates province demand template

## Tips

1. **Always save your work**: Click "💾 Save Config" before closing
2. **Use Export for backups**: Export to a new file before making major changes
3. **Watch the status indicator**: Shows if you have unsaved changes (⚠️)
4. **Expand sheets**: Click on any sheet expander to view and edit

## Configuration Examples

### Generator Attributes

For realistic generator behavior:

| carriers | p_min_pu | p_max_pu | ramp_limit_up | ramp_limit_down | min_cf | max_cf |
|----------|----------|----------|---------------|-----------------|--------|--------|
| nuclear  | 0.70     | 1.0      | 0.05          | 0.05            | 0.85   | 0.95   |
| coal     | 0.40     | 1.0      | 0.10          | 0.10            | 0.50   | 0.80   |
| gas      | 0.20     | 1.0      | 0.30          | 0.30            | 0.10   | 0.60   |
| hydro    | 0.00     | 1.0      | 1.00          | 1.00            | 0.00   | 1.00   |

### Province Mapping

| short | official |
|-------|----------|
| 강원  | 강원특별자치도 |
| 경기  | 경기도 |
| 서울  | 서울특별시 |

## Troubleshooting

**"Config directory not found!"**
- Make sure you're running from the project root directory
- Check that `config/` directory exists

**"Error loading file"**
- Ensure the Excel file is not open in another program
- Check file permissions

**"Error saving file"**
- Close the Excel file if it's open elsewhere
- Check you have write permissions

## Security Note

This tool modifies Excel files directly. Always:
- Keep backups of your configuration files
- Test changes in a copy before modifying production configs
- Use version control (git) to track changes
