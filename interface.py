import pickle
import sys
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter.ttk import Frame, Button, Label, Entry, Combobox
from io import BytesIO
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import distributions
from stack_manager import StackManager, get_cpk, lengths_to_magnitudes
from stackup_step import StackupStep
from qbstyles import mpl_style
from report_generator import ReportGenerator

"""
Author: Samuel Lehmann
Network with him at: https://www.linkedin.com/in/samuellehmann/
"""

TITLE = "Tol Ninja: Tolerance Stackup Analysis"
_DECIMAL_PLACES = 2
_MPL_BACKGROUND = "#1c1c1c"

row_entries = []

# UI Elements
table_frame, bold_style, tab_control, root, arrow_figure, oal_figure, stack_manager, middle_frame, report_scroll_canvas, \
setup_scroll_canvas, setup_scroll_canvas_frame, oal_lsl_lref, oal_usl_limit_lref, magnitude_figure, mean_label, \
median_label, min_label, max_label, samples_label, absolute_label, percent_below_label, \
percent_above_label, percent_ok_label, percent_nok_label, custom_lower_entry_sv, custom_upper_entry_sv, \
percent_below_custom_label, percent_above_custom_label, percent_good_custom_label, \
percent_bad_custom_label, std_label, cpk_label, cust_cpk_label, stack_type_combo, title_entry, author_entry, \
revision_entry = (None for i in range(37))


def generate_interface():
    """
    Creates the window and the interface within it
    :return:
    """
    global table_frame, tab_control, root
    root = tk.Tk()
    root.title(TITLE)
    root.iconbitmap("icon.ico")
    root.geometry('1800x1200')

    # Set the theme.
    # Credits to: https://github.com/rdbende/Sun-Valley-ttk-theme & https://github.com/quantumblacklabs/qbstyles
    # TKinter theme:
    root.tk.call("source", "sun-valley.tcl")
    root.tk.call("set_theme", "dark")
    # Matplotlib theme:
    mpl_style(dark=True)

    tab_control = ttk.Notebook(root)
    setup_frame = Frame(tab_control)
    report_frame = Frame(tab_control)
    tab_control.pack(fill="both", expand=1)

    bold_style = ttk.Style()
    bold_style.configure("Bold.TButton", font=('Sans', '12', 'bold'))

    _generate_setup_frame(setup_frame)
    _generate_report_frame(report_frame)

    setup_frame.pack()
    report_frame.pack()

    tab_control.add(setup_frame, text='Setup')
    tab_control.add(report_frame, text='Report')

    root.mainloop()
    sys.exit()


def _generate_setup_frame(setup_frame):
    """
    Configures and lays out the interface for the setup tab
    :param setup_frame: The setup frame to be configured
    :return:
    """
    global table_frame, oal_lsl_lref, oal_usl_limit_lref, stack_type_combo, setup_scroll_canvas, \
        setup_scroll_canvas_frame

    top_frame = Frame(setup_frame)
    top_frame.pack(fill="x", pady=10)
    top_frame.grid_columnconfigure(0, weight=1)
    top_frame.grid_columnconfigure(1, weight=1)
    top_frame.grid_columnconfigure(2, weight=1)

    save_load_button_frame = Frame(top_frame)
    save_button = Button(save_load_button_frame, text="Save Stack", command=_save_pressed)
    save_button.grid(row=0, column=0, padx=10)
    load_button = Button(save_load_button_frame, text="Load Stack", command=_load_pressed)
    load_button.grid(row=0, column=1, padx=10)
    save_load_button_frame.grid(row=0, column=0, sticky="w", padx=30)

    stack_type_frame = Frame(top_frame)
    Label(stack_type_frame, text="Stack Type:").pack(side="left", padx=5)
    stack_type_combo = Combobox(stack_type_frame, values=("1-Dimensional Stack", "Radial Stack"), width=20,
                                justify="center")
    stack_type_combo.set("1-Dimensional Stack")
    stack_type_combo.pack(side="left")
    stack_type_combo.bind("<<ComboboxSelected>>", lambda event: _stack_type_change())
    stack_type_frame.grid(row=0, column=1)

    spec_limits_frame = Frame(top_frame, width=100)
    spec_limits_frame.grid_columnconfigure(0, weight=1)
    spec_limits_frame.grid_columnconfigure(1, weight=1)

    oal_lsl_lref = LabelRestrictedEntryFrame(spec_limits_frame, "Overall Lower Specification Limit")
    oal_lsl_lref.grid(row=0, column=0)
    oal_usl_limit_lref = LabelRestrictedEntryFrame(spec_limits_frame, "Overall Upper Specification Limit")
    oal_usl_limit_lref.grid(row=0, column=1, padx=20)
    spec_limits_frame.grid(row=0, column=2, sticky="e", padx=50)

    table_title_frame = Frame(setup_frame)
    table_title_frame.pack(fill="x", pady="10")
    Label(table_title_frame, text="Part Names", width=21, justify="center", anchor="center").pack(side="left",
                                                                                                  padx=(38, 0))
    Label(table_title_frame, text="Descriptions", width=21, justify="center", anchor="center").pack(side="left",
                                                                                                    padx=(80, 0))
    Label(table_title_frame, text="Distribution Types", width=24, justify="center", anchor="center").pack(side="left")
    Label(table_title_frame, text="Add Or Remove \nSubsteps", width=15, justify="center", anchor="center").pack(
        side="right", padx=30)

    # Create a frame for the canvas and scrollbar(s).
    table_frame_container = Frame(setup_frame)
    table_frame_container.pack(fill="both")

    # Add a canvas in that frame.
    setup_scroll_canvas = tk.Canvas(table_frame_container)
    setup_scroll_canvas.pack(side="left", fill="x", expand=1)

    table_frame = Frame(table_frame_container)

    # Create a vertical scrollbar linked to the canvas.
    scroll_bar = ttk.Scrollbar(table_frame_container, orient=tk.VERTICAL, command=setup_scroll_canvas.yview)

    scroll_bar.pack(side="right", fill="y")
    setup_scroll_canvas.configure(yscrollcommand=scroll_bar.set)

    setup_scroll_canvas_frame = setup_scroll_canvas.create_window((0, 0), window=table_frame, anchor="nw")

    table_frame.bind("<Configure>", _on_frame_configure)
    setup_scroll_canvas.bind('<Configure>', _update_scroll_canvas_width)

    table_frame.update_idletasks()  # Needed to make bbox info available.
    bbox = setup_scroll_canvas.bbox(tk.ALL)  # Get bounding box of canvas

    # Define the scrollable region as entire canvas with only the desired width/height
    setup_scroll_canvas.configure(scrollregion=bbox, height=850)

    init_entry = StackRow(table_frame, init_entry=True)
    init_entry.pack(fill="x", expand=1)
    row_entries.append(init_entry)

    footer_frame = Frame(setup_frame)
    footer_frame.pack(side="bottom", fill="both", pady=10)

    Label(footer_frame, text="Input the steps that make up the tolerance stack. \n"
                             "Lower and upper cutoffs are optional and will truncate the distribution for a stackup "
                             "step at these values. "
                             "They should be used in the event that an inspection is performed for which parts are "
                             "rejected.\n"
                             "The skew value in a skewed normal distribution ranges from - infinity to + infinity. "
                             "A negative value will skew the distribution to the left. A positive value will skew the "
                             "distribution to the right. 0 skew results in the normal distribution.",
          justify="center", anchor="center").pack(anchor="center", side="bottom", pady=10)

    save_load_button_frame = Frame(footer_frame, width=150)
    save_load_button_frame.grid_columnconfigure(0, weight=1)
    save_load_button_frame.grid_columnconfigure(1, weight=1)
    save_load_button_frame.grid_columnconfigure(2, weight=1)

    add_part_button = Button(save_load_button_frame, text="Add Part", style="Bold.TButton", command=_add_part_pressed)
    add_part_button.grid(row=0, column=0, padx=50, pady=10, ipady=10, ipadx=10)

    calculate_button = Button(save_load_button_frame, text="Calculate", style="Bold.TButton",
                              command=_calculate_button_pressed)
    calculate_button.grid(row=0, column=2, padx=50, pady=10, ipady=10, ipadx=10)
    save_load_button_frame.pack(anchor="center", side="bottom", pady=10)


