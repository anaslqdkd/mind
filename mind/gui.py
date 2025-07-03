""" Gui interface.

Build Mind project's graphical user interface.
"""

import os
import logging
from threading import Thread
from threading import Event
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog

from mind.builder import Configuration, build_model
from mind.interfaceSolver import SolverObject
from mind.util import generate_absolute_path
from mind.solve import GlobalOptimisation

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler('log.txt')
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)

# background = '#41B77F'
# text_color = 'white'

background = '#F0D31D'
background = '#CEB61E'
text_color = 'black'
error_color = 'red'
param_size = 16


class ThreadSolver(Thread):
    """Thread performing solver resolution.
    Attributes:
        master (tk.TK): Top parent application's window object
    """

    def __init__(self, win):
        Thread.__init__(self)
        self.master = win  # on mémorise une référence sur la fenêtre

    def run(self):
        """Execute an algorithm on `PYOMO` 's model."""
        # code à executer par le thread solver
        # build solver instance
        # TODO: solver definition can be put in another scope
        try:
            frame = self.master.solveButton

            # path to knitro is in my PYTHONPATH
            frame.optsolver = SolverObject()
            frame.optsolver.solver_factory('knitro')
            # frame.optsolver.the_solver.options['threads'] = 1
            frame.optsolver.the_solver.options['maxtime_cpu'] = 180
            frame.log = generate_absolute_path() + "log" + os.path.sep
            # print(self.log_directory)

            while not self.master.leave:
                # self.master.event.wait()
                frame.my_solver = GlobalOptimisation(frame.optsolver, frame.log)

                # deactivate obj function
                # frame.modelisation.instance.obj.deactivate()
                # frame.modelisation.instance.preprocess()

                self.master.solver_launched = True

                if frame.algorithm == "multistart":
                    frame.my_solver.multistart(frame.modelisation,
                                               frame.nb_points_randomized,
                                               frame.seed1)

                elif frame.algorithm == "mbh":
                    frame.my_solver.mbh(frame.modelisation, frame.max_trials,
                                        frame.max_no_improve, frame.seed1,
                                        frame.seed2, False)

                elif frame.algorithm == "genetic_method":
                    frame.my_solver.launching_evolutionary_algorithm(
                        frame.modelisation, frame.pop_size,
                        frame.nb_generations)

                elif frame.algorithm == "population_method":
                    frame.instance_file = None
                    frame.n1_element = None
                    assert False
                    frame.my_solver.launching_modified_evolutionary_algorithm(
                        frame.modelisation, frame.instance_file,
                        frame.n1_element)

                else:
                    frame.my_solver.global_optimisation_algorithm(
                        frame.modelisation, frame.max_trials,
                        frame.max_no_improve, frame.nb_points_randomized,
                        frame.seed1, frame.seed2)

                frame.my_solver.print_statistics()
                logger.info("status = {}".format(frame.my_solver.feasible))
                print()
                # my_solver.modelisation.instance.pprint("file.log")
                # my_solver.modelisation.instance.write("file.nl")

                # plotting solver optimization result if it exists
                # if frame.my_solver.feasible:
                #     frame.my_solver.visualise_solutions(
                #         frame.my_solver.modelisation.instance,
                #         frame.my_solver.modelisation.parameter)

                self.master.event_generate("<<thread_fini>>")
                self.master.event.clear()
                self.master.thread_waiting = True
                self.master.event.wait()
                self.master.thread_waiting = False

        except Exception:
            self.master.close_window()
            # raise


class StartPage(tk.Frame):

    def __init__(self, window):
        tk.Frame.__init__(self, window)
        self.master = window
        self.config(bg=background)

    def boolean_widget(self, frame, value_widget, text, row, col):
        widget = tk.Label(frame,
                          text=text,
                          font=("Helvetica", param_size),
                          bg=background,
                          fg=text_color)

        widget.grid(row=row, column=col, sticky=tk.W)

        widget = tk.Checkbutton(frame,
                                variable=value_widget,
                                onvalue=1,
                                offvalue=0,
                                bg=background,
                                bd=0,
                                highlightthickness=0)

        widget.grid(row=row, column=col + 1, sticky=tk.W)

    def parameter_dashboard(self, my_param_frame):
        row = 0
        col = 0
        num_membranes = tk.Label(my_param_frame,
                                 text="Number of membranes",
                                 font=("Helvetica", param_size),
                                 bg=background,
                                 fg=text_color)
        num_membranes.grid(row=row, column=col, sticky=tk.W)

        self.master.num_membranes = tk.IntVar()
        self.master.num_membranes.set(2)
        self.master.nb_spinbox = tk.Spinbox(
            my_param_frame,
            from_=1,
            to=5,
            width=5,
            textvariable=self.master.num_membranes)
        self.master.nb_spinbox.grid(row=row, column=col + 1, sticky=tk.W)

        row += 1

        # checkbutton
        self.master.uniform_pup_value = tk.IntVar()
        self.master.uniform_pup_value.set(1)
        self.boolean_widget(my_param_frame, self.master.uniform_pup_value,
                            "Is pressure uniform ? ", row, col)

        row += 1
        # checkbutton
        self.master.vp_value = tk.IntVar()
        self.master.vp_value.set(1)
        self.boolean_widget(my_param_frame, self.master.vp_value,
                            "Is there a vacuum pump ? ", row, col)

        row += 1
        # checkbutton
        self.master.perm_variable_value = tk.IntVar()
        # self.perm_variable_value.set(1)
        self.boolean_widget(my_param_frame, self.master.perm_variable_value,
                            "Are permeability variable ? ", row, col)

        row += 1
        # checkbutton
        self.master.is_fixing_var = tk.IntVar()
        self.boolean_widget(my_param_frame, self.master.is_fixing_var,
                            "are some variables fixed ? ", row, col)

        row += 1
        blank = tk.Label(my_param_frame,
                         text="",
                         font=("Helvetica", param_size),
                         bg=background,
                         fg=text_color)
        blank.grid(row=row, column=col, sticky=tk.W)

        row += 1
        # radiobutton
        file_data = tk.Label(my_param_frame,
                             text="Process constraint data",
                             font=("Helvetica", param_size),
                             bg=background,
                             fg=text_color)
        file_data.grid(row=row, column=col, sticky=tk.W)

        self.master.datafiles_active_button = tk.Radiobutton(
            my_param_frame,
            variable=self.master.datafiles_active,
            bg=background,
            state=tk.DISABLED,
            value=1,
            bd=0,
            highlightthickness=0)

        self.master.datafiles_active_button.grid(row=row,
                                                 column=col + 1,
                                                 sticky=tk.W + tk.S)

        row += 1
        perm_dataFiles = tk.Label(my_param_frame,
                                  text="Process permeability data",
                                  font=("Helvetica", param_size),
                                  bg=background,
                                  fg=text_color)
        perm_dataFiles.grid(row=row, column=col, sticky=tk.W)

        self.master.datafiles_active_perm_button = tk.Radiobutton(
            my_param_frame,
            variable=self.master.perm_datafiles_active,
            bg=background,
            selectcolor='white',
            state=tk.DISABLED,
            value=1,
            bd=0,
            highlightthickness=0)

        self.master.datafiles_active_perm_button.grid(row=row,
                                                      column=col + 1,
                                                      sticky=tk.W + tk.S)

        row += 1
        eco_dataFiles = tk.Label(my_param_frame,
                                 text="Process economic data",
                                 font=("Helvetica", param_size),
                                 bg=background,
                                 fg=text_color)
        eco_dataFiles.grid(row=row, column=col, sticky=tk.W)

        self.master.datafiles_active_eco_button = tk.Radiobutton(
            my_param_frame,
            variable=self.master.eco_datafiles_active,
            bg=background,
            selectcolor='white',
            state=tk.DISABLED,
            value=1,
            bd=0,
            highlightthickness=0)

        self.master.datafiles_active_eco_button.grid(row=row,
                                                     column=col + 1,
                                                     sticky=tk.W + tk.S)

    def dashboard(self):
        row = 0
        col = 0
        canvas = tk.Canvas(self,
                           width=300,
                           height=300,
                           background=background,
                           bd=0,
                           highlightthickness=0)
        canvas.create_image(150, 150, image=self.master.img)
        canvas.grid(row=row, column=col, sticky=tk.E, pady=50)

        my_frame = tk.Frame(self, bg=background)
        my_frame.grid(row=row, column=col + 1, sticky=tk.W, pady=70)

        # titre Parameters
        label_title = tk.Label(my_frame,
                               text="Process configuration",
                               font=("Helvetica", 36),
                               bg=background,
                               fg=text_color)
        label_title.pack()

        my_param_frame = tk.Frame(my_frame, bg=background)
        my_param_frame.pack(padx=50, pady=5)

        self.parameter_dashboard(my_param_frame)

        arrow_frame = tk.Frame(self, bg=background)
        arrow_frame.grid(row=row + 1, column=col + 1, sticky=tk.W)

        label_next = tk.Label(arrow_frame,
                              text="click on next",
                              font=("Helvetica", 16),
                              bg=background,
                              fg=text_color)

        label_next.pack()

        # Arrow button
        tk.Button(arrow_frame,
                  relief=tk.GROOVE,
                  font=("Helvetica", param_size),
                  bg=background,
                  fg=text_color,
                  bd=0,
                  highlightthickness=0,
                  image=self.master.next_arrow,
                  compound=tk.LEFT,
                  command=self.master.redirect_second_page).pack(side=tk.BOTTOM,
                                                                 padx=100,
                                                                 pady=5,
                                                                 fill=tk.X)


