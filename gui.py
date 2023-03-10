from tkinter import *
import tkinter as tk
from tkinter.messagebox import *
from datetime import datetime
import threading
import platform

from winnerodds_export_csv import *

token_fname = "token.txt"
datetime_format = "%Y-%m-%d"

class App(tk.Frame):
    def __init__(self, window):
        super().__init__(window)

        self.success = True
        self.message = ""
        self.wo_exporter = None

        padding = {"padx": 5, "pady": 5}

        ## Load token
        if os.path.exists("token.txt"):
            with open("token.txt") as f:
                token = f.read()
        else:
            token = ""

        ## Create window
        window.title("WinnerOdds Bet History Exporter")
        if platform.system().lower == "darwin": # MAC OS
            window.geometry('300x220')
        else:
            window.geometry('300x200')
        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(1, weight=1)

        Label(window, text="Token").grid(column=0, row=0)
        Label(window, text="Start Date").grid(column=0, row=1)
        Label(window, text="End Date").grid(column=0, row=2)
        Label(window, text="Sport").grid(column=0, row=3)
        Label(window, text="").grid(column=0, row=4)

        self.tokField = Entry(window)
        self.tokField.grid(column=1, row=0, **padding)
        self.tokField.insert(0, token)

        self.startdate = Entry(window)
        self.startdate.grid(column=1, row=1, **padding)
        self.startdate.insert(0, "1970-12-31")

        self.enddate = Entry(window)
        self.enddate.grid(column=1, row=2, **padding)
        self.enddate.insert(0, datetime.now().strftime(datetime_format))

        self.sportVar = StringVar()
        self.sportVar.set("TENNIS")
        sport = OptionMenu(window, self.sportVar, "TENNIS", "FOOTBALL")
        sport.grid(column=1, row=3, **padding)

        btn = Button(window, text="Download CSV", command=self.clicked)
        btn.grid(column=0, row=5, columnspan=2)

        self.progress = Label(window, text="")
        self.progress.grid(column=0, row=6, columnspan=2)
    

    def clicked(self):
        ## Validate dates
        sd = self.startdate.get()
        try:
            datetime.strptime(sd, datetime_format)
        except:
            tk.messagebox.showerror(title="Error", message="Invalid start date. Must be YYYY-MM-DD")
            return
        
        ed = self.enddate.get()
        try:
            datetime.strptime(ed, datetime_format)
        except:
            tk.messagebox.showerror(title="Error", message="Invalid end date. Must be YYYY-MM-DD")
            return
        
        ## Validate token and save to file
        token = self.tokField.get()
        if token.startswith("Bearer "):
            token = token[len("Bearer "):]
        token = token.strip()

        if token == "":
            tk.messagebox.showerror(title="Error", message="Token cannot be empty")

        with open("token.txt", "w") as f:
            f.write(token)

        ## Start downloading CSV
        self.download_thread = threading.Thread(target=self.run)
        self.download_thread.daemon = True
        self.download_thread.start()
        root.after(1, self.check_thread)


    def run(self):
        try:
            self.wo_exporter = WinnerOddsExporter(self.startdate.get(), self.enddate.get(), self.sportVar.get())
            self.wo_exporter.run()
            self.success = True
            self.message = f"Saved to {self.wo_exporter.csv_path}"
        except Exception as e:
            self.success = False
            self.message = str(e)


    def check_thread(self):
        if (self.wo_exporter):
                self.progress.config(text=self.wo_exporter.last_print)
        
        if self.download_thread.is_alive():
            root.after(1, self.check_thread)
        else:
            if (self.success):
                tk.messagebox.showinfo(title="Done", message=self.message)
            else:
                tk.messagebox.showerror(title="Error", message=self.message)


root = tk.Tk()
myapp = App(root)
myapp.mainloop()