def _generate_report_frame(report_frame):
    """
    Configures and lays out the interface for the report tab
    :param report_frame: The report frame to be configured
    :return:
    """
    global arrow_figure, mean_label, median_label, min_label, max_label, samples_label, absolute_label, \
        percent_below_label, percent_above_label, percent_ok_label, percent_nok_label, custom_lower_entry_sv, \
        custom_upper_entry_sv, percent_below_custom_label, percent_above_custom_label, percent_good_custom_label, \
        percent_bad_custom_label, arrow_figure, oal_figure, magnitude_figure, middle_frame, report_scroll_canvas, \
        std_label, cpk_label, cust_cpk_label, title_entry, author_entry, revision_entry

    # Generate Header Row
    header_frame = Frame(report_frame)
    header_frame.pack(fill="x", pady=10)
    header_frame.grid_columnconfigure(0, weight=1)
    header_frame.grid_columnconfigure(1, weight=1)
    header_frame.grid_columnconfigure(2, weight=1)

    title_frame = ttk.Frame(header_frame)
    title_label = Label(title_frame, text="Title:", anchor="e")
    title_entry = Entry(title_frame, width=20)
    title_label.pack(side="left", padx=5)
    title_entry.pack(side="left")

    author_frame = ttk.Frame(header_frame)
    author_label = Label(author_frame, text="Author:", width=21, anchor="e")
    author_entry = Entry(author_frame, width=20)
    author_label.pack(side="left", padx=5)
    author_entry.pack(side="left")

    revision_frame = ttk.Frame(header_frame)
    revision_label = Label(revision_frame, text="Revision:", width=21, anchor="e")
    revision_entry = Entry(revision_frame, width=20)
    revision_label.pack(side="left", padx=5)
    revision_entry.pack(side="left")

    title_frame.grid(row=0, column=0)
    author_frame.grid(row=0, column=1)
    revision_frame.grid(row=0, column=2)
    header_frame.pack(fill="x")

    # Create a frame for the canvas and scrollbar(s).
    mid_frame = Frame(report_frame)
    mid_frame.pack()

    # Add a canvas in that frame.
    report_scroll_canvas = tk.Canvas(mid_frame)
    report_scroll_canvas.grid(row=0, column=0)

    # Create a vertical scrollbar linked to the canvas.
    scroll_bar = tk.Scrollbar(mid_frame, orient=tk.VERTICAL, command=report_scroll_canvas.yview)
    scroll_bar.grid(row=0, column=1, sticky=tk.NS)
    report_scroll_canvas.configure(yscrollcommand=scroll_bar.set)

    # Generate Middle Frame
    middle_frame = Frame(report_scroll_canvas)
    middle_frame.grid_columnconfigure(0, weight=1)
    middle_frame.grid_columnconfigure(1, weight=1)
    middle_frame.grid_rowconfigure(0, weight=1)
    middle_frame.grid_rowconfigure(1, weight=1)

    # Layout the arrow figure
    arrow_figure = plt.figure(figsize=(10, 5))
    figure_canvas = FigureCanvasTkAgg(arrow_figure, master=middle_frame)
    figure_canvas.draw()
    figure_canvas.get_tk_widget().columnconfigure(0, weight=1)
    figure_canvas.get_tk_widget().grid(column=0, row=0)

    data_summary_frame = Frame(middle_frame)
    data_summary_frame.grid_columnconfigure(0, weight=1)
    data_summary_frame.grid_columnconfigure(1, weight=1)
    data_summary_frame.grid_rowconfigure(0, weight=1)
    data_summary_frame.grid_rowconfigure(1, weight=1)
    data_summary_frame.grid_rowconfigure(2, weight=1)
    data_summary_frame.grid_rowconfigure(3, weight=1)
    data_summary_frame.grid_rowconfigure(4, weight=1)
    data_summary_frame.grid_rowconfigure(6, weight=1)
    data_summary_frame.grid_rowconfigure(7, weight=1)
    data_summary_frame.grid_rowconfigure(8, weight=1)
    data_summary_frame.grid_rowconfigure(9, weight=1)
    data_summary_frame.grid_rowconfigure(10, weight=1)

    title_label = Label(data_summary_frame, text="Data Summary: ", justify="center", anchor="center",
                        font=("Arial bold", 15))
    title_label.grid(row=0, column=0, columnspan=2, sticky=tk.W + tk.E, pady=15)

    mean_label = Label(data_summary_frame, text="Mean: ")
    median_label = Label(data_summary_frame, text="Median: ")
    mean_label.grid(row=1, column=0, pady=5, sticky="w")
    median_label.grid(row=1, column=1, pady=5, sticky="w")

    min_label = Label(data_summary_frame, text="Min: ")
    max_label = Label(data_summary_frame, text="Max: ")
    min_label.grid(row=2, column=0, pady=5, sticky="w")
    max_label.grid(row=2, column=1, pady=5, sticky="w")

    std_label = Label(data_summary_frame, text="Standard Deviation: ")
    std_label.grid(row=3, column=0, pady=5, sticky="w")
    cpk_label = Label(data_summary_frame, text="CPK: ")
    cpk_label.grid(row=3, column=1, pady=5, sticky="w")

    samples_label = Label(data_summary_frame, text="Number of Samples: ")
    samples_label.grid(row=4, column=0, pady=5, sticky="w")
    absolute_label = Label(data_summary_frame, text="Specification Limits: ")
    absolute_label.grid(row=4, column=1, pady=5, sticky="w")

    percent_below_label = Label(data_summary_frame, text="Percent Below Limit: ")
    percent_above_label = Label(data_summary_frame, text="Percent Above Limit: ")
    percent_below_label.grid(row=5, column=0, pady=5, sticky="w")
    percent_above_label.grid(row=5, column=1, pady=5, sticky="w")

    percent_ok_label = Label(data_summary_frame, text="Percent Within Limits: ")
    percent_nok_label = Label(data_summary_frame, text="Percent Outside Limits: ")
    percent_ok_label.grid(row=6, column=0, pady=5, sticky="w")
    percent_nok_label.grid(row=6, column=1, pady=5, sticky="w")

    custom_lower_entry_sv = tk.StringVar()
    custom_lower_entry_sv.trace("w", lambda name, index, mode, sv=custom_lower_entry_sv: _populate_report_frame(
        just_update_custom_limits=True))
    lower_limit_entry = LabelRestrictedEntryFrame(data_summary_frame, "Custom Lower Limit: ",
                                                  text_variable=custom_lower_entry_sv)
    custom_upper_entry_sv = tk.StringVar()
    custom_upper_entry_sv.trace("w", lambda name, index, mode, sv=custom_lower_entry_sv: _populate_report_frame(
        just_update_custom_limits=True))
    upper_limit_entry = LabelRestrictedEntryFrame(data_summary_frame, "Custom Upper Limit: ",
                                                  text_variable=custom_upper_entry_sv)
    lower_limit_entry.grid(row=7, column=0, pady=20, sticky="w")
    upper_limit_entry.grid(row=7, column=1, pady=20, sticky="w")

    percent_below_custom_label = Label(data_summary_frame, text="Percent Below Custom Limit: ")
    percent_above_custom_label = Label(data_summary_frame, text="Percent Above Custom Limit: ")
    percent_below_custom_label.grid(row=8, column=0, pady=5, sticky="w")
    percent_above_custom_label.grid(row=8, column=1, pady=5, sticky="w")

    percent_good_custom_label = Label(data_summary_frame, text="Percent Within Custom Limits: ")
    percent_bad_custom_label = Label(data_summary_frame, text="Percent Outside Custom Limits: ")
    percent_good_custom_label.grid(row=9, column=0, pady=5, sticky="w")
    percent_bad_custom_label.grid(row=9, column=1, pady=5, sticky="w")

    cust_cpk_label = Label(data_summary_frame, text="CPK For Custom Limits: ")
    cust_cpk_label.grid(row=10, column=0, pady=5, sticky="w")

    data_summary_frame.grid(column=1, row=0)

    # Layout the overall figure
    oal_figure = plt.figure(figsize=(6, 5))
    figure_canvas = FigureCanvasTkAgg(oal_figure, master=middle_frame)
    middle_frame.columnconfigure(0, weight=1)
    middle_frame.columnconfigure(1, weight=1)
    figure_canvas.draw()
    figure_canvas.get_tk_widget().grid(column=0, row=1, pady=10, ipady=10)

    # Layout the magnitude figure
    magnitude_figure = plt.figure(figsize=(7, 5))
    figure_canvas = FigureCanvasTkAgg(magnitude_figure, master=middle_frame)
    figure_canvas.draw()
    figure_canvas.get_tk_widget().grid(column=1, row=1, pady=10, ipady=10)

    report_scroll_canvas.create_window((0, 0), window=middle_frame, anchor=tk.NW)

    middle_frame.update_idletasks()
    bbox = report_scroll_canvas.bbox(tk.ALL)  # Get bounding box of canvas
    # Define the scrollable region as entire canvas with only the desired width/height
    report_scroll_canvas.configure(scrollregion=bbox, width=bbox[2], height=1050)

    footer_frame = Frame(report_frame)
    footer_frame.grid_columnconfigure(0, weight=1)
    footer_frame.grid_columnconfigure(1, weight=1)

    generate_report_button = Button(footer_frame, text="Create Report", style="Bold.TButton",
                                    command=_create_report_pressed)
    add_images_button = Button(footer_frame, text="Add Report Images", style="Bold.TButton", command=add_report_images)
    add_images_button.grid(row=0, column=0, sticky="e", pady=10, padx=10)
    generate_report_button.grid(row=0, column=1, sticky="w", pady=10, padx=10)
    footer_frame.pack(fill="x")