class MainPage(tk.Frame):

    def __init__(self, window):
        tk.Frame.__init__(self, window)
        self.master = window
        self.config(bg=background)

    def split_widget(self, my_param_frame, entry_widget, value_widget,
                     default_val, row, col):
        frame = tk.Frame(my_param_frame, bg=background)
        frame.grid(row=row, column=col + 1, sticky=tk.W, pady=30)

        for i in range(self.master.num_membranes.get() - 1):
            value_widget.append(tk.DoubleVar())
            value_widget[i].set(str(default_val))

            entry_widget.append(
                tk.Entry(frame, width=5, textvariable=value_widget[i]))

            entry_widget[i].pack(side=tk.RIGHT)
            space = tk.Label(frame,
                             text=" ",
                             font=("Helvetica", param_size),
                             bg=background,
                             fg=text_color)
            space.pack(side=tk.RIGHT)

        index = self.master.num_membranes.get() - 1
        value_widget.append(tk.DoubleVar())
        value_widget[index].set(str(default_val))

        entry_widget.append(
            tk.Entry(frame, width=5, textvariable=value_widget[index]))
        entry_widget[index].pack(side=tk.RIGHT)

    def parameter_dashboard(self, my_param_frame):
        row = 0
        col = 0

        ub_area_ = tk.Label(my_param_frame,
                            text="Ub area",
                            font=("Helvetica", param_size),
                            bg=background,
                            fg=text_color)

        ub_area_.grid(row=row, column=col, sticky=tk.W)
        self.master.ub_area_value_ = []
        self.master.ub_area_entry_ = []

        self.split_widget(my_param_frame, self.master.ub_area_entry_,
                          self.master.ub_area_value_, 1000, row, col)

        row += 1

        lb_area_ = tk.Label(my_param_frame,
                            text="Lb area",
                            font=("Helvetica", param_size),
                            bg=background,
                            fg=text_color)

        lb_area_.grid(row=row, column=col, sticky=tk.W)
        self.master.lb_area_value_ = []
        self.master.lb_area_entry_ = []

        self.split_widget(my_param_frame, self.master.lb_area_entry_,
                          self.master.lb_area_value_, 1, row, col)

        row += 1

        ub_acell_ = tk.Label(my_param_frame,
                             text="Ub acell",
                             font=("Helvetica", param_size),
                             bg=background,
                             fg=text_color)

        ub_acell_.grid(row=row, column=col, sticky=tk.W)
        self.master.ub_acell_value_ = []
        self.master.ub_acell_entry_ = []

        self.split_widget(my_param_frame, self.master.ub_acell_entry_,
                          self.master.ub_acell_value_, 25, row, col)

    def dashboard(self):
        row = 0
        col = 0

        canvas = tk.Canvas(self,
                           width=300,
                           height=300,
                           background=background,
                           bd=0,
                           highlightthickness=0)
        canvas.create_image(150, 150, image=self.master.img)
        canvas.grid(row=row, column=col, sticky=tk.E, pady=50)

        my_frame = tk.Frame(self, bg=background)
        my_frame.grid(row=row, column=col + 1, sticky=tk.W, pady=30)

        # titre Parameters
        label_title = tk.Label(my_frame,
                               text="Process configuration",
                               font=("Helvetica", 36),
                               bg=background,
                               fg=text_color)
        label_title.pack()

        my_param_frame = tk.Frame(my_frame, bg=background)
        my_param_frame.pack(padx=50, pady=5)
        row += 1

        self.parameter_dashboard(my_param_frame)

        clik = tk.Frame(self, bg=background)
        clik.grid(row=row, column=col + 1, sticky=tk.W, pady=30)

        arrow_frame = tk.Frame(clik, bg=background)
        arrow_frame.grid(row=0, column=col + 1, sticky=tk.W)

        label_return = tk.Label(arrow_frame,
                                text="Return",
                                font=("Helvetica", 14),
                                bg=background,
                                fg=text_color)

        label_return.pack()

        # Arrow button
        tk.Button(arrow_frame,
                  relief=tk.GROOVE,
                  font=("Helvetica", param_size),
                  bg=background,
                  fg=text_color,
                  bd=0,
                  highlightthickness=0,
                  image=self.master.reverse_arrow,
                  compound=tk.LEFT,
                  command=self.master.home).pack(side=tk.BOTTOM,
                                                 padx=100,
                                                 pady=5,
                                                 fill=tk.X)

        row += 1

        button_frame = tk.Frame(clik, bg=background)
        button_frame.grid(row=0, column=col + 2, sticky=tk.W)
        self.master.solve_button = tk.Button(button_frame,
                                             text="Solve",
                                             relief=tk.GROOVE,
                                             font=("Helvetica", param_size),
                                             bg='white',
                                             fg=text_color,
                                             bd=2,
                                             highlightthickness=1,
                                             command=self.master.solve)
        self.master.solve_button.pack(side=tk.BOTTOM,
                                      padx=50,
                                      pady=5,
                                      fill=tk.X)


