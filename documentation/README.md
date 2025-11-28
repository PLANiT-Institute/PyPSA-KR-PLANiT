# PyPSA Alternative - Complete Documentation

Welcome to the comprehensive documentation for the PyPSA Alternative project. This documentation provides detailed explanations of all components, processes, and configurations.

## Documentation Structure

This documentation is organized into four main sections:

### 1. [Main Scripts Documentation](01_MAIN_SCRIPTS.md)

Comprehensive guide to the three main entry point scripts that run the analysis.

**Contents:**
- Overview of aggregation levels (single-node, province, group)
- Detailed execution flow for each script
- Configuration requirements
- When to use each script
- Key differences and features
- Example outputs and visualizations

**Start here if you:**
- Want to understand what each main script does
- Need to choose which script to use for your analysis
- Are running the project for the first time
- Want to understand the overall analysis workflow

---

### 2. [Library Modules Documentation](02_LIBRARY_MODULES.md)

In-depth documentation of all library modules in the `libs/` folder.

**Contents:**
- Detailed function signatures and parameters
- Module purposes and responsibilities
- Input/output specifications
- Code examples and usage patterns
- Data flow between modules
- Special considerations and gotchas

**Modules Covered:**
- config.py - Configuration management
- data_loader.py - Network and data loading
- temporal_data.py - Time-series data application
- carrier_standardization.py - Carrier name mapping
- component_attributes.py - Operational parameters
- cc_merger.py - Combined cycle generator merging
- generator_p_set.py - Fixed dispatch profiles
- energy_constraints.py - Capacity factor constraints
- aggregators.py - Generator aggregation by carrier/region
- region_aggregator.py - Network spatial aggregation
- resample.py - Temporal resampling
- visualization.py - Result plotting
- bus_mapper.py - Bus name utilities

**Start here if you:**
- Need to understand specific library functions
- Are developing new features or modifications
- Want to trace data transformations
- Need API reference for functions

---

### 3. [Process Flow Documentation](03_PROCESS_FLOW.md)

Complete explanation of the execution process, data flow, and decision logic.

**Contents:**
- Overall architecture and system components
- Data flow diagrams
- Step-by-step process explanation
- Decision trees for conditional logic
- Component interaction diagrams
- Error handling and common issues

**Key Topics:**
- Configuration loading process
- Network data loading and parsing
- Combined cycle merging logic
- Time-series data application
- Regional aggregation workflow
- Carrier standardization process
- Attribute configuration
- Temporal operations (limiting, resampling)
- Optimization preparation
- Result visualization

**Start here if you:**
- Want to understand the complete pipeline
- Need to debug issues in the workflow
- Are optimizing performance
- Want to add new processing steps
- Need to understand data transformations

---

### 4. [Configuration Guide](04_CONFIGURATION_GUIDE.md)

Comprehensive guide to configuring the project through Excel files.

**Contents:**
- Configuration file overview
- Required and optional sheets
- All configuration parameters explained
- Regional aggregation settings
- Temporal configuration options
- Configuration examples for common scenarios
- Best practices and recommendations
- Troubleshooting common configuration issues

**Configuration Sheets:**
- carrier_mapping - Carrier name standardization
- generator_attributes - Generator operational parameters
- storage_unit_attributes - Storage parameters
- file_paths - Data file locations
- regional_settings - Regional configuration
- cc_merge_rules - Combined cycle aggregation rules
- carrier_order - Visualization ordering
- regional_aggregation - Regional aggregation settings
- generator_region_agg_rules - Generator aggregation rules
- generator_t_aggregator_rules - Time-series aggregation
- lines_config - Transmission line aggregation
- links_config - HVDC link aggregation
- province_mapping - Province names and groups
- province_demand - Regional load distribution
- modelling_setting - Temporal parameters
- resample_rules - Attribute resampling rules

**Start here if you:**
- Need to create or modify configuration files
- Want to understand configuration options
- Are setting up a new analysis scenario
- Need to troubleshoot configuration errors
- Want configuration best practices

---

## Quick Start Guide

### For First-Time Users

1. **Read** [Main Scripts Documentation](01_MAIN_SCRIPTS.md) - Overview section
2. **Choose** your analysis level (single-node, province, or group)
3. **Review** [Configuration Guide](04_CONFIGURATION_GUIDE.md) - Your config file
4. **Run** the appropriate main script
5. **Refer to** [Process Flow Documentation](03_PROCESS_FLOW.md) if issues arise

### For Developers

1. **Understand** [Process Flow Documentation](03_PROCESS_FLOW.md) - Complete pipeline
2. **Study** [Library Modules Documentation](02_LIBRARY_MODULES.md) - Relevant modules
3. **Review** [Main Scripts Documentation](01_MAIN_SCRIPTS.md) - Integration points
4. **Configure** [Configuration Guide](04_CONFIGURATION_GUIDE.md) - Test scenarios