def _populate_report_frame(just_update_custom_limits=False):
    """
    Populates the report frame with data from the stack manager
    :param just_update_custom_limits: If True, only features related to the custom limits are updated
    :return:
    """

    global stack_manager, arrow_figure, middle_frame, mean_label, median_label, min_label, max_label, samples_label, \
        report_scroll_canvas, std_label, cpk_label, stack_type_combo, oal_figure, magnitude_figure

    if not stack_manager:
        return

    radial_stack_bool = stack_type_combo.get() == "Radial Stack"
    if radial_stack_bool:
        stack_manager.one_d_stack = False

    stack_manager.calculate_stack(radial_stack_bool)
    lengths = stack_manager.calc_oal_dist()

    if radial_stack_bool:
        # This is a radial stack, base off of magnitudes
        lengths = lengths_to_magnitudes(lengths)

    plt.clf()

    custom_limits = None
    try:
        custom_limits = [float(custom_lower_entry_sv.get()), float(custom_upper_entry_sv.get())]
    except Exception:
        # Cant convert the entered values into limits
        pass

    summary_data = stack_manager.get_summary_data(lengths, cust_limits=custom_limits)

    if summary_data.percent_below_cust_lsl is not None:
        percent_below_custom_label.config(
            text=f"Percent Below Custom Lower Limit: {round(summary_data.percent_below_cust_lsl, _DECIMAL_PLACES)}%")
        percent_above_custom_label.config(
            text=f"Percent Above Custom Upper Limit: {round(summary_data.percent_above_cust_usl, _DECIMAL_PLACES)}%")
        percent_good_custom_label.config(
            text=f"Percent Within Custom Limits: {round(summary_data.percent_cust_ok, _DECIMAL_PLACES)}%")
        percent_bad_custom_label.config(
            text=f"Percent Outside Custom Limits: {round(summary_data.percent_cust_nok, _DECIMAL_PLACES)}%")

        cpk = get_cpk(custom_limits[0], custom_limits[1], lengths.mean(), np.std(lengths))
        cust_cpk_label.config(text=f"CPK Given Custom Limits: {round(cpk, _DECIMAL_PLACES)}")

    if just_update_custom_limits:
        return

    # Update all labels

    mean_label.config(text=f"Mean: {round(summary_data.mean, _DECIMAL_PLACES)}")
    median_label.config(text=f"Median: {round(summary_data.median, _DECIMAL_PLACES)}")
    min_label.config(text=f"Minimum: {round(summary_data.min, _DECIMAL_PLACES)}")
    max_label.config(text=f"Maximum: {round(summary_data.max, _DECIMAL_PLACES)}")
    std_label.config(text=f"Standard Deviation: {round(summary_data.std, _DECIMAL_PLACES)}")
    samples_label.config(text=f"Number of Samples: {summary_data.samples}")
    if summary_data.target_limits and summary_data.target_limits[0] is not None and \
            summary_data.target_limits[1] is not None:
        absolute_label.config(text=f"Specification Limits:  {summary_data.target_limits}")
        percent_below_label.config(
            text=f"Percent Below Lower Specification Limit: {round(summary_data.percent_below_lsl, _DECIMAL_PLACES)}%")
        percent_above_label.config(
            text=f"Percent Above Upper Specification Limit: {round(summary_data.percent_above_usl, _DECIMAL_PLACES)}%")
        percent_ok_label.config(
            text=f"Percent Within Specification Limits: {round(summary_data.percent_ok, _DECIMAL_PLACES)}%")
        percent_nok_label.config(
            text=f"Percent Outside Specification Limits: {round(summary_data.percent_nok, _DECIMAL_PLACES)}%")
        cpk_label.config(text=f"CPK: {round(summary_data.cpk, _DECIMAL_PLACES)}")

    else:
        absolute_label.config(text=f"Specification Limits: Not Defined")

    # Update arrow diagram
    arrow_figure.clf()
    arrow_figure.set_facecolor(_MPL_BACKGROUND)
    stack_manager.create_arrow_diagram(arrow_figure.gca())
    arrow_figure.canvas.draw()
    arrow_figure.canvas.flush_events()

    # Create summaries for each stackup step
    for stackup_it in enumerate(stack_manager.stackup_steps):
        row = stackup_it[0] + 2
        middle_frame.grid_rowconfigure(row, weight=1)
        lengths = stackup_it[1].lengths

        # Create histogram
        hist_figure = plt.figure(figsize=(10, 5))
        figure_canvas = FigureCanvasTkAgg(hist_figure, master=middle_frame)
        figure_canvas.draw()
        figure_canvas.get_tk_widget().grid(column=0, row=row, pady=30, ipady=50)
        hist_figure.set_facecolor(_MPL_BACKGROUND)
        hist_figure = StackManager.create_oal_diagram(None, hist_figure.gca(), lengths, radial_stack=radial_stack_bool)
        hist_figure.set_title(f"Distribution Of Part: {stackup_it[1].part_name}, {stackup_it[1].description}")
        stackup_it[1].image = _get_axis_image(hist_figure)

        summary_table = Frame(middle_frame)
        summary_table.grid_columnconfigure(0, weight=1)
        summary_table.grid_columnconfigure(1, weight=1)
        summary_table.grid_rowconfigure(0, weight=1)
        summary_table.grid_rowconfigure(1, weight=1)
        summary_table.grid_rowconfigure(2, weight=1)
        summary_table.grid_rowconfigure(3, weight=1)

        if radial_stack_bool:
            # This is a radial stack, base off of magnitudes
            lengths = lengths_to_magnitudes(lengths)

        title_label = Label(summary_table, text=f"Summary For Part: {stackup_it[1].part_name}, "
                                                f"{stackup_it[1].description} ", justify="center", anchor="center",
                            font=("Arial bold", 12))
        title_label.grid(row=0, column=0, columnspan=2, sticky=tk.W + tk.E, pady=15)

        Label(summary_table, text=f"Mean: {round(lengths.mean(), 2)}").grid(row=1, column=0, pady=5, sticky="w")
        Label(summary_table, text=f"Median: {round(np.median(lengths), 2)}").grid(row=1, column=1, pady=5,
                                                                                  sticky="w")

        Label(summary_table, text=f"Min: {round(min(lengths), 2)}").grid(row=2, column=0, pady=5, sticky="w")
        Label(summary_table, text=f"Max: {round(max(lengths), 2)}").grid(row=2, column=1, pady=5, sticky="w")

        Label(summary_table, text=f"Number of Samples: {round(stackup_it[1].distribution.num_samples, 2)}").grid \
            (row=3, column=0, pady=5, sticky="w")

        summary_table.grid(column=1, row=row, pady=10)

        figure_canvas.draw()
        figure_canvas.flush_events()

    if radial_stack_bool:
        # Need to resize figures, thus create a new oal figure
        oal_figure.clf()
        oal_figure.canvas.get_tk_widget().grid_remove()
        oal_figure = plt.figure(figsize=(6, 5))
        figure_canvas = FigureCanvasTkAgg(oal_figure, master=middle_frame)
        figure_canvas.get_tk_widget().columnconfigure(0, weight=1)
        figure_canvas.get_tk_widget().columnconfigure(1, weight=1)
        oal_figure.canvas.get_tk_widget().grid(column=0, row=1, columnspan=1, ipady=40)
        stack_manager.create_oal_diagram(oal_figure.gca())
        oal_figure.gca().set_title("Overall Stackup Result")

        magnitude_figure.clf()
        magnitude_figure.set_facecolor(_MPL_BACKGROUND)
        magnitude_figure.canvas.get_tk_widget().grid(column=1, row=1, ipady=10)
        stack_manager.create_magnitude_diagram(magnitude_figure.gca())
        magnitude_figure.canvas.draw()
        magnitude_figure.canvas.flush_events()

    else:
        oal_figure.clf()
        oal_figure.canvas.get_tk_widget().grid_remove()
        oal_figure = plt.figure(figsize=(16, 5))
        figure_canvas = FigureCanvasTkAgg(oal_figure, master=middle_frame)
        figure_canvas.get_tk_widget().columnconfigure(0, weight=1)
        oal_figure.canvas.get_tk_widget().grid(column=0, row=1, columnspan=2, pady=10, ipady=10)
        stack_manager.create_oal_diagram(oal_figure.gca())
        oal_figure.gca().set_title("Histogram Of Stackup Result")

        magnitude_figure.clf()
        magnitude_figure.canvas.get_tk_widget().grid_remove()

    oal_figure.set_facecolor(_MPL_BACKGROUND)
    oal_figure.canvas.draw()
    oal_figure.canvas.flush_events()

    # Update the frame/scrollbar to reflect the frame
    bbox = report_scroll_canvas.bbox(tk.ALL)  # Get bounding box of canvas
    report_scroll_canvas.configure(scrollregion=bbox, width=bbox[2], height=1000)