class ParameterPage(tk.Frame):

    def __init__(self, window):
        tk.Frame.__init__(self, window)
        self.master = window
        self.config(bg=background)

    def print_info_message(self, msg):
        """ alert info message
        """
        messagebox.showinfo("Information", msg)

    def print_warning_message(self, msg):
        """ alert warning message
        """
        messagebox.showwarning("Waring", msg)

    def print_error_message(self, msg):
        """ alert error message
        """
        messagebox.showerror("ERROR", msg)

    def valid_value(self, entry_widget, entry_value):
        try:
            entry_widget.configure(bg='white')
            logger.debug("function valid_value [" + str(entry_widget) + " = " +
                         str(entry_value.get()) + "]")
            return True
        except tk.TclError:
            entry_widget.configure(bg=error_color)
            logger.error("function valid_value [" + str(entry_widget) +
                         "] (Empty field or wrong caracter typed)")
            self.print_error_message("Empty field or wrong caracter typed")
            return False

    # def valid_limit(self, entry_widget, entry_value):
    #     # from 1 to 5 else warning (error)
    #     entry_widget.configure(bg='white')
    #     if not 1 <= entry_value.get() <= 5:
    #         print("Warning")
    #         entry_widget.configure(bg=error_color)
    #         self.print_error_message("num_membranes borne limit")
    #         # raise ValueError("...Number of membrane is out of scope")
    #         return False
    #     return True

    def controle_fiels(self):
        """Controle if submitted fiels are ok.
        """
        if not self.valid_value(self.seed_1_entry, self.seed_1_temp):
            return False
        if not self.valid_value(self.seed_2_entry, self.seed_2_temp):
            return False
        if not self.valid_value(self.max_trials_entry, self.max_trials_temp):
            return False
        if not self.valid_value(self.max_no_improve_entry,
                                self.max_no_improve_temp):
            return False
        if not self.valid_value(self.nb_points_randomized_entry,
                                self.nb_points_randomized_temp):
            return False
        if not self.valid_value(self.pressure_ratio_entry,
                                self.pressure_ratio_temp):
            return False

        if not self.valid_value(self.pop_size_entry, self.pop_size_temp):
            return False
        if not self.valid_value(self.pop_gen_entry, self.pop_gen_temp):
            return False
        return True

    def validate_parameter(self):
        # check input validity
        var_control = self.controle_fiels()
        if not var_control:
            return
        logger.info("Parameter changement validated")
        self.print_info_message("Validate parameter change" +
                                "\n\n [Press a key to escape]")

        if self.master.solver_launched:
            # assigned values in temporary variable
            # and put it in original variable once thread solve terminated
            self.master.update_param = True
        else:
            # assigned values in original variable
            page = self.master.solveButton
            page.seed1 = self.seed_1_temp.get()
            page.seed2 = self.seed_2_temp.get()
            page.max_trials = self.max_trials_temp.get()
            page.max_no_improve = self.max_no_improve_temp.get()
            page.nb_points_randomized = self.nb_points_randomized_temp.get()
            page.pressure_ratio = self.pressure_ratio_temp.get()

            page.pop_size = self.pop_size_temp.get()
            page.nb_generations = self.pop_gen_temp.get()

        self.master.pages['exec'].tkraise()

    def dashboard(self):
        canvas = tk.Canvas(self,
                           width=300,
                           height=300,
                           background=background,
                           bd=0,
                           highlightthickness=0)
        canvas.create_image(150, 150, image=self.master.img)
        canvas.grid(row=0, column=0, sticky=tk.E, pady=50)

        my_frame = tk.Frame(self, bg=background)
        my_frame.grid(row=0, column=1, sticky=tk.W)

        # titre Parameters
        label_title = tk.Label(my_frame,
                               text="Change parameters",
                               font=("Helvetica", 36),
                               bg=background,
                               fg=text_color)
        label_title.pack()

        my_param_frame = tk.Frame(my_frame, bg=background)
        my_param_frame.pack(padx=100, pady=5)

        seed_1 = tk.Label(my_param_frame,
                          text="seed 1",
                          font=("Helvetica", param_size),
                          bg=background,
                          fg=text_color)
        seed_1.grid(row=0, column=0, sticky=tk.W)

        self.seed_1_temp = tk.IntVar()
        self.seed_1_temp.set(str(self.master.solveButton.seed1))
        self.seed_1_entry = tk.Entry(my_param_frame,
                                     width=10,
                                     textvariable=self.seed_1_temp)
        self.seed_1_entry.grid(row=0, column=1, sticky=tk.W)

        seed_2 = tk.Label(my_param_frame,
                          text="seed 2",
                          font=("Helvetica", param_size),
                          bg=background,
                          fg=text_color)
        seed_2.grid(row=1, column=0, sticky=tk.W)

        self.seed_2_temp = tk.IntVar()
        self.seed_2_temp.set(str(self.master.solveButton.seed2))
        self.seed_2_entry = tk.Entry(my_param_frame,
                                     width=10,
                                     textvariable=self.seed_2_temp)
        self.seed_2_entry.grid(row=1, column=1, sticky=tk.W)

        max_trials = tk.Label(my_param_frame,
                              text="max trials",
                              font=("Helvetica", param_size),
                              bg=background,
                              fg=text_color)
        max_trials.grid(row=2, column=0, sticky=tk.W)
        self.max_trials_temp = tk.IntVar()
        self.max_trials_temp.set(str(self.master.solveButton.max_trials))
        self.max_trials_entry = tk.Entry(my_param_frame,
                                         width=10,
                                         textvariable=self.max_trials_temp)
        self.max_trials_entry.grid(row=2, column=1, sticky=tk.W)

        max_no_improve = tk.Label(my_param_frame,
                                  text="max no improve",
                                  font=("Helvetica", param_size),
                                  bg=background,
                                  fg=text_color)
        max_no_improve.grid(row=3, column=0, sticky=tk.W)

        self.max_no_improve_temp = tk.IntVar()
        self.max_no_improve_temp.set(str(
            self.master.solveButton.max_no_improve))
        self.max_no_improve_entry = tk.Entry(
            my_param_frame, width=10, textvariable=self.max_no_improve_temp)
        self.max_no_improve_entry.grid(row=3, column=1, sticky=tk.W)

        nb_points_randomized = tk.Label(my_param_frame,
                                        text="nb points gen.",
                                        font=("Helvetica", param_size),
                                        bg=background,
                                        fg=text_color)
        nb_points_randomized.grid(row=4, column=0, sticky=tk.W)

        self.nb_points_randomized_temp = tk.IntVar()
        self.nb_points_randomized_temp.set(
            str(self.master.solveButton.nb_points_randomized))
        self.nb_points_randomized_entry = tk.Entry(
            my_param_frame,
            width=10,
            textvariable=self.nb_points_randomized_temp)
        self.nb_points_randomized_entry.grid(row=4, column=1, sticky=tk.W)

        pressure_ratio = tk.Label(my_param_frame,
                                  text="Pressure ratio",
                                  font=("Helvetica", param_size),
                                  bg=background,
                                  fg=text_color)
        pressure_ratio.grid(row=5, column=0, sticky=tk.W)

        self.pressure_ratio_temp = tk.DoubleVar()
        self.pressure_ratio_temp.set(str(
            self.master.solveButton.pressure_ratio))

        self.pressure_ratio_entry = tk.Entry(
            my_param_frame, width=10, textvariable=self.pressure_ratio_temp)
        self.pressure_ratio_entry.grid(row=5, column=1, sticky=tk.W)

        pressure_ratio = tk.Label(my_param_frame,
                                  text="Epsilon (fixed)",
                                  font=("Helvetica", param_size),
                                  bg=background,
                                  fg=text_color)
        pressure_ratio.grid(row=6, column=0, sticky=tk.W)

        pop_size_label = tk.Label(my_param_frame,
                                  text="Population size",
                                  font=("Helvetica", param_size),
                                  bg=background,
                                  fg=text_color)
        pop_size_label.grid(row=7, column=0, sticky=tk.W)

        self.pop_size_temp = tk.IntVar()
        self.pop_size_temp.set(str(self.master.solveButton.pop_size))
        self.pop_size_entry = tk.Entry(my_param_frame,
                                       width=10,
                                       textvariable=self.pop_size_temp)
        self.pop_size_entry.grid(row=7, column=1, sticky=tk.W)

        pop_generations_label = tk.Label(my_param_frame,
                                         text="Nb. generations",
                                         font=("Helvetica", param_size),
                                         bg=background,
                                         fg=text_color)
        pop_generations_label.grid(row=8, column=0, sticky=tk.W)

        self.pop_gen_temp = tk.IntVar()
        self.pop_gen_temp.set(str(self.master.solveButton.nb_generations))
        self.pop_gen_entry = tk.Entry(my_param_frame,
                                      width=10,
                                      textvariable=self.pop_gen_temp)
        self.pop_gen_entry.grid(row=8, column=1, sticky=tk.W)

        # valide uploading
        validate = tk.Button(my_param_frame,
                             text="Validate",
                             relief=tk.GROOVE,
                             font=("Helvetica", param_size),
                             bg='white',
                             fg=text_color,
                             bd=2,
                             highlightthickness=1,
                             command=self.validate_parameter)
        validate.grid(row=9, column=0, sticky=tk.W, pady=20)


