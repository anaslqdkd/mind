Each problem's instance require three datafiles :

1. constraint description file
2. permeability information data
3. economic informations data

ex:
/005 Arkema_1.dat
/038 Arkema_1_eco.dat
/086 Arkema_1_fix_perm.dat


Arkema_1.data


---

**StartPage**
- Lets the user configure initial process parameters:
  - Number of membranes (Spinbox)
  - Several boolean options (Checkbuttons): uniform pressure, vacuum pump, variable permeability, fixing variables
  - Radiobuttons for data file selection (disabled by default)
- Has a "Next" button (with arrow image) to proceed to the next page

---

**MainPage**
- Lets the user set bounds for process parameters:
  - Upper/lower bounds for area (per membrane)
  - Upper bounds for "acell" (per membrane)
- Has navigation buttons:
  - "Return" (with arrow image) to go back
  - "Solve" button to start the solving process

---

**ParameterPage**
- Lets the user set advanced/solver parameters:
  - Seeds, max trials, max no improve, number of points, pressure ratio, population size, number of generations (all as Entry fields)
- Has a "Validate" button to confirm and apply changes
- Shows error/info dialogs for validation

---

**GuidePage**
- Displays a help/welcome guide:
  - Step-by-step instructions for using the application (as Labels)

---

**InfosPage**
- Displays project information:
  - Version, project description, collaborators
  - Logos/images of collaborators

---

**SolveButton**
- Not a page, but a logic/utility class for:
  - Storing and validating process parameters
  - Checking bounds and input validity
  - Showing error/info dialogs

---

**ThreadSolver**
- Not a page, but a thread class for running the solver in the background

---

**At first, you must fill in:**  
- Process data (from .dat file)
- Number of membranes and their bounds/types
- Algorithm/solver parameters
- Option flags (booleans)
- (Optionally) a fixing/mask file


voir pour parallaliser l'algo


## Idées sur l'implémentation
### 1. Wizard/Stepper Layout

Break the process into logical steps, each with its own screen. Example steps:

1. **General Settings**  
   - Project name, output directory, random seeds, etc.

2. **System Parameters**  
   - Number of membranes, number of components, pressure settings, etc.

3. **Component Details**  
   - For each component (dynamically generated based on previous step):  
     - Name, molar mass, bounds, etc.

4. **Membrane Parameters**  
   - For each membrane:  
     - Area bounds, acell, type, etc.

5. **Economic Parameters**  
   - Cost coefficients, operation time, etc.

6. **Permeability Data**  
   - For each membrane/component:  
     - Permeability values, bounds, etc.

7. **Optional Mask File**  
   - Enable/disable mask, upload or generate mask, etc.

8. **Review & Generate**  
   - Show a summary, allow editing, then generate files.

### 2. Dynamic Forms

- Use **dynamic fields**: When the user sets "number of components" to 3, show 3 input rows for molar mass, names, etc.
- For lists (e.g., bounds per membrane), use repeatable form sections or tables.
- For booleans, use checkboxes or toggles.
- For file paths, use file pickers.

### 3. Validation & Guidance

- Validate input at each step (e.g., correct number of values, numeric ranges).
- Show tooltips or help texts for each field (explain units, expected values).
- Disable "Next" until current step is valid.

### 5. Output

- At the end, generate all files and show download links or save to disk.
- Optionally, allow exporting/importing a project as a JSON for later editing.


## Sur le deployement
Pour des raisons légales il faut acheter une licence, 3 dollars par ans
Mais sinon on peut avec avec PyInstaller:

### **1. Prepare Your App**

- Make sure your main Python script (e.g., `main.py`) runs correctly.

---

### **2. Install PyInstaller**

PyInstaller bundles your Python app and all dependencies into a single folder or executable.

```sh
pip install pyinstaller
```

---

### **3. Bundle Your App**

Run this command in your project directory:

```sh
pyinstaller --onefile main.py
```

- This creates a single executable in the `dist/` folder.

---

### **4. Test the Executable**

Go to the `dist/` folder and run your app:

```sh
cd dist
./main
```

Make sure it works as expected.

---

### **5. Create a Tarball (Installer)**

From the `dist/` directory, package your executable:

```sh
tar czvf myapp.tar.gz main
```

**Summary:**  
- With permissive/commercial licenses: users cannot modify your code unless you provide it.
- With GPL: you must provide the source code, so users can modify it.  
- The tarball itself does not allow code modification unless it contains the source.

private git repository
<!-- TODO: update the doc with the info on deployement -->



MainWindow (QMainWindow)
 └── CentralWidget (QWidget)
      └── QHBoxLayout (mainHorizontalLayout)
           ├── Sidebar (QWidget)
           │     └── QVBoxLayout
           │           ├── QLabel (Logo or Title)
           │           ├── QListWidget or QTreeWidget (Navigation or Progress)
           │           └── Stretch (optional)
           └── MainArea (QWidget)
                 └── QVBoxLayout
                       ├── QStackedWidget (Form Pages)
                       └── Navigation Buttons (QWidget + QHBoxLayout)



# On building parameters

## in config.ini
num_membranes = 2

ub_area = [5 , 5]
lb_area = [0.1, 0.1]
ub_acell = [0.1, 0.1]


3 boolean values
uniform_pup = False
vp = false
variable_perm = False

for the path files, a filechooser, or default value


fixing var = True -> generate fixing var config


# pour demain
fix value in all params
beg writing in files, file attribute in files
add the versions in the app