def add_report_images():
    """
    Opens a dialog box to select image files which are then added to the stack manager
    :return:
    """
    filename = filedialog.askopenfilenames(title="Select file", filetypes=[("Image files", ".png .jpg")])
    stack_manager.add_report_image_paths(filename)


def _update_scroll_canvas_width(event):
    """
    Event that appropriately resizes the srcoll canvas
    :param event:
    :return:
    """
    canvas_width = event.width
    setup_scroll_canvas.itemconfig(setup_scroll_canvas_frame, width=canvas_width)


def _on_frame_configure(_):
    setup_scroll_canvas.configure(scrollregion=setup_scroll_canvas.bbox("all"))


def _save_pressed():
    """
    Function that handles the save button being pressed
    :return:
    """
    _generate_stack_manager()

    # Get file location, and save to a file
    filename = filedialog.asksaveasfilename(title="Select file",
                                            filetypes=(("Pickle", "*.pickle"), ("all files", "*.*")))
    # Add file name to end if not there
    if filename[-7:] != ".pickle":
        filename += ".pickle"

    file = open(filename, "ab")
    pickle.dump(stack_manager, file)
    file.close()


def _load_pressed():
    """
    Loads the data from a file, saves it into the stack manager, and updates the display
    :return:
    """
    global stack_manager

    # Load the data
    filename = filedialog.askopenfilename(title="Select file", filetypes=(("Pickle", "*.pickle"), ("all files", "*.*")))
    file = open(filename, 'rb')
    stack_manager = pickle.load(file)

    # Update the setup interface
    # Clear the current list
    for row_entry in row_entries:
        row_entries.remove(row_entry)
        row_entry.destroy()

    _generate_stackup_steps()