class GuidePage(tk.Frame):

    def __init__(self, window):
        tk.Frame.__init__(self, window)
        self.master = window
        self.config(bg=background)

    def dashboard(self):
        canvas = tk.Canvas(self,
                           width=300,
                           height=300,
                           background=background,
                           bd=0,
                           highlightthickness=0)
        canvas.create_image(150, 150, image=self.master.img)
        canvas.grid(row=0, column=0, sticky=tk.E, pady=50)

        my_frame = tk.Frame(self, bg=background)
        my_frame.grid(row=0, column=1, sticky=tk.W, pady=50)

        # titre Parameters
        label_title = tk.Label(my_frame,
                               text="Welcome guide",
                               font=("Helvetica", 36),
                               bg=background,
                               fg=text_color)
        label_title.pack()

        my_param_frame = tk.Frame(my_frame, bg=background)
        my_param_frame.pack(fill="both", expand="yes", padx=10)

        question = tk.Label(my_param_frame,
                            text="How to use this application ?",
                            font=("Helvetica", 18),
                            bg=background,
                            fg=text_color)
        # num_membranes.pack()
        question.grid(row=0, column=0, sticky=tk.W)

        one = tk.Label(my_param_frame,
                       text="1) Go to Home page",
                       font=("Helvetica", param_size),
                       bg=background,
                       fg=text_color)
        one.grid(row=1, column=0, sticky=tk.W)

        two = tk.Label(my_param_frame,
                       text="2) Give inputs informations ",
                       font=("Helvetica", param_size),
                       bg=background,
                       fg=text_color)
        two.grid(row=2, column=0, sticky=tk.W)

        three = tk.Label(
            my_param_frame,
            text="3) Load datafiles and corresponding permeability data",
            font=("Helvetica", param_size),
            bg=background,
            fg=text_color)
        three.grid(row=3, column=0, sticky=tk.W)

        three_a = tk.Label(
            my_param_frame,
            text="3) For that, select File menu and load data files",
            font=("Helvetica", param_size),
            bg=background,
            fg=text_color)
        three_a.grid(row=4, column=0, sticky=tk.W)

        four = tk.Label(my_param_frame,
                        text="4) Click to solve button",
                        font=("Helvetica", param_size),
                        bg=background,
                        fg=text_color)
        four.grid(row=5, column=0, sticky=tk.W)

        five = tk.Label(my_param_frame,
                        text="5) Wait problem resolution",
                        font=("Helvetica", param_size),
                        bg=background,
                        fg=text_color)
        five.grid(row=6, column=0, sticky=tk.W)

        six = tk.Label(my_param_frame,
                       text="6) If problem occurs, you'll get error message",
                       font=("Helvetica", param_size),
                       bg=background,
                       fg=text_color)
        six.grid(row=7, column=0, sticky=tk.W)

        seven = tk.Label(
            my_param_frame,
            text="7) If no problem occurs, you'll get solutions in output file ",
            font=("Helvetica", param_size),
            bg=background,
            fg=text_color)
        seven.grid(row=8, column=0, sticky=tk.W)

        eight = tk.Label(
            my_param_frame,
            text="8) And design's result is saved in plotting.png ",
            font=("Helvetica", param_size),
            bg=background,
            fg=text_color)
        eight.grid(row=9, column=0, sticky=tk.W)