### For Configuration Changes

1. **Start with** [Configuration Guide](04_CONFIGURATION_GUIDE.md)
2. **Understand** [Process Flow Documentation](03_PROCESS_FLOW.md) - How config is used
3. **Refer to** [Library Modules Documentation](02_LIBRARY_MODULES.md) - Config parsing
4. **Test** using [Main Scripts Documentation](01_MAIN_SCRIPTS.md) - Validation

---

## Common Use Cases

### Use Case 1: Running a Basic Analysis

**Goal:** Run a simple national-level analysis

**Steps:**
1. Read: [Main Scripts](01_MAIN_SCRIPTS.md) → main_singlenode.py section
2. Configure: [Configuration Guide](04_CONFIGURATION_GUIDE.md) → config_single.xlsx
3. Run: `python main_singlenode.py`
4. Troubleshoot: [Process Flow](03_PROCESS_FLOW.md) → Error Handling

---

### Use Case 2: Provincial Analysis with Custom Aggregation

**Goal:** Analyze inter-provincial transmission with custom line aggregation rules

**Steps:**
1. Read: [Main Scripts](01_MAIN_SCRIPTS.md) → main_province.py section
2. Understand: [Process Flow](03_PROCESS_FLOW.md) → Regional Aggregation
3. Configure: [Configuration Guide](04_CONFIGURATION_GUIDE.md) → lines_config sheet
4. Reference: [Library Modules](02_LIBRARY_MODULES.md) → region_aggregator.py
5. Run: `python main_province.py`

---

### Use Case 3: Multi-Level Aggregation with Temporal Resampling

**Goal:** Analyze mainland vs. islands scenario with 4-hour resolution

**Steps:**
1. Read: [Main Scripts](01_MAIN_SCRIPTS.md) → main_group.py section
2. Understand: [Process Flow](03_PROCESS_FLOW.md) → Steps 7 (aggregation) and 13 (resampling)
3. Configure: [Configuration Guide](04_CONFIGURATION_GUIDE.md) → regional_aggregation and modelling_setting sheets
4. Reference: [Library Modules](02_LIBRARY_MODULES.md) → region_aggregator.py and resample.py
5. Run: `python main_group.py`

---

### Use Case 4: Custom Data Processing

**Goal:** Add new time-series attribute (e.g., emissions factor)

**Steps:**
1. Understand: [Process Flow](03_PROCESS_FLOW.md) → Steps 4-5 (data application)
2. Study: [Library Modules](02_LIBRARY_MODULES.md) → temporal_data.py
3. Modify: Data files to include new attribute
4. Configure: [Configuration Guide](04_CONFIGURATION_GUIDE.md) → Ensure status=TRUE for new data
5. Test: [Main Scripts](01_MAIN_SCRIPTS.md) → Verify loading

---

### Use Case 5: Debugging Optimization Failures

**Goal:** Resolve "infeasible" optimization status

**Steps:**
1. Review: [Process Flow](03_PROCESS_FLOW.md) → Error Handling section
2. Check: [Configuration Guide](04_CONFIGURATION_GUIDE.md) → Troubleshooting → Optimization Infeasible
3. Analyze: [Library Modules](02_LIBRARY_MODULES.md) → energy_constraints.py
4. Test: Modify configuration based on recommendations
5. Verify: [Main Scripts](01_MAIN_SCRIPTS.md) → Check optimization output

---

## Project Overview

### What is PyPSA Alternative?

PyPSA Alternative is a flexible energy system modeling framework for Korea, built on PyPSA (Python for Power System Analysis). It enables multi-scale power system analysis with support for:

- **Multiple aggregation levels:** Single-node, provincial (17 regions), or custom groupings
- **Flexible temporal resolution:** Hourly to daily snapshots with automatic resampling
- **Comprehensive data integration:** Monthly costs, hourly capacity factors, regional demand
- **Advanced network operations:** Combined cycle merging, generator aggregation, transmission modeling
- **Interactive visualization:** Plotly-based charts for generation, transmission flows, and storage

### Key Features

1. **Modular Architecture**
   - Separate configuration from code
   - Reusable library modules
   - Three main scripts for different aggregation levels

2. **Excel-Based Configuration**
   - No coding required for most changes
   - Human-readable configuration
   - Version control friendly

3. **Spatial Flexibility**
   - National → Provincial → Group aggregation
   - Configurable region definitions
   - Custom transmission aggregation rules

4. **Temporal Flexibility**
   - Snapshot limiting (analyze specific periods)
   - Temporal resampling (1-hour → 4-hour → daily)
   - Automatic attribute scaling

5. **Data Handling**
   - Supports Korean and English carrier names
   - Multiple aggregation levels (national/province/generator)
   - Time-series data from monthly to hourly

---

## Documentation Conventions

### Notation