def _stack_type_change():
    """
    Function that handles the stack type being changed and updates the interface accordingly
    :return:
    """

    # Add or removes the lower limit if the stack type has changed
    if stack_type_combo.get() == "Radial Stack":
        oal_lsl_lref.grid_remove()
    else:
        oal_lsl_lref.grid(row=0, column=0)


def _create_report_pressed():
    """
    Creates a file dialog and saves a pdf version of the report accordingly
    :return:
    """
    filename = filedialog.asksaveasfilename(title="Select file", filetypes=(("PDF", "*.pdf"), ("all files", "*.*")))

    # Add pdf to end if it's not already there
    if filename[-4:] != ".pdf":
        filename += ".pdf"

    image_list = _get_standard_plot_images()
    report_generator = ReportGenerator(stack_manager, title_entry.get(), author_entry.get(), revision_entry.get())
    report_generator.create_report(filename, image_list)


def _get_standard_plot_images():
    """
    Gets the standard images for the plots
    :return: A list of images
    """
    image_list = [_get_axis_image(arrow_figure), _get_axis_image(oal_figure)]

    if stack_type_combo.get() == "Radial Stack":
        image_list.append(_get_axis_image(magnitude_figure))

    return image_list


def _get_axis_image(axs):
    """
    Creates an image of a given matplotlib axis
    :param axs: The axis to create an image for
    :return: The image representing the plot
    """
    image_data = BytesIO()
    axs.get_figure().savefig(image_data, format='png', bbox_inches='tight')
    image_data.seek(0)
    plt.close()
    return image_data