class InfosPage(tk.Frame):

    def __init__(self, window):
        tk.Frame.__init__(self, window)
        self.master = window
        self.config(bg=background)

    def dashboard(self):
        canvas = tk.Canvas(self,
                           width=300,
                           height=300,
                           background=background,
                           bd=0,
                           highlightthickness=0)
        canvas.create_image(150, 150, image=self.master.img)
        canvas.grid(row=0, column=0, sticky=tk.E, pady=50)

        my_frame = tk.Frame(self, bg=background)
        my_frame.grid(row=0, column=1, sticky=tk.W, pady=50)

        # titre Parameters
        label_title = tk.Label(my_frame,
                               text="Mind Project",
                               font=("Helvetica", 36),
                               bg=background,
                               fg=text_color)
        label_title.pack()

        my_param_frame = tk.Frame(my_frame, bg=background)
        my_param_frame.pack(fill="both", expand="yes", padx=10)

        tk.Label(my_param_frame,
                 text="Version: 0.2",
                 bg=background,
                 font=("Helvetica", 18),
                 fg=text_color).grid(row=0, column=0, sticky=tk.W)

        tk.Label(my_param_frame,
                 text="Continuous NonLinear Programming Solver",
                 bg=background,
                 font=("Helvetica", 18),
                 fg=text_color).grid(row=1, column=0, sticky=tk.W)

        tk.Label(my_param_frame,
                 text="For Membranes System Design",
                 font=("Helvetica", 18),
                 bg=background,
                 fg=text_color).grid(row=2, column=0, sticky=tk.W)

        tk.Label(my_param_frame,
                 text="Under collaboration of",
                 font=("Helvetica", 16),
                 bg=background,
                 fg=text_color).grid(row=3, column=0, sticky=tk.W)

        img_frame = tk.Frame(my_param_frame, bg=background)
        img_frame.grid(row=4, column=0, sticky=tk.W)

        canvas = tk.Canvas(img_frame,
                           width=200,
                           height=150,
                           background=background,
                           bd=0,
                           highlightthickness=0)
        canvas.create_image(100, 100, image=self.master.satt_img)
        canvas.grid(row=3, column=0, sticky=tk.W)

        canvas = tk.Canvas(img_frame,
                           width=200,
                           height=150,
                           background=background,
                           bd=0,
                           highlightthickness=0)
        canvas.create_image(100, 100, image=self.master.loria_img)
        canvas.grid(row=3, column=1, sticky=tk.W)


class SolveButton():

    def __init__(self, window):
        self.master = window

        self.epsilon = {
            'At': 0.3,
            'press_up_f': 0.2,
            'press_down_f': 0.2,
            'feed': 0.3,
            'perm_ref': 0.1,
            'alpha': 0.1,
            'delta': 0.1
        }

        self.seed1 = 2
        self.seed2 = 1

        self.max_trials = 10
        self.max_no_improve = 3
        self.nb_points_randomized = 5

        self.pressure_ratio = 0.03

        self.pop_size = 10
        self.nb_generations = 3

        # self.algorithm = "global_opt"
        # self.algorithm = "mbh"
        self.algorithm = "multistart"

    def print_info_message(self, msg):
        """ alert info message
        """
        messagebox.showinfo("Information", msg)

    def print_warning_message(self, msg):
        """ alert warning message
        """
        messagebox.showwarning("Warning", msg)

    def print_error_message(self, msg):
        """ alert error message
        """
        messagebox.showerror("ERROR", msg)

    def valid_value(self, entry_widget, entry_value):
        try:
            entry_widget.configure(bg='white')
            logger.debug("function valid_value [" + str(entry_widget) + " = " +
                         str(entry_value.get()) + "]")
            return True
        except tk.TclError:
            entry_widget.configure(bg=error_color)
            logger.error("function valid_value [" + str(entry_widget) +
                         "] (Empty field or wrong caracter typed)")
            self.print_error_message("Empty field or wrong caracter typed")
            return False

    def valid_limit(self, entry_widget, entry_value):
        # from 1 to 5 else warning (error)
        entry_widget.configure(bg='white')
        if not 1 <= entry_value.get() <= 5:
            msg = "abnormal number of membrane [{}]".format(entry_value.get())
            logger.warning(msg)
            entry_widget.configure(bg=error_color)
            self.print_warning_message(msg)
            return False
        return True

    def valid_area_bound(self):
        # upper bound must be greater than lower bound
        for index in range(self.master.num_membranes.get()):
            if self.master.lb_area_value_[index].get(
            ) > self.master.ub_area_value_[index].get():

                self.master.lb_area_entry_[index].configure(bg=error_color)
                self.master.ub_area_entry_[index].configure(bg=error_color)
                logger.error("Invalid bound [LB > UB]")
                self.print_error_message("Invalid bound [LB > UB]")
                return False
        return True

    def controle_fiels(self):
        """Controle if submitted fiels are ok.
        """
        if not self.valid_value(self.master.nb_spinbox,
                                self.master.num_membranes):
            return False
        if not self.valid_limit(self.master.nb_spinbox,
                                self.master.num_membranes):
            return False

        for index in range(self.master.num_membranes.get()):
            if not self.valid_value(self.master.ub_area_entry_[index],
                                    self.master.ub_area_value_[index]):
                return False

            if not self.valid_value(self.master.lb_area_entry_[index],
                                    self.master.lb_area_value_[index]):
                return False

            if not self.valid_value(self.master.ub_acell_entry_[index],
                                    self.master.ub_acell_value_[index]):
                return False

        if not self.valid_area_bound():
            return False

        logger.debug("function controle_fiels [ uniform pressure" + " = " +
                     str(self.master.uniform_pup_value.get()) + "]")

        logger.debug("function controle_fiels [ vacuum pump" + " = " +
                     str(self.master.vp_value.get()) + "]")

        logger.debug("function controle_fiels [ variable permeability" + " = " +
                     str(self.master.perm_variable_value.get()) + "]")

        logger.debug("function controle_fiels [ fixing variables" + " = " +
                     str(self.master.is_fixing_var.get()) + "]")

        # at this step, we get parameters

        # check if files loaded
        if self.master.datafiles_active.get() == 0:
            logger.error("Any datafiles selected for solving")
            self.print_error_message(
                "Any process constraint datafile selected for solving, "
                "select file in menubar")
            self.master.home()
            return False

        if self.master.perm_datafiles_active.get() == 0:
            logger.error("Any permeability datafile selected for solving")
            self.print_error_message(
                "Any process permeability datafile selected for solving, "
                "select file in menubar")
            self.master.home()
            return False

        if self.master.eco_datafiles_active.get() == 0:
            logger.error("Any economic datafile selected for solving")
            self.print_error_message(
                "Any process economic datafile selected for solving, "
                "select file in menubar")
            self.master.home()
            return False

        if (self.master.is_fixing_var.get() == 1 and
                self.master.filename_mask is None):
            # error
            logger.error(
                "Fixing variables status enabled but don't get any datafile")
            self.print_error_message(
                "Fixing variables status enabled but don't get any datafile, "
                "select file in menubar and choice 'fixing data'")
            self.master.home()
            return False

        logger.debug("function controle_fiels [ datafiles" + " = " +
                     str(self.master.datafiles_active.get()) + "]")

        logger.debug("function controle_fiels [ permeability datafile" + " = " +
                     str(self.master.perm_datafiles_active.get()) + "]")

        logger.debug("function controle_fiels [ economic datafile" + " = " +
                     str(self.master.eco_datafiles_active.get()) + "]")
        return True

    def solve(self):
        logger.info("User asking to solve")
        # messagebox.showinfo("Title", "a Tk MessageBox info")
        # messagebox.showwarning("Title", "a Tk MessageBox warning")
        # messagebox.showerror("Title", "a Tk MessageBox error")
        # controle case
        var_control = self.controle_fiels()
        if not var_control:
            return

        # build parameter
        self.parameter = Configuration(
            num_membranes=self.master.num_membranes.get(),
            ub_area=[
                self.master.ub_area_value_[index].get()
                for index in range(self.master.num_membranes.get())
            ],
            lb_area=[
                self.master.lb_area_value_[index].get()
                for index in range(self.master.num_membranes.get())
            ],
            ub_acell=[
                self.master.ub_acell_value_[index].get()
                for index in range(self.master.num_membranes.get())
            ],
            uniform_pup=bool(self.master.uniform_pup_value.get()),
            vp=bool(self.master.vp_value.get()),
            variable_perm=bool(self.master.perm_variable_value.get()),
            fixing_var=bool(self.master.is_fixing_var.get()))

        # build model instance
        try:
            self.modelisation = build_model(self.parameter,
                                            self.master.filename,
                                            self.master.filename_perm,
                                            self.master.filename_eco,
                                            self.master.filename_mask)
        except (ValueError, IndexError) as e:
            logger.error("Failed to create model instance [Exception raised]")

            self.print_error_message("Failed to create model instance" +
                                     "\n [problem with datafiles]" +
                                     "\n See log file")
            raise e
        except AttributeError as e:
            self.print_error_message("Failed to create model instance" +
                                     "\n[AttributeError]")
            raise e
        except Exception as e:
            self.print_error_message(
                "Failed to create model instance" +
                "\nError in datafiles / prameters not correctly configured")
            raise e
        else:
            self.master.solve_button.config(state=tk.DISABLED)
            self.master.event.set()

            if not self.master.thread_first_exec:
                self.master.my_thread.daemon = True
                self.master.my_thread.start()
                self.master.thread_first_exec = True

        finally:
            # Instruction(s) exécutée(s) qu'il y ait eu des erreurs ou non
            # When finish execution, deselect some field
            # self.master.datafiles_active.set(0)
            # self.master.perm_datafiles_active.set(0)
            # self.master.eco_datafiles_active.set(0)
            # self.master.is_fixing_var.set(0)

            pass
            # self.datafiles_active_button.deselect()