- **`monospace`**: Code, filenames, function names
- **bold**: Important terms, emphasis
- *italic*: Variables, placeholders

### File Paths

All paths are relative to project root unless specified otherwise:
```
pypsa_alternative/
├── config/
├── data/
├── libs/
├── documentation/  ← You are here
└── main_*.py
```

### Code Examples

```python
# Inline comments explain specific lines
config = load_config('config/config.xlsx')  # Load configuration

# Example output shown below code
# Output: Configuration loaded successfully
```

### Dates

**Critical:** This project uses **day-first** date format (DD/MM/YYYY)

```
01/03/2024 = 1st March 2024 (NOT 3rd January)
```

---

## Getting Help

### Finding Information

1. **Search Documentation**
   - Use your IDE's search (Ctrl+Shift+F)
   - Search for function names, error messages, or concepts

2. **Check Related Sections**
   - Each document links to related documentation
   - Cross-references help navigate complex topics

3. **Review Examples**
   - Each document includes practical examples
   - Look for "Example:" sections

### Common Questions

**Q: Which main script should I use?**
→ [Main Scripts Documentation](01_MAIN_SCRIPTS.md) → Overview section

**Q: How do I configure regional aggregation?**
→ [Configuration Guide](04_CONFIGURATION_GUIDE.md) → Regional Aggregation Configuration

**Q: What does function X do?**
→ [Library Modules Documentation](02_LIBRARY_MODULES.md) → Find the module

**Q: Why is my optimization failing?**
→ [Process Flow Documentation](03_PROCESS_FLOW.md) → Error Handling

**Q: How does the pipeline work?**
→ [Process Flow Documentation](03_PROCESS_FLOW.md) → Overall Architecture

**Q: What are the Excel sheet names and their purposes?**
→ [Configuration Guide](04_CONFIGURATION_GUIDE.md) → Common Configuration Sheets

---

## Contributing to Documentation

### Documentation Standards

- **Clear hierarchy:** Use headers (##, ###, ####) consistently
- **Concrete examples:** Provide code and data examples
- **Cross-references:** Link to related sections
- **Completeness:** Cover parameters, returns, and edge cases
- **Accuracy:** Test all code examples

### Updating Documentation

When modifying code:
1. Update function docstrings
2. Update relevant sections in library modules documentation
3. Update process flow if workflow changes
4. Update configuration guide if config changes
5. Update examples in main scripts documentation

---

## Version History

### Current Version: 1.0 (November 2025)

**Documentation:**
- Complete rewrite of all documentation
- Four comprehensive documents
- Process flow diagrams
- Configuration guide with all sheets
- Troubleshooting sections
- Examples for common use cases

**Previous Documentation:**
- Located in old `doc/` folder (removed)
- Fragmented across multiple files
- Incomplete coverage

---

## License and Attribution

This documentation is part of the PyPSA Alternative project.

For the PyPSA core library:
- PyPSA Documentation: https://pypsa.readthedocs.io/
- PyPSA Repository: https://github.com/PyPSA/PyPSA

---

## Quick Reference

### Main Scripts

| Script | Purpose | Config File |
|--------|---------|-------------|
| main_singlenode.py | National analysis | config_single.xlsx |
| main_province.py | Provincial analysis | config_province.xlsx |
| main_group.py | Group analysis | config_group.xlsx |

### Key Library Modules

| Module | Primary Function |
|--------|-----------------|
| config.py | Load configuration |
| data_loader.py | Load network and data |
| temporal_data.py | Apply time-series data |
| carrier_standardization.py | Standardize carrier names |
| region_aggregator.py | Spatial aggregation |
| resample.py | Temporal aggregation |
| visualization.py | Create charts |

### Configuration Essentials

| Sheet | Purpose |
|-------|---------|
| carrier_mapping | Korean → English names |
| generator_attributes | Operational parameters |
| file_paths | Data locations |
| regional_aggregation | Spatial settings |
| modelling_setting | Temporal settings |
| lines_config | Transmission aggregation |

### Execution Flow

1. Load config → 2. Load network → 3. Merge CC → 4. Apply data → 5. Aggregate (optional) → 6. Standardize carriers → 7. Set attributes → 8. Apply constraints → 9. Resample (optional) → 10. Optimize → 11. Visualize

---

## Next Steps

Choose your path:

- **New User?** → Start with [Main Scripts Documentation](01_MAIN_SCRIPTS.md)
- **Configuring?** → Go to [Configuration Guide](04_CONFIGURATION_GUIDE.md)
- **Developing?** → Read [Library Modules Documentation](02_LIBRARY_MODULES.md)
- **Debugging?** → Check [Process Flow Documentation](03_PROCESS_FLOW.md)

---

**Last Updated:** November 2025

**Documentation Version:** 1.0

**Project:** PyPSA Alternative - Korea Energy System Model
