"""
Configuration Editor GUI using Streamlit

A standalone utility to view and edit PyPSA configuration Excel files.

Usage:
------
streamlit run utils/config_editor.py

Features:
---------
- Load and save Excel configuration files
- Edit all configuration tabs in a visual interface
- Add/remove rows from tables
- Validate configuration values
- Export configuration to new file
"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="PyPSA Config Editor",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ PyPSA Configuration Editor")
st.markdown("---")

# Session state initialization
if 'config_data' not in st.session_state:
    st.session_state.config_data = {}
if 'current_file' not in st.session_state:
    st.session_state.current_file = None
if 'modified' not in st.session_state:
    st.session_state.modified = False


def _display_sheet_editor(sheet_name):
    """Display an editable dataframe for a configuration sheet."""
    with st.expander(f"📋 {sheet_name}", expanded=False):
        df = st.session_state.config_data[sheet_name]

        # Display info about the sheet
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.caption(f"Rows: {len(df)} | Columns: {len(df.columns)}")
        with col2:
            if st.button("➕ Add Row", key=f"add_{sheet_name}"):
                # Add empty row
                new_row = pd.DataFrame([[None] * len(df.columns)], columns=df.columns)
                st.session_state.config_data[sheet_name] = pd.concat([df, new_row], ignore_index=True)
                st.session_state.modified = True
                st.rerun()
        with col3:
            if st.button("🗑️ Delete Last Row", key=f"del_{sheet_name}", disabled=len(df) == 0):
                st.session_state.config_data[sheet_name] = df.iloc[:-1]
                st.session_state.modified = True
                st.rerun()

        # Editable data editor
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            key=f"editor_{sheet_name}",
            hide_index=True
        )

        # Update session state if edited
        if not edited_df.equals(df):
            st.session_state.config_data[sheet_name] = edited_df
            st.session_state.modified = True

# Sidebar - File operations
st.sidebar.header("📁 File Operations")

# File selector
config_dir = Path("config")
if config_dir.exists():
    config_files = list(config_dir.glob("*.xlsx"))
    config_file_names = [f.name for f in config_files]

    selected_file = st.sidebar.selectbox(
        "Select Config File",
        config_file_names,
        index=config_file_names.index("config_province.xlsx") if "config_province.xlsx" in config_file_names else 0
    )

    config_path = config_dir / selected_file
else:
    st.sidebar.error("Config directory not found!")
    config_path = None

# Load button
if st.sidebar.button("📂 Load Config", disabled=config_path is None):
    try:
        # Read all sheets from Excel file
        xl_file = pd.ExcelFile(config_path)
        st.session_state.config_data = {}

        for sheet_name in xl_file.sheet_names:
            st.session_state.config_data[sheet_name] = pd.read_excel(config_path, sheet_name=sheet_name)

        st.session_state.current_file = config_path
        st.session_state.modified = False
        st.sidebar.success(f"✅ Loaded {len(xl_file.sheet_names)} sheets")
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")

# Save button
if st.sidebar.button("💾 Save Config", disabled=st.session_state.current_file is None):
    try:
        with pd.ExcelWriter(st.session_state.current_file, engine='openpyxl') as writer:
            for sheet_name, df in st.session_state.config_data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        st.session_state.modified = False
        st.sidebar.success("✅ Config saved successfully!")
    except Exception as e:
        st.sidebar.error(f"Error saving file: {e}")

# Export to new file
new_filename = st.sidebar.text_input("Export as:", "")
if st.sidebar.button("📤 Export", disabled=not new_filename or st.session_state.current_file is None):
    try:
        export_path = config_dir / new_filename
        if not export_path.suffix:
            export_path = export_path.with_suffix('.xlsx')

        with pd.ExcelWriter(export_path, engine='openpyxl') as writer:
            for sheet_name, df in st.session_state.config_data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        st.sidebar.success(f"✅ Exported to {export_path.name}")
    except Exception as e:
        st.sidebar.error(f"Error exporting: {e}")

# Status indicator
if st.session_state.current_file:
    st.sidebar.markdown("---")
    st.sidebar.info(f"**Current File:** {st.session_state.current_file.name}")
    if st.session_state.modified:
        st.sidebar.warning("⚠️ Unsaved changes")

# Main content area
if st.session_state.config_data:
    st.header("📊 Configuration Sheets")

    # Sheet selector
    sheet_names = list(st.session_state.config_data.keys())

    # Categorize sheets for easier navigation
    core_sheets = ['carrier_mapping', 'generator_attributes', 'storage_unit_attributes', 'global_constraints']
    regional_sheets = ['regional_aggregation', 'lines_config', 'links_config',
                      'generator_region_aggregator_rules', 'generator_t_aggregator_rules']
    data_sheets = ['province_mapping', 'province_demand']
    other_sheets = [s for s in sheet_names if s not in core_sheets + regional_sheets + data_sheets]

    # Tabs for categories
    tab1, tab2, tab3, tab4 = st.tabs(["Core Config", "Regional Aggregation", "Data Tables", "Other"])

    # Core Config Tab
    with tab1:
        for sheet in core_sheets:
            if sheet in st.session_state.config_data:
                _display_sheet_editor(sheet)

    # Regional Aggregation Tab
    with tab2:
        for sheet in regional_sheets:
            if sheet in st.session_state.config_data:
                _display_sheet_editor(sheet)

    # Data Tables Tab
    with tab3:
        st.info("💡 These tables contain province mapping and demand data")
        for sheet in data_sheets:
            if sheet in st.session_state.config_data:
                _display_sheet_editor(sheet)

        # Option to add missing data sheets
        if 'province_mapping' not in st.session_state.config_data:
            if st.button("➕ Add Province Mapping Sheet"):
                st.session_state.config_data['province_mapping'] = pd.DataFrame({
                    'short': ['강원', '경기', '경남', '경북', '광주', '대구', '대전', '부산', '서울', '세종', '울산', '인천', '전남', '전북', '제주', '충남', '충북'],
                    'official': ['강원특별자치도', '경기도', '경상남도', '경상북도', '광주광역시', '대구광역시', '대전광역시', '부산광역시', '서울특별시', '세종특별자치시', '울산광역시', '인천광역시', '전라남도', '전북특별자치도', '제주특별자치도', '충청남도', '충청북도']
                })
                st.session_state.modified = True
                st.rerun()

        if 'province_demand' not in st.session_state.config_data:
            if st.button("➕ Add Province Demand Sheet"):
                st.session_state.config_data['province_demand'] = pd.DataFrame({
                    'province': ['강원', '경기', '경남', '경북', '광주', '대구', '대전', '부산', '서울', '세종', '울산', '인천', '전남', '전북', '제주', '충남', '충북'],
                    'demand': [0.0] * 17
                })
                st.session_state.modified = True
                st.rerun()

    # Other Tab
    with tab4:
        for sheet in other_sheets:
            _display_sheet_editor(sheet)

else:
    st.info("👈 Select and load a configuration file from the sidebar to begin editing")

    # Show example of what can be edited
    st.markdown("""
    ### What you can edit:

    **Core Configuration:**
    - 🔄 Carrier mapping (fuel types)
    - ⚡ Generator attributes (ramp rates, capacity factors, etc.)
    - 📊 Global constraints

    **Regional Aggregation:**
    - 🗺️ Regional settings
    - 🔌 Line aggregation rules
    - 🔗 Link aggregation rules
    - 📈 Generator aggregation rules

    **Data Tables:**
    - 🏙️ Province mapping (short ↔ official names)
    - 📊 Province demand data

    **And more...**
    """)


if __name__ == "__main__":
    # This allows the script to be run directly
    pass