def _add_part_pressed():
    """
    Handles the add part button being pressed
    :return:
    """
    # Create an interface row
    interface_entry = StackRow(table_frame, True)
    interface_entry.pack(fill="x")
    row_entries.append(interface_entry)

    # Create a part row
    part_entry = StackRow(table_frame, False, mating_interface=interface_entry)
    part_entry.pack(fill="x")
    row_entries.append(part_entry)


def _calculate_button_pressed():
    """
    Handles the calculate button being pressed
    :return:
    """
    _generate_stack_manager()
    tab_control.select(1)
    _populate_report_frame()


def _generate_stackup_steps():
    """
    Creates stackup steps and displays theme in the interface given the stackup manager
    :return:
    """
    prior_part = None
    inner_row = 0

    for stackup_step in enumerate(stack_manager.stackup_steps):

        # Generate Values & Text Arrays for lref
        if stackup_step[1].distribution.name == "Normal":
            text = StackRow.NORMAL_TEXT
            combo_text = "Normal Distribution"
            values = [stackup_step[1].distribution.mean, stackup_step[1].distribution.std,
                      stackup_step[1].distribution.lower_lim,
                      stackup_step[1].distribution.upper_lim, None]

        elif stackup_step[1].distribution.name == "Uniform":
            combo_text = "Uniform Distribution"
            text = StackRow.UNIFORM_TEXT
            values = [stackup_step[1].distribution.lower_lim, stackup_step[1].distribution.upper_lim, None, None, None]
        elif stackup_step[1].distribution.name == "Skewed Normal":
            combo_text = "Skewed Distribution"
            text = StackRow.SKEW_TEXT
            values = [stackup_step[1].distribution.mean, stackup_step[1].distribution.std,
                      stackup_step[1].distribution.skew,
                      stackup_step[1].distribution.lower_lim, stackup_step[1].distribution.upper_lim]
        else:
            raise ValueError('Distribution has an unaccounted for value')

        description = stackup_step[1].description
        part_name = stackup_step[1].part_name

        if len(row_entries) == 0:  # First entry
            row_entry = StackRow(table_frame, init_entry=True)
            prior_part = row_entry
            row_entry.set_lref_values(description, part_name, text, values, inner_row)
            row_entry.pack(fill="x")
            row_entries.append(row_entry)
            row_entries[-1].dist_combo[inner_row].delete(0, "end")
            row_entries[-1].dist_combo[inner_row].insert(0, combo_text)

        elif stackup_step[1].is_interface:
            inner_row = 0
            row_entry = StackRow(table_frame, stackup_step[1].is_interface, mating_interface=prior_part)
            row_entry.set_lref_values(description, part_name, text, values, inner_row)
            row_entry.pack(fill="x")
            row_entries.append(row_entry)
            row_entries[-1].dist_combo[inner_row].delete(0, "end")
            row_entries[-1].dist_combo[inner_row].insert(0, combo_text)

        else:
            if stack_manager.stackup_steps[stackup_step[0] - 1].part_name == stackup_step[1].part_name:
                inner_row += 1
                # Add a row, don't make a new entry (it's still the same part)
                row_entries[-1].add_inner_row()
                row_entries[-1].set_lref_values(description, part_name, text, values, inner_row)
                row_entries[-1].dist_combo[inner_row].delete(0, "end")
                row_entries[-1].dist_combo[inner_row].insert(0, combo_text)

            else:
                inner_row = 0
                if row_entries[-1].is_interface:
                    prior_part = stackup_step[1]

                # Create a new row entry
                row_entry = StackRow(table_frame, stackup_step[1].is_interface)
                row_entry.set_lref_values(description, part_name, text, values, inner_row)
                row_entry.pack(fill="x")
                row_entries.append(row_entry)
                row_entries[-1].dist_combo[inner_row].delete(0, "end")
                row_entries[-1].dist_combo[inner_row].insert(0, combo_text)