class Application(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)
        self.filename = None
        self.filename_perm = None
        self.filename_mask = None
        self.datafiles_active = tk.IntVar()
        self.perm_datafiles_active = tk.IntVar()
        self.eco_datafiles_active = tk.IntVar()
        self.pages = {}
        self.event = Event()  # create event object
        self.event.clear()
        self.my_thread = ThreadSolver(self)
        self.solver_launched = False
        self.thread_waiting = False
        self.thread_first_exec = False
        self.leave = False
        self.update_param = False  # Update the parameter after thread solve

        self.solveButton = SolveButton(self)

        self.menu_bar()
        # Set a title
        self.title('Mind project')
        # set window size
        self.set_window_size()
        # logo app
        # window.iconbitmap("logo.ico")

        self.resizable(False, False)
        # grid_columnconfigure

        # couleur de font
        self.config(background=background)

    # TODO: checker si le contenue du fichier est bon
    # put the frame on the top
    # frame.tkraise()
    #
    # def click_edit_button(self):
    #     print("Edit menu clicked")

    def click_preferences_button(self):
        pass

    def print_info_message(self, msg):
        """ alert info message
        """
        messagebox.showinfo("Information", msg)

    def print_warning_message(self, msg):
        """ alert warning message
        """
        messagebox.showwarning("Warning", msg)

    def print_error_message(self, msg):
        """ alert error message
        """
        messagebox.showerror("ERROR", msg)

    def load_data_file(self):
        self.filename = tk.filedialog.askopenfilename(
            title="Ouvrir votre document",
            filetypes=[('dat files (.dat)', '.dat')])

        if self.filename == "" or not self.filename:
            logger.warning("No datafile selected")
            self.print_warning_message("No datafile selected")
            self.datafiles_active.set(0)

        else:
            logger.info("model data path = {}".format(self.filename))
            self.datafiles_active.set(1)

    def load_perm_data(self):
        self.filename_perm = tk.filedialog.askopenfilename(
            title="Ouvrir votre document",
            filetypes=[('dat files (.dat)', '.dat')])

        if self.filename_perm == "" or not self.filename_perm:
            logger.warning("No permeability datafile selected")
            self.print_warning_message("No permeability datafile selected")
            self.perm_datafiles_active.set(0)
        else:
            logger.info("model permeability data path = {}".format(
                self.filename_perm))
            self.perm_datafiles_active.set(1)

    def load_economic_data(self):
        self.filename_eco = tk.filedialog.askopenfilename(
            title="Ouvrir votre document",
            filetypes=[('dat files (.dat)', '.dat')])

        if self.filename_eco == "" or not self.filename_eco:
            logger.warning("No economic datafile selected")
            self.print_warning_message("No economic datafile selected")
            self.eco_datafiles_active.set(0)
        else:
            logger.info("model economic data path = {}".format(
                self.filename_eco))
            self.eco_datafiles_active.set(1)

    def info(self):
        """ Mind project information.
        """
        self.pages['info'].tkraise()

    def guide(self):
        """ Mind project information.
        """
        self.pages['guide'].tkraise()

    def fixing_values(self):
        """Fixing some variables.
        """
        # self.pages['exec'].tkraise()
        self.filename_mask = tk.filedialog.askopenfilename(
            title="Ouvrir votre document",
            filetypes=[('dat files (.dat)', '.dat')])

        if self.filename_mask == "":
            logger.warning("No data selected for fixing variables values")
            self.print_warning_message(
                "No data selected for fixing variables values")
            self.is_fixing_var.set(0)
        else:
            logger.info("model economic data path = {}".format(
                self.filename_mask))
            self.is_fixing_var.set(1)

    def home(self):
        self.pages['start'].tkraise()

    def redirect_second_page(self):
        self.pages['exec'].dashboard()
        self.pages['exec'].tkraise()

    def set_parameters(self):
        self.pages['param'].tkraise()

    def solve(self):
        self.solveButton.solve()

    def global_opt(self):
        self.solveButton.algorithm = "global_opt"
        logger.info("Choice of algorithm : global optimization")
        self.print_info_message("Choice of algorithm : Global optimization")

        # Activated necessary input field paramaters
        self.pages['param'].seed_1_entry.config(state=tk.NORMAL)
        self.pages['param'].seed_2_entry.config(state=tk.NORMAL)
        self.pages['param'].pressure_ratio_entry.config(state=tk.NORMAL)
        self.pages['param'].max_trials_entry.config(state=tk.NORMAL)
        self.pages['param'].max_no_improve_entry.config(state=tk.NORMAL)
        self.pages['param'].nb_points_randomized_entry.config(state=tk.NORMAL)

        # DISABLED unnecessary input field paramaters
        self.pages['param'].pop_size_entry.config(state=tk.DISABLED)
        self.pages['param'].pop_gen_entry.config(state=tk.DISABLED)

    def mbh(self):
        self.solveButton.algorithm = "mbh"
        logger.info("Choice of algorithm : mbh")
        self.print_info_message("Choice of algorithm : MBH")

        # Activated necessary input field paramaters
        self.pages['param'].seed_1_entry.config(state=tk.NORMAL)
        self.pages['param'].seed_2_entry.config(state=tk.NORMAL)
        self.pages['param'].pressure_ratio_entry.config(state=tk.NORMAL)
        self.pages['param'].max_trials_entry.config(state=tk.NORMAL)
        self.pages['param'].max_no_improve_entry.config(state=tk.NORMAL)

        # DISABLED unnecessary input field paramaters
        self.pages['param'].nb_points_randomized_entry.config(state=tk.DISABLED)
        self.pages['param'].pop_size_entry.config(state=tk.DISABLED)
        self.pages['param'].pop_gen_entry.config(state=tk.DISABLED)

    def multistart(self):
        self.solveButton.algorithm = "multistart"
        logger.info("Choice of algorithm : multistart")
        self.print_info_message("Choice of algorithm : Multistart")

        # Activated necessary input field paramaters
        self.pages['param'].seed_1_entry.config(state=tk.NORMAL)
        self.pages['param'].nb_points_randomized_entry.config(state=tk.NORMAL)
        self.pages['param'].pressure_ratio_entry.config(state=tk.NORMAL)

        # DISABLED unnecessary input field paramaters
        self.pages['param'].seed_2_entry.config(state=tk.DISABLED)
        self.pages['param'].max_trials_entry.config(state=tk.DISABLED)
        self.pages['param'].max_no_improve_entry.config(state=tk.DISABLED)

        self.pages['param'].pop_size_entry.config(state=tk.DISABLED)
        self.pages['param'].pop_gen_entry.config(state=tk.DISABLED)

    def genetic_method(self):
        self.solveButton.algorithm = "genetic_method"
        logger.info("Choice of algorithm : Evolutionary method")
        self.print_info_message("Choice of algorithm : Evolutionary method")

        # Activated necessary input field paramaters
        self.pages['param'].pop_size_entry.config(state=tk.NORMAL)
        self.pages['param'].pop_gen_entry.config(state=tk.NORMAL)
        self.pages['param'].seed_1_entry.config(state=tk.NORMAL)

        # DISABLED unnecessary input field paramaters
        self.pages['param'].seed_2_entry.config(state=tk.DISABLED)
        self.pages['param'].pressure_ratio_entry.config(state=tk.DISABLED)
        self.pages['param'].max_trials_entry.config(state=tk.DISABLED)
        self.pages['param'].max_no_improve_entry.config(state=tk.DISABLED)
        self.pages['param'].nb_points_randomized_entry.config(state=tk.DISABLED)

    def population_method(self):
        self.solveButton.algorithm = "population_method"
        logger.info("Choice of algorithm : Modified Evolutionary method")
        self.print_info_message("Choice of algorithm : Evolutionary method")

        # Activated necessary input field paramaters
        self.pages['param'].pop_size_entry.config(state=tk.DISABLED)
        self.pages['param'].pop_gen_entry.config(state=tk.DISABLED)
        self.pages['param'].seed_1_entry.config(state=tk.DISABLED)

        # DISABLED unnecessary input field paramaters
        self.pages['param'].seed_2_entry.config(state=tk.DISABLED)
        self.pages['param'].pressure_ratio_entry.config(state=tk.DISABLED)
        self.pages['param'].max_trials_entry.config(state=tk.DISABLED)
        self.pages['param'].max_no_improve_entry.config(state=tk.DISABLED)
        self.pages['param'].nb_points_randomized_entry.config(state=tk.DISABLED)

    def menu_bar(self):
        # Menubar
        menubar = tk.Menu(self)

        menu_home = tk.Menu(menubar, tearoff=0)
        menu_home.add_command(label="home", command=self.home)
        menubar.add_cascade(label="Home", menu=menu_home)

        menu1 = tk.Menu(menubar, tearoff=0)
        menu1.add_command(label="data file", command=self.load_data_file)
        menu1.add_command(label="permeability data",
                          command=self.load_perm_data)
        menu1.add_command(label="economic data",
                          command=self.load_economic_data)
        menu1.add_command(label="fixing data", command=self.fixing_values)
        # menu1.add_separator()
        menubar.add_cascade(label="File", menu=menu1)

        menu_algo = tk.Menu(menubar, tearoff=0)
        menu_algo.add_command(label="Global optmization",
                              command=self.global_opt)
        menu_algo.add_command(label="genetic method",
                              command=self.genetic_method)

        menu_algo.add_command(label="Modified Population method",
                              command=self.population_method)

        menu_algo.add_command(label="MBH", command=self.mbh)
        menu_algo.add_command(label="Multistart", command=self.multistart)
        menu_algo.add_command(label="Change parameter",
                              command=self.set_parameters)
        menubar.add_cascade(label="Algorithm", menu=menu_algo)

        menu5 = tk.Menu(menubar, tearoff=0)
        menu5.add_command(label="About", command=self.info)
        menu5.add_command(label="Welcome guide", command=self.guide)
        menubar.add_cascade(label="Help", menu=menu5)

        # menu_fixing = tk.Menu(menubar, tearoff=0)
        # menu_fixing.add_command(label="Loading file",
        #                         command=self.fixing_values)
        # menubar.add_cascade(label="Fixing values", menu=menu_fixing)

        self.config(menu=menubar)

    def set_window_size(self):
        if (self.winfo_screenwidth() >= 1080 and
                self.winfo_screenheight() >= 720):
            # HD format
            geom_string = "1080x720"
            geom_string = "900x650"
        else:
            HalfScreenWidth = int(self.winfo_screenwidth() / 2)
            HalfScreenHeight = int(self.winfo_screenheight() / 2)

            w = HalfScreenWidth - int(HalfScreenWidth / 2)
            h = HalfScreenHeight - int(HalfScreenHeight / 2)

            geom_string = "+{}+{}".format(w, h)

        self.geometry(geom_string)
        # window.minsize(
        #     int(window.winfo_screenwidth()/4),
        #     int(window.winfo_screenheight()/4)
        #     )

        self.minsize(900, 650)

    def thread_solver_termination(self, event):
        # print(event)
        # reactivate solve button
        self.solve_button.config(state=tk.NORMAL)
        self.solver_launched = False

        # Save execution parameters on a file
        self.save_parameters()

        if self.update_param:
            # doing update
            self.solveButton.seed1 = self.pages['param'].seed_1_temp.get()
            self.solveButton.seed2 = self.pages['param'].seed_2_temp.get()
            self.solveButton.max_trials = self.pages[
                'param'].max_trials_temp.get()
            self.solveButton.max_no_improve = self.pages[
                'param'].max_no_improve_temp.get()
            self.solveButton.nb_points_randomized = self.pages[
                'param'].nb_points_randomized_temp.get()
            self.solveButton.pressure_ratio = self.pages[
                'param'].pressure_ratio_temp.get()

            self.update_param = False

        # Visualise the solution (the best if it exists)
        #  Save image in file
        if self.solveButton.my_solver.feasible:
            self.solveButton.my_solver.visualise_solutions(
                self.solveButton.modelisation.instance,
                self.solveButton.modelisation.parameter)

            logger.info("algorithm's run finished," +
                        " Solution saved as image [plotting.png]")

            self.print_info_message("algorithm's run finished," +
                                    "\nSolution saved as image [plotting.png]")

            # obj_data.generate_sol_log(log_sol)
            # obj_data.histogramme_capex(model, parameter)
            # obj_data.histogramme_opex()

        else:
            logger.info("algorithm's run finished," + " No solution founded")

            self.print_info_message("algorithm's run finished," +
                                    "\n No solution founded")

    def save_parameters(self):
        # Save execution parameters on a file
        outfile = self.solveButton.log + "param.log"
        logger.info("Saving process configurations in ".format(outfile))
        with open(outfile, 'w') as file:
            file.write("Paramaters :\n")

            file.write("Algorithm =  " + self.solveButton.algorithm + "\n")

            file.write("nombre de membrane =  " +
                       str(self.num_membranes.get()) + "\n")

            file.write("ub area =  " + str([
                self.ub_area_value_[index].get()
                for index in range(self.num_membranes.get())
            ]) + "\n")

            file.write("lb area =  " + str([
                self.lb_area_value_[index].get()
                for index in range(self.num_membranes.get())
            ]) + "\n")

            file.write("ub acell =  " + str([
                self.ub_acell_value_[index].get()
                for index in range(self.num_membranes.get())
            ]) + "\n")

            file.write("uniform_pup =  " +
                       str(bool(self.uniform_pup_value.get())) + "\n")

            file.write("Vacuum pump =  " + str(bool(self.vp_value.get())) +
                       "\n")

            file.write("permeability variable =  " +
                       str(bool(self.perm_variable_value.get())) + "\n")

            file.write("seed1 = " + str(self.solveButton.seed1) + "\n")

            file.write("seed2 = " + str(self.solveButton.seed2) + "\n")

            file.write("max_trials = " + str(self.solveButton.max_trials) +
                       "\n")

            file.write("max_no_improve = " +
                       str(self.solveButton.max_no_improve) + "\n")

            file.write("nb_points_randomized = " +
                       str(self.solveButton.nb_points_randomized) + "\n")

            file.write("pressure_ratio = " +
                       str(self.solveButton.pressure_ratio) + "\n")

            file.flush()

    def init_default_config(self):
        logger.info("Default parameter activated")

        dir = (generate_absolute_path() + "log" + os.path.sep + "img" +
               os.path.sep)
        path_img = dir + "distillation.png"
        next_arrow_img = dir + "arrow.png"
        reverse_arrow_img = dir + "return.png"

        # print(path_img)
        self.img = tk.PhotoImage(file=path_img).zoom(20).subsample(33)
        self.next_arrow = tk.PhotoImage(file=next_arrow_img).subsample(20, 20)
        self.reverse_arrow = tk.PhotoImage(file=reverse_arrow_img).subsample(
            5, 5)

        path_img = dir + "sayens.png"
        self.satt_img = tk.PhotoImage(file=path_img)

        path_img = dir + "loria.png"
        self.loria_img = tk.PhotoImage(file=path_img).zoom(20).subsample(33)

    def set_pages(self):
        self.pages['start'] = StartPage(window)
        self.pages['start'].grid(row=0, column=0, sticky='nsew')
        self.pages['start'].dashboard()

        self.pages['param'] = ParameterPage(window)
        self.pages['param'].grid(row=0, column=0, sticky='nsew')
        self.pages['param'].dashboard()

        self.pages['guide'] = GuidePage(window)
        self.pages['guide'].grid(row=0, column=0, sticky='nsew')
        self.pages['guide'].dashboard()

        self.pages['info'] = InfosPage(window)
        self.pages['info'].grid(row=0, column=0, sticky='nsew')
        self.pages['info'].dashboard()

        self.pages['exec'] = MainPage(window)
        self.pages['exec'].grid(row=0, column=0, sticky='nsew')
        self.pages['exec'].dashboard()

        # update the first page
        self.pages['start'].tkraise()

    def close_window(self):
        logger.info("Quitting application ...")
        if self.solver_launched:
            # stopper le thread
            self.leave = True
            window.destroy()
            self.quit()
        elif self.thread_waiting:
            # stopper le thread
            self.leave = True
            self.event.set()
            self.destroy()
            self.quit()
        else:
            None
            # thread is not yet launched
            self.destroy()
            self.quit()


if __name__ == '__main__':
    # create window
    # window = tk.Tk()
    window = Application()
    window.init_default_config()

    # define pages
    window.set_pages()

    window.bind("<<thread_fini>>", window.thread_solver_termination)

    window.protocol("WM_DELETE_WINDOW", window.close_window)

    # print window
    window.mainloop()
