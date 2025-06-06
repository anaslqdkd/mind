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