def _generate_stack_manager():
    """
    Creates the stackup manager given the rows currently within the interface
    :return:
    """
    global stack_manager
    # Create a Stack Manager and items
    stack_manager = StackManager()

    for row_entry in row_entries:
        part_name = row_entry.part_entry.get()
        for stackup_step_it in range(len(row_entry.description_entry)):
            description_name = row_entry.description_entry[stackup_step_it].get()

            # Generate Values Array
            values = np.zeros(5)
            for lref_it in enumerate(row_entry.lr_list[stackup_step_it]):
                try:
                    values[lref_it[0]] = float(lref_it[1].get_text())
                except ValueError:
                    continue

            if row_entry.dist_combo[stackup_step_it].get() == "Normal Distribution":
                distribution = distributions.Normal(values[0], values[1], lower_lim=values[2], upper_lim=values[3])

            elif row_entry.dist_combo[stackup_step_it].get() == "Uniform Distribution":
                distribution = distributions.Uniform(nominal=(values[0] + values[1]) / 2,
                                                     tolerance=(values[1] - values[0]) / 2)
                pass
            elif row_entry.dist_combo[stackup_step_it].get() == "Skewed Distribution":
                distribution = distributions.SkewedNormal(skew=values[2], mean=values[0],
                                                          std=values[1], lower_lim=values[3], upper_lim=values[4])
            elif row_entry.dist_combo[stackup_step_it].get() == "No Stack Contribution":
                continue
            else:
                raise ValueError('Combobox has an unaccounted for value')

            stackup_step = StackupStep(part_name=part_name, description=description_name, distribution=distribution,
                                       is_interface=row_entry.is_interface)

            stack_manager.add_part(stackup_step)

    try:
        stack_manager.oal_lsl = float(oal_lsl_lref.get_text())
    except ValueError:
        pass  # The entry does not have a valid limit
    try:
        stack_manager.oal_usl = float(oal_usl_limit_lref.get_text())
    except ValueError:
        pass  # The entry does not have a valid limit

    return stack_manager


class RestrictedEntry(tk.Entry):
    """A child of the entry class that is restricted to only allow floats to be entered"""

    def __init__(self, master=None, text_variable=None, **kwargs):
        if not text_variable:
            text_variable = tk.StringVar()

        tk.Entry.__init__(self, master, textvariable=text_variable, **kwargs)

        self.old_value = ''
        text_variable.trace('w', self._check)
        self.get, self.set = text_variable.get, text_variable.set

    def _check(self, *args):
        """
        Verifies whether or not the current value is a valid float
        :param args:
        :return:
        """
        try:
            float(self.get())
            # The current value is a valid float
            self.old_value = self.get()
        except ValueError:
            # Not a valid float -> reject
            if self.get() != "" and self.get() != "-":
                self.set(self.old_value)


class LabelRestrictedEntryFrame(ttk.Frame):
    """
    A combination of a label and a restricted entry, placed abutting each other
    """

    def __init__(self, master=None, text="", text_variable=None, **kwargs):
        Frame.__init__(self, master, **kwargs)
        self.label_text = tk.StringVar()
        self.label_text.set(text)

        self.label = Label(self, textvariable=self.label_text, justify="right", anchor="e")
        self.spacer = Frame(self, width=5, height=30)
        self.restricted_entry = RestrictedEntry(self, width=10, text_variable=text_variable)
        self.restricted_entry.insert(0, "TEXT")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self.show()

    def set_text(self, text):
        """
        Sets the text of the label
        :param text: The text that the label should display
        :return: None
        """
        self.label_text.set(text)

    def set_value(self, value):
        """
        Sets the value of the entry
        :param value: The text that the label should display
        :return: None
        """
        self.restricted_entry.set(value)

    def get_text(self):
        """
        Gets the text of the entry
        :return: the text of the entry
        """
        return self.restricted_entry.get()

    def hide(self):
        """
        Hides the elements of the LabelRestrictedEntryFrame
        :return:
        """
        self.label.grid_forget()
        self.spacer.grid_forget()
        self.restricted_entry.grid_forget()

    def show(self):
        """
        Shows and places appropriately the elements of the LabelRestrictedEntryFrame
        :return:
        """
        self.label.grid(row=0, column=0, sticky ="nsew")
        self.spacer.grid(row=0, column=1, sticky ="nsew")
        self.restricted_entry.grid(row=0, column=2, sticky ="nsew")


