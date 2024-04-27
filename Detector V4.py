import os
import re
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from ttkbootstrap import Style
from tqdm import tqdm, tqdm_gui
import threading
import time


class SourceCodeVulnerabilityDetectionDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        style = Style(theme="simplex")
        self.title("Detector")
        self.geometry("800x600")
        self.resizable(True, True)  # Enable window resizing

        self.source_code_folder = ""
        self.wordlist_file = ""
        self.results = []
        self.skipped_files = []
        self.config_file = "config.json"
        self.notepad_path = r"C:\Program Files\Notepad++\notepad++.exe"  # Update with the correct path
        self.menu_config = {}

        self.create_menu()
        self.create_dashboard()
        line_number_tag = "line_number"
        line_number_color = "red"

    def create_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Start", command=self.start_search)
        file_menu.add_command(label="Export", command=self.export_results)
        file_menu.add_command(label="Export Skipped Files",
                              command=self.export_skipped_files)  # Add Export Skipped Files option
        menubar.add_cascade(label="File", menu=file_menu)

        # Add the about submenu
        about_menu = tk.Menu(menubar, tearoff=0)
        about_menu.add_command(label="About", command=self.show_about_info)

        menubar.add_cascade(label="About", menu=about_menu)

        # Add the settings submenu
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Change Notepad++ Executable", command=self.browse_notepad_executable)


        menubar.add_cascade(label="Settings", menu=settings_menu)

        self.config(menu=menubar)

    def create_dashboard(self):
        notebook = ttk.Notebook(self)

        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        browse_frame = tk.Frame(notebook)
        notebook.add(browse_frame, text="Start")
        preview_frame = tk.Frame(notebook)
        notebook.add(preview_frame, text="Preview")

        results_frame = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create the widgets in the browse_frame
        source_label = tk.Label(browse_frame, text="Source Code Folder:")
        source_label.grid(row=0, column=0, sticky=tk.W, pady=5)

        self.source_entry = tk.Entry(browse_frame, width=50)
        self.source_entry.grid(row=0, column=1, padx=5, pady=5)

        source_browse_button = tk.Button(browse_frame, text="Browse", command=self.browse_source_folder)
        source_browse_button.grid(row=0, column=2, padx=5, pady=5)

        wordlist_label = tk.Label(browse_frame, text="Wordlist File:")
        wordlist_label.grid(row=1, column=0, sticky=tk.W, pady=5)

        self.wordlist_entry = tk.Entry(browse_frame, width=50)
        self.wordlist_entry.grid(row=1, column=1, padx=5, pady=5)

        wordlist_browse_button = tk.Button(browse_frame, text="Browse", command=self.browse_wordlist_file)
        wordlist_browse_button.grid(row=1, column=2, padx=5, pady=5)

        self.case_sensitive_var = tk.BooleanVar()
        self.case_sensitive_checkbutton = tk.Checkbutton(browse_frame, text="Case Sensitive",
                                                         variable=self.case_sensitive_var)
        self.case_sensitive_checkbutton.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)

        self.regex_var = tk.BooleanVar()
        self.regex_checkbutton = tk.Checkbutton(browse_frame, text="Regex", variable=self.regex_var)
        self.regex_checkbutton.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        search_button = tk.Button(browse_frame, text="Start Detector", command=self.start_search)
        search_button.grid(row=3, column=1, pady=10)

        # Create the widgets in the preview_frame
        self.preview_text = tk.Text(preview_frame, wrap=tk.WORD, state=tk.DISABLED, height=5)
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        button_frame = tk.Frame(preview_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        open_button = tk.Button(button_frame, text="Open in Notepad++", command=self.open_file_in_notepad)
        open_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.mark_positive_button = tk.Button(button_frame, text="Mark as True Positive", state=tk.DISABLED,
                                              command=self.mark_as_true_positive)
        self.mark_positive_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.mark_negative_button = tk.Button(button_frame, text="Mark as False Positive", state=tk.DISABLED,
                                              command=self.mark_as_false_positive)
        self.mark_negative_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Create the widgets in the results_frame
        self.results_treeview = ttk.Treeview(results_frame,
                                             columns=("Index", "File Path", "Line Number", "Keyword", "Preview"),
                                             show="headings")
        self.results_treeview.heading("Index", text="S.No", command=lambda: self.sort_results("Index"))
        self.results_treeview.heading("File Path", text="File Path",
                                       command=lambda: self.sort_results("File Path"))
        self.results_treeview.heading("Line Number", text="Line Number",
                                       command=lambda: self.sort_results("Line Number"))
        self.results_treeview.heading("Keyword", text="Keyword", command=lambda: self.sort_results("Keyword"))
        self.results_treeview.heading("Preview", text="Preview")
        self.results_treeview.column("Index", width=50, anchor=tk.CENTER)
        self.results_treeview.column("File Path", width=200, anchor=tk.CENTER)
        self.results_treeview.column("Line Number", width=100, anchor=tk.CENTER)
        self.results_treeview.column("Keyword", width=100, anchor=tk.CENTER)
        self.results_treeview.column("Preview", width=300)

        scroll_bar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_treeview.yview)
        scroll_bar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_treeview.configure(yscrollcommand=scroll_bar.set)

        self.results_treeview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.results_treeview.bind("<<TreeviewSelect>>", self.preview_selected_file)

        browse_frame.columnconfigure(1, weight=1)
        browse_frame.rowconfigure(3, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        results_frame.columnconfigure(0, weight=1)

    def open_file_in_notepad(self):
        selected_item = self.results_treeview.selection()[0]
        file_path = self.results_treeview.item(selected_item, "values")[1]
        line_number = self.results_treeview.item(selected_item, "values")[2]

        if os.path.exists(self.notepad_path):
            command = [self.notepad_path, "-n" + str(line_number), file_path]
            subprocess.Popen(command)
        else:
            messagebox.showinfo("Info", "Notepad++ executable not found.")
            self.browse_notepad_executable()

    def browse_notepad_executable(self):
        file_path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
        if file_path:
            self.notepad_path = file_path

    def create_search_frame(self):
        search_frame = tk.Frame(self)
        search_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        source_label = tk.Label(search_frame, text="Source Code Folder:")
        source_label.grid(row=0, column=0, sticky=tk.W, pady=5)

        self.source_entry = tk.Entry(search_frame, width=50)
        self.source_entry.grid(row=0, column=1, padx=5, pady=5)

        source_browse_button = tk.Button(search_frame, text="Browse", command=self.browse_source_folder)
        source_browse_button.grid(row=0, column=2, padx=5, pady=5)

        wordlist_label = tk.Label(search_frame, text="Wordlist File:")
        wordlist_label.grid(row=1, column=0, sticky=tk.W, pady=5)

        self.wordlist_entry = tk.Entry(search_frame, width=50)
        self.wordlist_entry.grid(row=1, column=1, padx=5, pady=5)

        wordlist_browse_button = tk.Button(search_frame, text="Browse", command=self.browse_wordlist_file)
        wordlist_browse_button.grid(row=1, column=2, padx=5, pady=5)

        self.case_sensitive_var = tk.BooleanVar()
        self.case_sensitive_checkbutton = tk.Checkbutton(search_frame, text="Case Sensitive",
                                                         variable=self.case_sensitive_var)
        self.case_sensitive_checkbutton.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)

        self.regex_var = tk.BooleanVar()
        self.regex_checkbutton = tk.Checkbutton(search_frame, text="Regex", variable=self.regex_var)
        self.regex_checkbutton.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        search_button = tk.Button(search_frame, text="Start Search", command=self.start_search)
        print("entered start button only")
        search_button.grid(row=3, column=1, pady=10)

        self.results_treeview = ttk.Treeview(search_frame,
                                             columns=("Index", "File Path", "Line Number", "Keyword", "Preview"),
                                             show="headings")
        self.results_treeview.heading("Index", text="S.No", command=lambda: self.sort_results("Index"))
        self.results_treeview.heading("File Path", text="File Path",
                                       command=lambda: self.sort_results("File Path"))
        self.results_treeview.heading("Line Number", text="Line Number",
                                       command=lambda: self.sort_results("Line Number"))
        self.results_treeview.heading("Keyword", text="Keyword", command=lambda: self.sort_results("Keyword"))
        self.results_treeview.heading("Preview", text="Preview")
        self.results_treeview.column("Index", width=50, anchor=tk.CENTER)
        self.results_treeview.column("File Path", width=200, anchor=tk.CENTER)
        self.results_treeview.column("Line Number", width=100, anchor=tk.CENTER)
        self.results_treeview.column("Keyword", width=100, anchor=tk.CENTER)
        self.results_treeview.column("Preview", width=300)
        self.results_treeview.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        scroll_bar = ttk.Scrollbar(search_frame, orient="vertical", command=self.results_treeview.yview)
        scroll_bar.grid(row=4, column=3, sticky="ns")
        self.results_treeview.configure(yscrollcommand=scroll_bar.set)

        self.results_treeview.bind("<<TreeviewSelect>>", self.preview_selected_file)

        search_frame.columnconfigure(1, weight=1)
        search_frame.rowconfigure(4, weight=1)

    def create_preview_frame(self):
        preview_frame = tk.Frame(self)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.preview_text = tk.Text(preview_frame, wrap=tk.WORD, state=tk.DISABLED, height=5)
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        button_frame = tk.Frame(preview_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        open_button = tk.Button(button_frame, text="Open in Notepad++", command=self.open_file_in_notepad)
        open_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.mark_positive_button = tk.Button(button_frame, text="Mark as True Positive", state=tk.DISABLED,
                                              command=self.mark_as_true_positive)
        self.mark_positive_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.mark_negative_button = tk.Button(button_frame, text="Mark as False Positive", state=tk.DISABLED,
                                              command=self.mark_as_false_positive)
        self.mark_negative_button.pack(side=tk.LEFT, padx=5, pady=5)

    def browse_source_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.source_code_folder = folder_path
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(tk.END, folder_path)

    def browse_wordlist_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            self.wordlist_file = file_path
            self.wordlist_entry.delete(0, tk.END)
            self.wordlist_entry.insert(tk.END, file_path)

    def start_search(self):
        self.clear_results()
        self.results_treeview.delete(*self.results_treeview.get_children())
        self.skipped_files = []

        if not self.source_code_folder or not self.wordlist_file:
            messagebox.showerror("Error", "Source code folder and wordlist file must be specified.")
            return

        keywords = self.get_keywords()
        if not keywords:
            messagebox.showerror("Error", "No keywords found in the wordlist file.")
            return

        case_sensitive = self.case_sensitive_var.get()
        regex = self.regex_var.get()

        progress_window = tk.Toplevel(self)
        progress_window.title("Progress")
        progress_window.geometry("300x100")
        progress_label = tk.Label(progress_window, text="Detector is Searching ! Please wait..")
        progress_label.pack(pady=10)
        progress_window.grab_set()

        progress_bar = ttk.Progressbar(progress_window, length=280, mode='indeterminate')
        progress_bar.pack()

        def search_task():
            try:
                for root, _, files in os.walk(self.source_code_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_extension = os.path.splitext(file)[1].lower()
                        try:
                            with open(file_path, "r") as f:
                                for line_number, line in enumerate(f, start=1):
                                    for keyword in keywords:
                                        if not case_sensitive:
                                            keyword = keyword.lower()
                                            line_lower = line.lower()
                                        else:
                                            line_lower = line

                                        if regex:
                                            match = re.search(keyword, line_lower)
                                            if match:
                                                self.results.append((file_path, line_number, keyword, line))
                                        else:
                                            if keyword in line_lower:
                                                self.results.append((file_path, line_number, keyword, line))

                        except UnicodeDecodeError:
                            self.skipped_files.append(file_path)
            finally:
                self.display_results()

        def search_thread():
            progress_bar.start()
            try:
                search_task()
            finally:
                progress_window.destroy()
                messagebox.showinfo("Detector", "Search Completed!")
                if self.skipped_files:
                    skipped_files_message = "The following files could not be processed:\n\n"
                    skipped_files_message += "\n".join(self.skipped_files)

                    messagebox.showinfo("Skipped Files", skipped_files_message, icon=messagebox.INFO,
                                        type=messagebox.OK)


        # Start the search in a separate thread
        search_thread = threading.Thread(target=search_thread)
        search_thread.start()

    def display_results(self):
        for index, result in enumerate(self.results, start=1):
            file_path, line_number, keyword, preview = result
            self.results_treeview.insert("", tk.END, text=index,
                                         values=(index, file_path, line_number, keyword, preview))

    def export_skipped_files(self):
        skipped_files_message = "The following files could not be processed:\n\n"
        skipped_files_message += "\n".join(self.skipped_files)

        save_location = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if save_location:
            with open(save_location, "w") as f:
                f.write(skipped_files_message)
            messagebox.showinfo("Skipped Files Saved", "Skipped files saved successfully.")

    def preview_selected_file(self, event):
        selected_item = self.results_treeview.selection()[0]
        index = self.results_treeview.item(selected_item, "text")
        file_path = self.results_treeview.item(selected_item, "values")[1]
        line_number = self.results_treeview.item(selected_item, "values")[2]
        keyword = self.results_treeview.item(selected_item, "values")[3]
        preview = self.results_treeview.item(selected_item, "values")[4]

        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(tk.END, f"Keyword: {keyword}\n\n")

        with open(file_path, "r") as f:
            lines = f.readlines()
            max_line_number_length = len(str(len(lines)))

            for i, line in enumerate(lines, start=1):
                line_number_text = str(i).rjust(max_line_number_length)
                line_with_indentation = f"  {line_number_text}:   {line}"
                if i == int(line_number):
                    self.preview_text.insert(tk.END, line_with_indentation, "selected_line")
                else:
                    self.preview_text.insert(tk.END, line_with_indentation)

        self.preview_text.tag_configure("selected_line", background="yellow")

        self.preview_text.config(state=tk.DISABLED)
        self.preview_text.configure(font=("Courier", 10))

        self.mark_positive_button.config(state=tk.NORMAL)
        self.mark_negative_button.config(state=tk.NORMAL)

        # Scroll to the selected line
        self.preview_text.see(f"{int(line_number)}.0")

    def open_file_in_notepad(self):
        selected_item = self.results_treeview.selection()[0]
        file_path = self.results_treeview.item(selected_item, "values")[1]
        line_number = self.results_treeview.item(selected_item, "values")[2]

        if os.path.exists(self.notepad_path):
            command = [self.notepad_path, "-n" + str(line_number), file_path]
            subprocess.Popen(command)
        else:
            messagebox.showinfo("Info", "Notepad++ executable not found.")
            self.browse_notepad_executable()

    def browse_notepad_executable(self):
        file_path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
        if file_path:
            self.notepad_path = file_path

    def mark_as_true_positive(self):
        selected_item = self.results_treeview.selection()[0]
        self.results_treeview.item(selected_item, tags=("True Positive",))
        self.results_treeview.tag_configure("True Positive", background="green")

    def mark_as_false_positive(self):
        selected_item = self.results_treeview.selection()[0]
        self.results_treeview.item(selected_item, tags=("False Positive",))
        self.results_treeview.tag_configure("False Positive", background="red")

    def sort_results(self, column):
        data = [(self.results_treeview.set(child, column), child) for child in self.results_treeview.get_children("")]
        data.sort(key=lambda x: self.convert_to_numeric(x[0]), reverse=False if column == "Line Number" else True)
        for index, (_, child) in enumerate(data):
            self.results_treeview.move(child, "", index)

    def convert_to_numeric(self, value):
        try:
            return int(value)
        except ValueError:
            return value

    def export_results(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["File Path", "Line Number", "Keyword", "Preview"])
                for result in self.results:
                    writer.writerow(result)

            messagebox.showinfo("Export Complete", "Search results exported successfully.")


    def get_keywords(self):
        keywords = []
        if self.wordlist_file:
            with open(self.wordlist_file, "r") as f:
                keywords = [line.strip() for line in f if line.strip()]
        return keywords

    def clear_results(self):
        self.results.clear()
        self.skipped_files.clear()

    def show_about_info(self):
        messagebox.showinfo("About",
                            'Developed By: Srirammanan\nVersion: V2\n\nThis application is for internal purposes only.')

    def run(self):
        self.mainloop()


if __name__ == "__main__":
    app = SourceCodeVulnerabilityDetectionDashboard()
    app.run()