| Parameter         | Section     | Optional? | Dependency/Condition                |
|-------------------|-------------|-----------|-------------------------------------|
| pressure_ratio    | tuning      | No        |                                     |
| epsilon           | tuning      | No        |                                     |
| seed1             | tuning      | No        |                                     |
| seed2             | tuning      | No        |                                     |
| iteration         | tuning      | No        |                                     |
| max_no_improve    | tuning      | No        |                                     |
| max_trials        | tuning      | No        |                                     |
| pop_size          | tuning      | No        |                                     |
| generations       | tuning      | No        |                                     |
| n1_element        | tuning      | No        |                                     |
| data_dir          | instance    | No        |                                     |
| log_dir           | instance    | No        |                                     |
| num_membranes     | instance    | No        |                                     |
| ub_area           | instance    | No        |                                     |
| lb_area           | instance    | No        |                                     |
| ub_acell          | instance    | No        |                                     |
| fixing_var        | instance    | No        |                                     |
| fname             | instance    | No        |                                     |
| fname_perm        | instance    | No        |                                     |
| fname_eco         | instance    | No        |                                     |
| fname_mask        | instance    | Yes       | Required if fixing_var = true       |
| prototype_data    | instance    | Yes       | Only if prototype individuals used  |
| uniform_pup       | instance    | No        |                                     |
| vp                | instance    | No        |                                     |
| variable_perm     | instance    | No        |                                     |

**ub_area**  
- **Description:** Upper bound(s) for the area of each membrane in the system.  
- **Type:** List of floats/ints, one per membrane (e.g., `[5, 5]` for two membranes).  
- **Purpose:** Sets the maximum allowed area for each membrane during optimization.

---

**lb_area**  
- **Description:** Lower bound(s) for the area of each membrane in the system.  
- **Type:** List of floats/ints, one per membrane (e.g., `[0.1, 0.1]`).  
- **Purpose:** Sets the minimum allowed area for each membrane during optimization.

---

**ub_acell**  
- **Description:** Upper bound(s) for the area of a single cell (subdivision) within each membrane.  
- **Type:** List of floats/ints, one per membrane (e.g., `[0.1, 0.1]`).  
- **Purpose:** Sets the maximum allowed area for a single cell when discretizing the membrane area for numerical modeling.

membranes, up to 3


# Parameters


## config
**Parameters:**
- pressure_ratio
- epsilon
- seed1
- seed2
- iteration
- max_no_improve
- max_trials
- pop_size
- generations
- n1_element

---

### `[instance]` Section

These are set and used in:
- `launcher.py` (`data_instance()`, `generate_configuration()`, `load_configuration()`)
- Used to build the model in `builder.py`, `gas.py`, etc.

**Parameters:**
- data_dir
- log_dir
- num_membranes
- ub_area
- lb_area
- ub_acell
- fixing_var
- fname
- fname_perm
- fname_eco
- fname_mask (optional, only if fixing_var is true)
- prototype_data (optional, for population algorithm)
- uniform_pup
- vp
- variable_perm






## data

| Parameter Name         | Indexed By         | Description                        |
|-----------------------|--------------------|------------------------------------|
| ub_press_up           | scalar             | Upper bound for pressure up        |
| lb_press_up           | scalar             | Lower bound for pressure up        |
| ub_area               | states             | Upper bound for area               |
| lb_area               | states             | Lower bound for area               |
| ub_acell              | states             | Upper bound for cell area          |
| lb_acell              | states             | Lower bound for cell area          |
| ub_perc_prod          | components         | Upper bound for product purity     |
| lb_perc_prod          | components         | Lower bound for product purity     |
| ub_perc_waste         | components         | Upper bound for waste purity       |
| lb_perc_waste         | components         | Lower bound for waste purity       |
| ub_feed_tot           | scalar             | Upper bound for total feed         |
| pressure_in           | scalar             | Feed pressure                      |
| pressure_prod         | scalar             | Product pressure                   |
| pressure_down         | states             | Downstream pressure                |
| ub_flow_prod          | scalar             | Upper bound for product flow       |
| lb_flow_prod          | scalar             | Lower bound for product flow       |
| ub_flow_waste         | scalar             | Upper bound for waste flow         |
| lb_flow_waste         | scalar             | Lower bound for waste flow         |
| ub_purity             | components         | Upper bound for purity             |
| lb_purity             | components         | Lower bound for purity             |
| ub_recovery           | components         | Upper bound for recovery           |
| lb_recovery           | components         | Lower bound for recovery           |
| ub_stage              | scalar             | Upper bound for stage              |
| lb_stage              | scalar             | Lower bound for stage              |
| ub_splitRET_frac_full | states x states    | Upper bound for split RET fraction |
| lb_splitRET_frac_full | states x states    | Lower bound for split RET fraction |
| ub_splitPERM_frac_full| states x states    | Upper bound for split PERM fraction|
| lb_splitPERM_frac_full| states x states    | Lower bound for split PERM fraction|
| molarmass             | components         | Molar mass per component           |
| final_product         | scalar             | Final product index/name           |


# perm file

### For **fixed permeability** files (`parser_fixed_permeability_data`):

- `nb_gas`
- `Permeability`
- `thickness`
- `mem_product`
- `mem_type` (optional, for mapping membrane index to type)

### For **variable permeability** (tradeoff) files (`parser_variable_permeability_data`):

- `Robeson_multi`
- `Robeson_power`
- `alpha_ub_bounds` (parsed as `ub_alpha`)
- `alpha_lb_bounds` (parsed as `lb_alpha`)
- `lb_permeability`
- `ub_permeability`
- `thickness`
- `mem_product`
- `mem_type` (optional, for mapping membrane index to type)

