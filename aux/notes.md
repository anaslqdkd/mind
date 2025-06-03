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