class StackRow(tk.Frame):
    """
    A class containing all interface elements for a StackRow (A part or interface row entry)
    Can contain multiple different stackup steps within this row
    """
    COMBO_OPTIONS = ["Normal Distribution", "Uniform Distribution", "Skewed Distribution", "No Stack Contribution"]

    # Text displayed for each label next to an entry. In order.
    NORMAL_TEXT = ["Mean", "Standard Deviation", "Lower Cutoff", "Upper Cutoff", None]
    UNIFORM_TEXT = ["Lower Limit", "Upper Limit", None, None, None]
    SKEW_TEXT = ["Mean", "Standard Deviation", "Skew", "Lower Cutoff", "Upper Cutoff"]
    NO_STACK_TEXT = [None, None, None, None, None]

    def __init__(self, master=None, is_interface=False, mating_interface=None, init_entry=False, **kwargs):
        """
        :param master:
        :param is_interface: Whether or not the row entry is an interface
        :param mating_interface: A stack row that represents the mating interface if it is present. Will be destroyed
        when all stack steps are removed
        :param kwargs:
        """
        tk.Frame.__init__(self, master, **kwargs, highlightthickness=1, highlightbackground="grey")

        self.is_interface = is_interface
        self.mating_interface = mating_interface
        self.init_entry = init_entry

        # Setup left right and inner frames
        self.left_frame = Frame(self)
        self.inner_frame = Frame(self)
        self.right_frame = Frame(self, width=50)

        self.left_frame.pack(side="left", padx=20)
        self.inner_frame.pack(side="left", padx=20)
        self.right_frame.pack(side="right", padx=20)

        # Setup Part Name Entry
        self.part_entry = Entry(self.left_frame, width=20, justify="center")

        if is_interface:
            part_label_text = "Interface"
        else:
            part_label_text = "Part"

        self.part_entry.insert(0, part_label_text)
        self.part_entry.pack(side="left", fill="x", padx=10)

        # Cannot have multiple steps for an interface
        if not is_interface:
            # Setup add and remove buttons
            self.remove_button = Button(self.right_frame, text="-", command=self.remove_inner_row, style="Bold.TButton")
            self.remove_button.pack(side="right", padx=5)
            self.add_button = Button(self.right_frame, text="+", command=self.add_inner_row, style="Bold.TButton")
            self.add_button.pack(side="right", padx=5)

        # Setup left inner and right inner frames
        # This is where each individual stackup step goes, and can be expanded/contracted by the +/- buttons
        self.left_inner_frame = Frame(self.inner_frame)
        self.right_inner_frame = Frame(self.inner_frame)
        self.left_inner_frame.pack(side="left", padx=20)
        self.right_inner_frame.pack(side="right", padx=20)

        # Lists of widgets that can be expanded/contracted
        self.description_entry = []
        self.dist_combo = []
        self.lr_list = []

        # Setup the column widths
        self.left_inner_frame.grid_columnconfigure(0, weight=1)
        self.left_inner_frame.grid_columnconfigure(1, weight=1)
        for i in range(0, len(self.NORMAL_TEXT)):
            self.right_inner_frame.grid_columnconfigure(i, weight=1)

        self.add_inner_row()

    def remove_inner_row(self, init_entry_override=False):
        """
        Removes an inner row for a stackup step within a part, updating lists and destroying widgets
        :return: None
        """

        # Don't remove the first entry
        if self.init_entry and len(self.lr_list) == 1 and not init_entry_override:
            return

        # Destroy widgets
        self.dist_combo[-1].destroy()
        self.description_entry[-1].destroy()
        for lref in self.lr_list[-1]:
            lref.destroy()

        row = len(self.lr_list) - 1
        # Remove from lists
        self.dist_combo.pop(row)
        self.description_entry.pop(row)
        self.lr_list.pop(row)

        # If there are no stackup steps left, destroy this stackup row and any mating interface
        if len(self.lr_list) == 0:
            if self.mating_interface:
                row_entries.remove(self.mating_interface)
                self.mating_interface.destroy()
            row_entries.remove(self)
            self.destroy()

    def add_inner_row(self):
        """
        Adds an inner row for a stackup step within a part
        :return: None
        """
        row = len(self.lr_list)
        self.left_inner_frame.rowconfigure(row, weight=1)
        self.right_inner_frame.rowconfigure(row, weight=1)

        self.description_entry.append(Entry(self.left_inner_frame, width=20, justify="center"))
        self.description_entry[-1].insert(0, "Description")

        self.dist_combo.append(Combobox(self.left_inner_frame, values=self.COMBO_OPTIONS, width=20, justify="center"))
        self.dist_combo[-1].set(self.COMBO_OPTIONS[0])
        self.dist_combo[-1].bind("<<ComboboxSelected>>", lambda event: self._combo_selection_change(event, row))
        self.description_entry[-1].grid(row=row, column=0)
        self.dist_combo[-1].grid(row=row, column=1)

        inner_lr_list = []
        for it in enumerate(self.NORMAL_TEXT):
            inner_lr_list.append(LabelRestrictedEntryFrame(self.right_inner_frame, it[1]))
            inner_lr_list[it[0]].grid(row=row, column=it[0], padx=10)
            if it[1] is None:
                inner_lr_list[it[0]].hide()

        self.lr_list.append(inner_lr_list)

    def _combo_selection_change(self, event, row):
        if self.dist_combo[row].get() == "Normal Distribution":
            self.update_lref_display(self.NORMAL_TEXT, row)
        elif self.dist_combo[row].get() == "Uniform Distribution":
            self.update_lref_display(self.UNIFORM_TEXT, row)
        elif self.dist_combo[row].get() == "Skewed Distribution":
            self.update_lref_display(self.SKEW_TEXT, row)
            return
        elif self.dist_combo[row].get() == "No Stack Contribution":
            self.update_lref_display(self.NO_STACK_TEXT, row)
            return
        else:
            raise ValueError('Combobox has an unaccounted for value')

    def update_lref_display(self, text, row):
        """
        Sets text and shows/hide elements of the lr_list appropriately. If a None entry is identified, the
        lref is hidden.
        :param text: A tuple of str or none values
        :param row: The row to update the LREFs for
        :return: None
        """
        for i in range(0, len(self.lr_list[row])):
            if text[i] is None:
                self.lr_list[row][i].hide()
            else:
                self.lr_list[row][i].show()
                self.lr_list[row][i].set_text(text[i])

    def set_lref_values(self, description, part_name, text, values, row):
        """
        Sets values and test of the lr_list appropriately. If a None entry is identified, the lref is hidden.
        :param text: A tuple of str or none values
        :param values: A tuple of values to set the entry to
        :param row: The row to update the LREFs for
        :return:
        """
        self.description_entry[row].delete(0, "end")
        self.description_entry[row].insert(0, description)
        self.part_entry.delete(0, "end")
        self.part_entry.insert(0, part_name)
        self.update_lref_display(text, row)
        for i in range(0, len(self.lr_list[row])):
            if values[i] is not None:
                self.lr_list[row][i].set_value(values[i])
